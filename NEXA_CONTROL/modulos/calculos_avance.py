"""Avances ponderados por presupuesto y cantidades por partida."""
import numpy as np
import pandas as pd

from .gestion_datos import CLAVE
from .valorizaciones import detalle_valorizaciones, presupuesto_contratado


def porcentaje(numerador, denominador):
    """Un presupuesto cero devuelve cero, sin ocultar la advertencia en UI."""
    return float(numerador / denominador * 100) if denominador > 0 else 0.0


def avance_por_trabajo(partidas, avances, hasta):
    corte = pd.Timestamp(hasta)
    acumulados = avances.loc[avances.fecha <= corte].groupby(CLAVE, as_index=False)[
        ["metrado_programado", "metrado_ejecutado"]].sum()
    d = partidas.merge(acumulados, on=CLAVE, how="left", validate="one_to_one")
    d[["metrado_programado", "metrado_ejecutado"]] = d[["metrado_programado", "metrado_ejecutado"]].fillna(0)
    d["presupuesto"] = d.metrado_contratado * d.precio_unitario
    d["valor_programado"] = d.metrado_programado * d.precio_unitario
    d["valor_ejecutado"] = d.metrado_ejecutado * d.precio_unitario
    denominador = d.metrado_contratado.where(d.metrado_contratado > 0)
    d["avance_programado"] = (100 * d.metrado_programado / denominador).fillna(0)
    d["avance_real"] = (100 * d.metrado_ejecutado / denominador).fillna(0)
    d["desviacion_pp"] = d.avance_real - d.avance_programado
    d["metrado_pendiente"] = (d.metrado_contratado - d.metrado_ejecutado).clip(lower=0)
    d["saldo"] = d.presupuesto - d.valor_ejecutado
    pendiente = d.metrado_pendiente > np.maximum(1, d.metrado_contratado) * 1e-9
    atrasado = pendiente & ((d.desviacion_pp < -1e-7) | (d.fecha_fin < corte))
    d["estado"] = np.select([~pendiente, atrasado, d.metrado_ejecutado > 0],
                             ["Completado", "Atrasado", "En ejecución"], default="Pendiente")
    return d


def avance_por_frente(trabajos):
    """No suma metrados de unidades distintas: pondera los montos."""
    d = trabajos.groupby(["proyecto", "frente"], as_index=False)[
        ["presupuesto", "valor_programado", "valor_ejecutado"]].sum()
    base = d.presupuesto.where(d.presupuesto > 0)
    d["avance_programado"] = (100 * d.valor_programado / base).fillna(0)
    d["avance_real"] = (100 * d.valor_ejecutado / base).fillna(0)
    d["desviacion_pp"] = d.avance_real - d.avance_programado
    return d


def curva_acumulada(partidas, avances, hasta):
    """Serie histórica completa al corte, con origen cero anterior al inicio."""
    corte = pd.Timestamp(hasta)
    d = detalle_valorizaciones(partidas, avances)
    d = d.loc[d.fecha <= corte]
    fechas = [corte]
    if not partidas.empty:
        fechas.append(partidas.fecha_inicio.min() - pd.Timedelta(days=1))
    if not d.empty:
        fechas.append(d.fecha.min() - pd.Timedelta(days=1))
    origen = min(fechas)
    diario = d.groupby("fecha")[["valor_programado", "valor_ejecutado"]].sum()
    indice = diario.index.union(pd.DatetimeIndex([origen, corte]).unique()).sort_values()
    diario = diario.reindex(indice, fill_value=0).cumsum()
    presupuesto = presupuesto_contratado(partidas)
    for monto, avance in [("valor_programado", "avance_programado"), ("valor_ejecutado", "avance_real")]:
        diario[avance] = 100 * diario[monto] / presupuesto if presupuesto > 0 else 0.0
    diario.index.name = "fecha"
    return diario.reset_index()
