import pandas as pd
import pytest

from modulos.gestion_datos import AVANCES, PARTIDAS, validar_datos


@pytest.fixture
def datos():
    p = pd.DataFrame([
        ["P", "001", "Excavación", "Norte", "m³", 100, 10, "2026-01-01", "2026-03-31"],
        ["P", "002", "Canal", "Sur", "m", 50, 40, "2026-01-01", "2026-03-31"],
    ], columns=PARTIDAS)
    a = pd.DataFrame([
        ["P", "2026-01-31", "001", 30, 20], ["P", "2026-01-31", "002", 10, 5],
        ["P", "2026-02-28", "001", 20, 30], ["P", "2026-02-28", "002", 15, 20],
    ], columns=AVANCES)
    return validar_datos(p, a)
