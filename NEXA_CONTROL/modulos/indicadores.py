"""Indicadores consistentes con el alcance y la fecha de corte seleccionados."""
from .calculos_avance import avance_por_trabajo, porcentaje
from .valorizaciones import presupuesto_contratado, valorizacion_periodo


def calcular_indicadores(partidas, avances, desde, hasta):
    trabajos = avance_por_trabajo(partidas, avances, hasta)
    presupuesto = presupuesto_contratado(partidas)
    ejecutado = float(trabajos.valor_ejecutado.sum())
    programado = float(trabajos.valor_programado.sum())
    real = porcentaje(ejecutado, presupuesto)
    plan = porcentaje(programado, presupuesto)
    return {
        "presupuesto_contratado": presupuesto,
        "ejecutado_acumulado": ejecutado,
        "saldo_por_valorizar": presupuesto - ejecutado,
        "avance_programado_pct": plan,
        "avance_real_pct": real,
        "desviacion_pp": real - plan,
        "trabajos_registrados": len(partidas),
        "trabajos_pendientes": int((trabajos.estado != "Completado").sum()),
        "trabajos_atrasados": int((trabajos.estado == "Atrasado").sum()),
        "ejecutado_periodo": valorizacion_periodo(partidas, avances, desde, hasta),
    }
