import pytest

from modulos.valorizaciones import (presupuesto_contratado, saldo_contractual,
    valorizacion_acumulada, valorizacion_periodo, valorizaciones_mensuales)


def test_montos_conocidos(datos):
    p, a = datos
    assert presupuesto_contratado(p) == 3000
    assert valorizacion_periodo(p, a, "2026-02-01", "2026-02-28") == 1100
    assert valorizacion_acumulada(p, a, "2026-02-28") == 1500
    assert saldo_contractual(p, a, "2026-02-28") == 1500
    assert valorizacion_acumulada(p, a, "2025-12-31") == 0


def test_periodo_inclusivo_y_meses_sin_movimientos(datos):
    p, a = datos
    assert valorizacion_periodo(p, a, "2026-01-31", "2026-01-31") == 400
    meses = valorizaciones_mensuales(p, a, "2026-01-01", "2026-03-31")
    assert meses.periodo.tolist() == ["2026-01", "2026-02", "2026-03"]
    assert meses.valor_ejecutado.tolist() == [400, 1100, 0]
