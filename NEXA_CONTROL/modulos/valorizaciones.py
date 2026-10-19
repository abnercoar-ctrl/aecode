"""Montos brutos a precios unitarios; sin reglas contractuales implícitas."""
import pandas as pd

from .gestion_datos import CLAVE


def presupuesto_contratado(partidas):
    return float((partidas.metrado_contratado * partidas.precio_unitario).sum())


def detalle_valorizaciones(partidas, avances):
    """Une por proyecto + código: ninguna cantidad se multiplica dos veces."""
    detalle = avances.merge(partidas[CLAVE + ["descripcion", "frente", "unidad", "precio_unitario"]],
                             on=CLAVE, how="left", validate="many_to_one")
    detalle["valor_programado"] = detalle.metrado_programado * detalle.precio_unitario
    detalle["valor_ejecutado"] = detalle.metrado_ejecutado * detalle.precio_unitario
    return detalle


def valorizacion_periodo(partidas, avances, desde, hasta):
    detalle = detalle_valorizaciones(partidas, avances)
    return float(detalle.loc[detalle.fecha.between(pd.Timestamp(desde), pd.Timestamp(hasta)),
                            "valor_ejecutado"].sum())


def valorizacion_acumulada(partidas, avances, hasta):
    detalle = detalle_valorizaciones(partidas, avances)
    return float(detalle.loc[detalle.fecha <= pd.Timestamp(hasta), "valor_ejecutado"].sum())


def saldo_contractual(partidas, avances, hasta):
    return presupuesto_contratado(partidas) - valorizacion_acumulada(partidas, avances, hasta)


def valorizaciones_mensuales(partidas, avances, desde, hasta):
    """Meses sin registros incluidos; extremos del intervalo son inclusivos."""
    d = detalle_valorizaciones(partidas, avances)
    d = d.loc[d.fecha.between(pd.Timestamp(desde), pd.Timestamp(hasta))].copy()
    d["periodo"] = d.fecha.dt.to_period("M")
    meses = pd.period_range(desde, hasta, freq="M")
    salida = d.groupby("periodo")[["valor_programado", "valor_ejecutado"]].sum().reindex(meses, fill_value=0)
    salida.index.name = "periodo"
    salida = salida.reset_index()
    salida["periodo"] = salida.periodo.astype(str)
    return salida
