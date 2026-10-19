import pytest

from modulos.calculos_avance import avance_por_frente, avance_por_trabajo, curva_acumulada
from modulos.graficos import (grafico_avance_frente, grafico_curva_s,
                              grafico_desviaciones, grafico_valorizaciones)
from modulos.valorizaciones import valorizaciones_mensuales


def test_graficos_reflejan_montos_y_porcentajes_del_corte(datos):
    p, a = datos
    trabajos = avance_por_trabajo(p, a, "2026-01-31")
    desviaciones = grafico_desviaciones(trabajos)
    assert list(desviaciones.data[0].x) == pytest.approx([-10, -10])
    frentes = grafico_avance_frente(avance_por_frente(trabajos))
    assert list(frentes.data[1].x) == pytest.approx([20, 10])
    curva = grafico_curva_s(curva_acumulada(p, a, "2026-02-28"))
    assert curva.data[1].y[-1] == 50
    mensual = grafico_valorizaciones(valorizaciones_mensuales(p, a, "2026-01-01", "2026-03-31"))
    assert list(mensual.data[0].y) == [400, 1100, 0]
    assert list(mensual.data[0].x) == ["2026-01", "2026-02", "2026-03"]
    assert mensual.layout.xaxis.type == "category"
