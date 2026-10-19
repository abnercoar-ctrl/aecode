"""Genera archivos demostrativos deterministas; no contiene datos empresariales."""
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from modulos.gestion_datos import AVANCES, PARTIDAS, validar_datos
from modulos.exportacion import libro_excel


def generar():
    filas = [
        ["Proyecto DEMO A", "TR-001", "Excavación de plataforma", "Movimiento de tierras", "m³", 1000, 20, "2026-01-01", "2026-04-30"],
        ["Proyecto DEMO A", "TR-002", "Relleno compactado", "Movimiento de tierras", "m³", 500, 40, "2026-01-01", "2026-05-31"],
        ["Proyecto DEMO A", "TR-003", "Canal de concreto", "Drenaje", "m", 200, 150, "2026-01-01", "2026-06-30"],
        ["Proyecto DEMO A", "TR-004", "Conformación de accesos", "Accesos", "m²", 1000, 10, "2026-01-01", "2026-06-30"],
        ["Proyecto DEMO A", "TR-005", "Señalización de acceso", "Accesos", "und", 20, 500, "2026-04-01", "2026-06-30"],
        ["Proyecto DEMO A", "TR-006", "Limpieza final", "Accesos", "m²", 2000, 5, "2026-05-01", "2026-06-30"],
        ["Proyecto DEMO B", "TR-001", "Excavación de cuneta", "Drenaje", "m³", 400, 25, "2026-01-01", "2026-06-30"],
        ["Proyecto DEMO B", "TR-002", "Revestimiento de cuneta", "Drenaje", "m", 100, 200, "2026-01-01", "2026-06-30"],
    ]
    registros = []
    # Fracciones incrementales; acumulados plan/real permiten atrasos y adelantos.
    perfiles = [([.2, .3, .3], [.15, .25, .25]), ([.1, .2, .3], [.1, .15, .2]),
                ([.1, .2, .2], [.15, .2, .25]), ([.2, .2, .2], [.2, .2, .2]),
                ([0, 0, 0], [0, 0, 0]), ([0, 0, 0], [0, 0, 0]),
                ([.2, .3, .2], [.2, .2, .2]), ([.1, .2, .2], [.1, .1, .2])]
    for fila, (plan, real) in zip(filas, perfiles):
        for fecha, fp, fr in zip(["2026-01-31", "2026-02-28", "2026-03-31"], plan, real):
            if fp or fr:
                registros.append([fila[0], fecha, fila[1], fila[5] * fp, fila[5] * fr])
    p, a = validar_datos(pd.DataFrame(filas, columns=PARTIDAS), pd.DataFrame(registros, columns=AVANCES))
    carpeta = BASE / "datos"
    carpeta.mkdir(exist_ok=True)
    for nombre, tabla in [("partidas", p), ("avances", a)]:
        (carpeta / f"{nombre}_ejemplo.xlsx").write_bytes(libro_excel({nombre: tabla}))
        tabla.to_csv(carpeta / f"{nombre}_ejemplo.csv", index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")
    print(f"Generados {len(p)} trabajos y {len(a)} registros ficticios en {carpeta}")


if __name__ == "__main__":
    generar()
