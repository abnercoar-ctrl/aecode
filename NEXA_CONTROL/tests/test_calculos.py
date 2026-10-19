import pandas as pd
import pytest

from modulos.calculos_avance import avance_por_frente, avance_por_trabajo, curva_acumulada, porcentaje
from modulos.gestion_datos import filtrar, tabla_vacia, validar_datos
from modulos.indicadores import calcular_indicadores


def test_ponderacion_no_es_promedio_simple(datos):
    p, a = datos
    ind = calcular_indicadores(p, a, "2026-01-01", "2026-01-31")
    # Cantidades: 20% y 10%; promedio simple=15%, ponderado=400/3000.
    assert ind["avance_real_pct"] == pytest.approx(400 / 3000 * 100)
    assert ind["avance_programado_pct"] == pytest.approx(700 / 3000 * 100)
    assert ind["desviacion_pp"] == pytest.approx(-10)
    assert ind["trabajos_atrasados"] == 2


def test_corte_y_periodo_no_pierden_historia(datos):
    p, a = datos
    ind = calcular_indicadores(p, a, "2026-02-01", "2026-02-28")
    assert ind["ejecutado_periodo"] == 1100
    assert ind["ejecutado_acumulado"] == 1500
    assert ind["avance_real_pct"] == 50
    serie = curva_acumulada(p, a, "2026-02-28")
    assert serie.avance_real.iloc[0] == 0
    assert serie.avance_real.iloc[-1] == 50
    assert serie.fecha.max() == pd.Timestamp("2026-02-28")


def test_filtros_y_frentes(datos):
    p, a = filtrar(*datos, proyecto="P", frente="Sur")
    assert len(p) == 1 and len(a) == 2
    trabajos = avance_por_trabajo(p, a, "2026-02-28")
    frentes = avance_por_frente(trabajos)
    assert frentes.avance_real.iloc[0] == 50
    assert trabajos.metrado_pendiente.iloc[0] == 25


def test_fecha_vencida_con_programacion_incompleta(datos):
    trabajos = avance_por_trabajo(*datos, "2026-04-01")
    assert trabajos.estado.tolist() == ["Atrasado", "Atrasado"]


def test_presupuesto_cero_y_vacios(datos):
    assert porcentaje(10, 0) == 0
    p, a = validar_datos(tabla_vacia("partidas"), tabla_vacia("avances"))
    ind = calcular_indicadores(p, a, "2026-01-01", "2026-02-28")
    assert ind["avance_real_pct"] == 0
    assert ind["trabajos_registrados"] == 0
    assert len(curva_acumulada(p, a, "2026-02-28")) == 1
    p, a = datos
    p.precio_unitario = 0
    assert calcular_indicadores(p, a, "2026-01-01", "2026-02-28")["avance_real_pct"] == 0
