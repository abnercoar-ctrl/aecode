"""Punto de entrada de NEXA CONTROL. Ejecutar con python -m streamlit run app.py."""
from pathlib import Path

import pandas as pd
import streamlit as st

from modulos.gestion_datos import cargar_ejemplos, filtrar, tabla_vacia, validar_datos
from modulos.interfaz import (SECCIONES, dashboard, guardar, registro_trabajos,
                              reportes, seguimiento, valorizaciones)

BASE = Path(__file__).resolve().parent
st.set_page_config(page_title="NEXA CONTROL", page_icon="📊", layout="wide")
st.markdown("""<style>
  .stApp {background:#fff;color:#162d46;}
  [data-testid="stSidebar"] {background:#f4f6f8;}
  .block-container {padding-top:2rem;padding-bottom:2rem;max-width:1700px;}
  h1,h2,h3 {color:#162d46;}
  h1 {letter-spacing:-.04em;}
  [data-testid="stMetricValue"] {font-size:clamp(1.15rem,1.7vw,1.9rem);font-weight:650;}
  [data-testid="stMetricLabel"] {font-size:.85rem;}
  [data-testid="stMetric"] {padding:.6rem 0;border-bottom:1px solid #edf1f5;}
  @media(max-width:700px) {.block-container{padding-top:1rem;} h1{font-size:2rem;}}
</style>""", unsafe_allow_html=True)

if "partidas" not in st.session_state:
    st.session_state.partidas, st.session_state.avances = cargar_ejemplos(BASE / "datos")
    st.session_state.origen = "Sesión iniciada con datos ficticios de demostración"
    st.session_state.revision = 0

with st.sidebar:
    st.title("NEXA CONTROL")
    seccion = st.radio("Navegación", SECCIONES, key="seccion", label_visibility="collapsed")
    st.divider()
    moneda = st.text_input("Unidad monetaria (etiqueta)", value="UM", max_chars=8).strip() or "UM"
    st.caption("UM = unidades monetarias ficticias. Cambiar la etiqueta no convierte los precios.")
    st.caption("Los datos se conservan durante la sesión. Descargue un respaldo antes de cerrar; "
               "un reinicio del servidor puede borrar los cambios.")
    with st.expander("Datos de la sesión"):
        st.write(st.session_state.origen)
        if st.button("Iniciar sesión vacía"):
            st.session_state.origen = "Sesión manual / archivos del usuario (no verificados como datos reales)"
            guardar(tabla_vacia("partidas"), tabla_vacia("avances"), "Sesión vacía preparada.")
        if st.button("Recargar demostración"):
            p, a = cargar_ejemplos(BASE / "datos")
            st.session_state.origen = "Sesión iniciada con datos ficticios de demostración"
            guardar(p, a, "Datos de demostración recargados.")

st.title("NEXA CONTROL")
st.markdown("### Sistema de Seguimiento de Trabajos y Valorizaciones")
st.caption(st.session_state.origen + " · Precios ilustrativos, sin información contractual real.")
if "confirmacion" in st.session_state:
    st.success(st.session_state.pop("confirmacion"))

p, a = validar_datos(st.session_state.partidas, st.session_state.avances)
c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
proyectos = ["Todos los proyectos"] + sorted(p.proyecto.unique().tolist())
proyecto = c1.selectbox("Proyecto", proyectos)
pv = p if proyecto == "Todos los proyectos" else p.loc[p.proyecto.eq(proyecto)]
frente = c2.selectbox("Frente de trabajo", ["Todos los frentes"] + sorted(pv.frente.unique().tolist()))
if not a.empty:
    inicio_defecto, fin_defecto = a.fecha.min().date(), a.fecha.max().date()
elif not p.empty:
    inicio_defecto, fin_defecto = p.fecha_inicio.min().date(), p.fecha_fin.max().date()
else:
    inicio_defecto, fin_defecto = pd.Timestamp("2026-01-01").date(), pd.Timestamp("2026-06-30").date()
desde = c3.date_input("Desde", value=inicio_defecto, format="YYYY-MM-DD", key=f"desde_{st.session_state.revision}")
hasta = c4.date_input("Hasta", value=fin_defecto, format="YYYY-MM-DD", key=f"hasta_{st.session_state.revision}")
if desde > hasta:
    st.error("Desde debe ser igual o anterior a Hasta.")
    st.stop()
pf, af = filtrar(p, a, None if proyecto == "Todos los proyectos" else proyecto,
                 None if frente == "Todos los frentes" else frente)
st.caption("Acumulados al corte Hasta; Desde limita las valorizaciones del período. "
           "El presupuesto incluye todas las partidas del alcance filtrado.")
if pf.empty:
    st.info("No hay trabajos en este alcance. Registre trabajos o importe las plantillas.")
if not af.empty:
    fechas = af.merge(pf[["proyecto", "codigo", "fecha_inicio", "fecha_fin"]], on=["proyecto", "codigo"])
    if ((fechas.fecha < fechas.fecha_inicio) | (fechas.fecha > fechas.fecha_fin)).any():
        st.warning("Hay registros fuera de las fechas programadas. Se incluyen en los cálculos; revise sus fechas.")
if (pf.precio_unitario.eq(0) | pf.metrado_contratado.eq(0)).any():
    st.warning("Hay partidas con precio o metrado contratado cero; revise su efecto en la ponderación.")

if seccion == "Dashboard general":
    dashboard(pf, af, desde, hasta, moneda)
elif seccion == "Registro de trabajos":
    registro_trabajos()
elif seccion == "Seguimiento de avances":
    seguimiento(pf, af, hasta)
elif seccion == "Valorizaciones":
    valorizaciones(pf, af, desde, hasta, moneda)
else:
    reportes(pf, af, desde, hasta, moneda, f"{proyecto} / {frente}", BASE / "datos")
