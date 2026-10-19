"""Esquemas, validación transaccional e importación de datos de la sesión."""
from io import BytesIO
from pathlib import Path
import re

import numpy as np
import pandas as pd

CLAVE = ["proyecto", "codigo"]
PARTIDAS = ["proyecto", "codigo", "descripcion", "frente", "unidad",
            "metrado_contratado", "precio_unitario", "fecha_inicio", "fecha_fin"]
AVANCES = ["proyecto", "fecha", "codigo", "metrado_programado", "metrado_ejecutado"]
FECHAS = ["fecha", "fecha_inicio", "fecha_fin"]


class ErrorDatos(ValueError):
    """Datos rechazados: la sesión no debe alterarse."""


def tabla_vacia(tipo):
    return pd.DataFrame(columns=PARTIDAS if tipo == "partidas" else AVANCES)


def _normalizar(df, columnas, numericas, fechas):
    if df.columns.duplicated().any():
        raise ErrorDatos("El archivo contiene encabezados duplicados.")
    faltantes = sorted(set(columnas) - set(df.columns))
    extras = sorted(set(df.columns) - set(columnas))
    if faltantes or extras:
        raise ErrorDatos(f"Columnas faltantes: {', '.join(faltantes) or 'ninguna'}. "
                         f"Columnas no esperadas: {', '.join(extras) or 'ninguna'}.")
    resultado = df[columnas].copy().reset_index(drop=True)
    if resultado.empty:
        for col in numericas:
            resultado[col] = pd.Series(dtype=float)
        for col in fechas:
            resultado[col] = pd.Series(dtype="datetime64[ns]")
        return resultado
    for col in columnas:
        if col in numericas:
            valores = pd.to_numeric(resultado[col], errors="coerce")
            invalido = valores.isna() | ~np.isfinite(valores) | (valores < 0)
            if invalido.any():
                raise ErrorDatos(f"{col}: use números finitos no negativos. "
                                 f"Filas de datos: {(resultado.index[invalido] + 1).tolist()}.")
            resultado[col] = valores.astype(float)
        elif col in fechas:
            # ISO o fechas Excel; no se interpretan números como nanosegundos.
            def parsear(valor):
                if isinstance(valor, (int, float, np.number)):
                    return pd.NaT
                if isinstance(valor, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor.strip()):
                    return pd.NaT
                try:
                    fecha = pd.Timestamp(valor)
                    if fecha.tzinfo is not None or pd.isna(fecha):
                        return pd.NaT
                    return fecha.normalize()
                except (ValueError, TypeError, OverflowError):
                    return pd.NaT
            valores = resultado[col].map(parsear)
            if valores.isna().any():
                raise ErrorDatos(f"{col}: complete fechas válidas en formato AAAA-MM-DD.")
            resultado[col] = pd.to_datetime(valores)
        else:
            if resultado[col].isna().any():
                raise ErrorDatos(f"{col}: campo obligatorio sin completar.")
            resultado[col] = resultado[col].astype(str).str.strip()
            if resultado[col].eq("").any():
                raise ErrorDatos(f"{col}: campo obligatorio sin completar.")
    return resultado


def validar_datos(partidas, avances):
    """Devuelve copias normalizadas o rechaza ambas tablas de forma atómica.

    Un registro representa cantidades incrementales de un día. Se admite el
    mismo código en proyectos distintos, nunca dos registros del mismo trabajo
    en la misma fecha. No se permiten sobre-ejecuciones ni sobre-programación.
    """
    p = _normalizar(partidas, PARTIDAS, ["metrado_contratado", "precio_unitario"],
                    ["fecha_inicio", "fecha_fin"])
    a = _normalizar(avances, AVANCES, ["metrado_programado", "metrado_ejecutado"], ["fecha"])
    if p.duplicated(CLAVE).any():
        raise ErrorDatos("Partidas duplicadas: proyecto + codigo deben ser únicos.")
    if (p.fecha_fin < p.fecha_inicio).any():
        raise ErrorDatos("La fecha de fin debe ser igual o posterior a la fecha de inicio.")
    if a.duplicated(CLAVE + ["fecha"]).any():
        raise ErrorDatos("Avance duplicado: solo un registro por proyecto, código y fecha. Edite el existente.")
    if not a.empty:
        unidos = a.merge(p[CLAVE + ["metrado_contratado"]], on=CLAVE, how="left", validate="many_to_one")
        if unidos.metrado_contratado.isna().any():
            raise ErrorDatos("Hay avances con proyecto o código de trabajo inexistente.")
        acumulado = unidos.groupby(CLAVE, as_index=False).agg(
            metrado_programado=("metrado_programado", "sum"),
            metrado_ejecutado=("metrado_ejecutado", "sum"),
            metrado_contratado=("metrado_contratado", "first"))
        for campo in ["metrado_ejecutado", "metrado_programado"]:
            tolerancia = np.maximum(1, acumulado.metrado_contratado) * 1e-9
            exceso = acumulado[campo] > acumulado.metrado_contratado + tolerancia
            if exceso.any():
                trabajos = acumulado.loc[exceso, CLAVE].astype(str).agg(" / ".join, axis=1)
                raise ErrorDatos(f"{campo} acumulado supera el metrado contratado: {', '.join(trabajos)}.")
    return p, a


def leer_archivo(contenido, nombre, tipo):
    """Lee una tabla sin incorporarla: el usuario debe revisar y confirmar."""
    datos = contenido if isinstance(contenido, bytes) else contenido.getvalue()
    if len(datos) > 20 * 1024 * 1024:
        raise ErrorDatos("El archivo excede el límite de 20 MB.")
    try:
        extension = Path(nombre).suffix.lower()
        if extension == ".xlsx":
            df = pd.read_excel(BytesIO(datos), dtype={"codigo": str, "proyecto": str}, engine="openpyxl")
        elif extension == ".csv":
            df = pd.read_csv(BytesIO(datos), sep=None, engine="python", encoding="utf-8-sig",
                             dtype={"codigo": str, "proyecto": str})
        else:
            raise ErrorDatos("Formato no admitido. Use Excel .xlsx o CSV UTF-8.")
    except ErrorDatos:
        raise
    except Exception as exc:
        raise ErrorDatos("No se pudo leer el archivo. Revise el formato y los encabezados.") from exc
    columnas = PARTIDAS if tipo == "partidas" else AVANCES
    return _normalizar(df, columnas,
                       ["metrado_contratado", "precio_unitario"] if tipo == "partidas"
                       else ["metrado_programado", "metrado_ejecutado"],
                       ["fecha_inicio", "fecha_fin"] if tipo == "partidas" else ["fecha"])


def incorporar(partidas, avances, nueva_tabla, tipo, reemplazar=False):
    """Prepara y valida el candidato completo sin mutar el estado anterior."""
    anterior = partidas if tipo == "partidas" else avances
    candidata = nueva_tabla.copy() if reemplazar else pd.concat([anterior, nueva_tabla], ignore_index=True)
    return validar_datos(candidata if tipo == "partidas" else partidas,
                         candidata if tipo == "avances" else avances)


def cargar_ejemplos(carpeta):
    carpeta = Path(carpeta)
    p = pd.read_excel(carpeta / "partidas_ejemplo.xlsx", dtype={"codigo": str})
    a = pd.read_excel(carpeta / "avances_ejemplo.xlsx", dtype={"codigo": str})
    return validar_datos(p, a)


def filtrar(partidas, avances, proyecto=None, frente=None):
    """Filtra ambas tablas conservando la relación compuesta."""
    p = partidas.copy()
    if proyecto is not None:
        p = p.loc[p.proyecto.eq(proyecto)]
    if frente is not None:
        p = p.loc[p.frente.eq(frente)]
    a = avances.merge(p[CLAVE], on=CLAVE, how="inner", validate="many_to_one")
    return p.reset_index(drop=True), a[AVANCES].reset_index(drop=True)
