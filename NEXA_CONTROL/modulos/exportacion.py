"""Exportación reproducible con metadatos del alcance y protección de texto."""
from io import BytesIO

import pandas as pd

from .calculos_avance import avance_por_trabajo
from .indicadores import calcular_indicadores
from .valorizaciones import detalle_valorizaciones, valorizaciones_mensuales


def libro_excel(hojas, moneda=None):
    salida = BytesIO()
    # Los textos de usuario que empiezan con '=' se exportan como texto literal.
    with pd.ExcelWriter(salida, engine="xlsxwriter", datetime_format="yyyy-mm-dd",
                        date_format="yyyy-mm-dd", engine_kwargs={"options": {
                            "strings_to_formulas": False, "strings_to_urls": False}}) as writer:
        libro = writer.book
        encabezado = libro.add_format({"bold": True, "bg_color": "#162D46", "font_color": "white",
                                       "text_wrap": True, "valign": "vcenter"})
        numero = libro.add_format({"num_format": "#,##0.00"})
        etiqueta = str(moneda or "").replace('"', '').replace('\\', '')
        monetario = libro.add_format({"num_format": f'"{etiqueta}" #,##0.00'}) if etiqueta else numero
        columnas_monto = {"precio_unitario", "presupuesto", "valor_programado", "valor_ejecutado", "saldo"}
        fecha = libro.add_format({"num_format": "yyyy-mm-dd"})
        for nombre, tabla in hojas.items():
            tabla.to_excel(writer, sheet_name=nombre, index=False)
            hoja = writer.sheets[nombre]
            hoja.freeze_panes(1, 0)
            hoja.set_row(0, 32)
            for indice, col in enumerate(tabla.columns):
                largo = max([len(str(col))] + [len(str(x)) for x in tabla[col].head(1000)])
                formato = fecha if pd.api.types.is_datetime64_any_dtype(tabla[col]) else (
                    monetario if col in columnas_monto else
                    numero if pd.api.types.is_numeric_dtype(tabla[col]) else None)
                hoja.set_column(indice, indice, min(48, max(15, largo + 2)), formato)
                hoja.write(0, indice, col, encabezado)
            if len(tabla.columns):
                hoja.autofilter(0, 0, len(tabla), len(tabla.columns) - 1)
    return salida.getvalue()


def exportar_reporte(partidas, avances, desde, hasta, moneda="UM", origen="Sesión", alcance="Todos"):
    """El registro exportado incluye historia hasta el corte para reproducir acumulados."""
    a = avances.loc[avances.fecha <= pd.Timestamp(hasta)].copy()
    indicadores = calcular_indicadores(partidas, a, desde, hasta)
    resumen = pd.DataFrame([
        ("Sistema", "NEXA CONTROL"), ("Origen", origen), ("Alcance", alcance),
        ("Desde (período)", str(desde)), ("Hasta (corte inclusivo)", str(hasta)),
        ("Unidad monetaria", moneda),
        ("Cálculo", "Montos brutos: sin IGV, adelantos, amortizaciones, retenciones ni penalidades"),
        ("Historial", "Registro de avances y valorizaciones incluyen historia hasta el corte"),
        ("Avance", "Ponderado por presupuesto; no es promedio simple"),
        ("Atrasado", "Pendiente y menor al programado o con fecha fin vencida"),
    ], columns=["concepto", "valor"])
    tabla_ind = pd.DataFrame(indicadores.items(), columns=["indicador", "valor"])
    tabla_ind["unidad"] = ["%" if x.endswith("_pct") else "pp" if x == "desviacion_pp"
                            else "trabajos" if x.startswith("trabajos_") else moneda
                            for x in tabla_ind.indicador]
    return libro_excel({
        "Resumen general": resumen, "Partidas contratadas": partidas,
        "Registro de avances": a, "Valorizaciones": detalle_valorizaciones(partidas, a),
        "Indicadores": tabla_ind, "Resumen mensual": valorizaciones_mensuales(partidas, a, desde, hasta),
        "Avance por trabajo": avance_por_trabajo(partidas, a, hasta),
    }, moneda=moneda)
