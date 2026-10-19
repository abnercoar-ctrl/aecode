"""Formularios y vistas Streamlit; los cálculos se delegan a módulos puros."""
from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st

from .gestion_datos import AVANCES, PARTIDAS, ErrorDatos, incorporar, leer_archivo, validar_datos
from .calculos_avance import avance_por_frente, avance_por_trabajo, curva_acumulada
from .exportacion import exportar_reporte
from .graficos import (grafico_avance_frente, grafico_curva_s,
                       grafico_desviaciones, grafico_valorizaciones)
from .indicadores import calcular_indicadores
from .valorizaciones import detalle_valorizaciones, valorizaciones_mensuales

SECCIONES = ["Dashboard general", "Registro de trabajos", "Seguimiento de avances",
             "Valorizaciones", "Reportes y exportación"]


def guardar(partidas, avances, mensaje):
    p, a = validar_datos(partidas, avances)
    st.session_state.partidas, st.session_state.avances = p, a
    st.session_state.revision += 1
    st.session_state.confirmacion = mensaje
    st.rerun()


def _error(exc):
    st.error(str(exc))


def tabla_editor(tipo):
    nombre = "partidas" if tipo == "partidas" else "avances"
    with st.expander("Editar o eliminar registros existentes"):
        st.caption("Edite las tablas completas de la sesión. Los cambios se aplican al pulsar Guardar edición.")
        editada = st.data_editor(st.session_state[nombre], num_rows="dynamic", hide_index=True,
                                width="stretch", key=f"editor_{tipo}_{st.session_state.revision}")
        if st.button("Guardar edición", key=f"guardar_{tipo}"):
            try:
                p, a = incorporar(st.session_state.partidas, st.session_state.avances,
                                   editada, tipo, reemplazar=True)
                guardar(p, a, "Edición guardada correctamente.")
            except ErrorDatos as exc:
                _error(exc)


def importar(tipo):
    with st.expander(f"Importar {tipo} desde Excel o CSV"):
        st.caption("Use las columnas de las plantillas. CSV UTF-8, separador coma o punto y coma, "
                   "decimal con punto y fechas AAAA-MM-DD. Códigos como texto para conservar ceros iniciales.")
        archivo = st.file_uploader(f"Archivo de {tipo}", type=["xlsx", "csv"], key=f"archivo_{tipo}",
                                   max_upload_size=20)
        modo = st.radio("Cómo incorporar", ["Agregar registros", "Reemplazar esta tabla"],
                        key=f"modo_{tipo}", horizontal=True)
        st.caption("El reemplazo se rechaza si deja avances sin una partida. Para reemplazar ambos conjuntos, "
                   "inicie una sesión vacía e importe primero las partidas.")
        if archivo is not None:
            try:
                candidata = leer_archivo(archivo, archivo.name, tipo)
                st.dataframe(candidata, hide_index=True, width="stretch")
                st.caption(f"Vista previa: {len(candidata)} registros. La sesión todavía no ha cambiado.")
                p, a = incorporar(st.session_state.partidas, st.session_state.avances,
                                   candidata, tipo, reemplazar=modo.startswith("Reemplazar"))
                if st.button("Incorporar archivo revisado", key=f"incorporar_{tipo}", type="primary"):
                    guardar(p, a, f"Archivo incorporado: {len(candidata)} registros de {tipo}.")
            except ErrorDatos as exc:
                _error(exc)


def registro_trabajos():
    st.subheader("Registro de trabajos")
    st.caption("Gestión de todas las partidas de la sesión. Los filtros del dashboard no limitan esta tabla.")
    with st.form("nueva_partida", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        proyecto = c1.text_input("Proyecto", placeholder="Proyecto demostrativo")
        codigo = c2.text_input("Código de trabajo", placeholder="TR-001")
        frente = c3.text_input("Frente de trabajo", placeholder="Frente norte")
        descripcion = st.text_input("Descripción del trabajo")
        c1, c2, c3 = st.columns(3)
        unidad = c1.selectbox("Unidad de medida", ["m³", "m²", "m", "kg", "t", "und", "glb", "hh"])
        metrado = c2.number_input("Metrado contratado", min_value=0.0, value=100.0, step=1.0, format="%.3f")
        precio = c3.number_input("Precio unitario", min_value=0.0, value=10.0, step=1.0, format="%.4f")
        c1, c2 = st.columns(2)
        inicio = c1.date_input("Fecha de inicio programada", value=date(2026, 1, 1), format="YYYY-MM-DD")
        fin = c2.date_input("Fecha de fin programada", value=date(2026, 6, 30), format="YYYY-MM-DD")
        enviado = st.form_submit_button("Registrar trabajo", type="primary")
    if enviado:
        fila = pd.DataFrame([[proyecto, codigo, descripcion, frente, unidad, metrado, precio, inicio, fin]],
                            columns=PARTIDAS)
        try:
            p, a = incorporar(st.session_state.partidas, st.session_state.avances, fila, "partidas")
            guardar(p, a, "Trabajo registrado correctamente.")
        except ErrorDatos as exc:
            _error(exc)
    st.dataframe(st.session_state.partidas, hide_index=True, width="stretch")
    tabla_editor("partidas")
    importar("partidas")


def seguimiento(partidas, avances, hasta):
    st.subheader("Seguimiento de avances")
    st.caption("Registre cantidades incrementales de cada fecha; no ingrese acumulados. "
               "La fecha es el cierre del período registrado. Un registro por trabajo y fecha.")
    p = st.session_state.partidas
    if p.empty:
        st.info("Registre o importe partidas antes de ingresar avances.")
    else:
        with st.form("nuevo_avance"):
            claves = list(p[["proyecto", "codigo"]].itertuples(index=False, name=None))
            clave = st.selectbox("Trabajo (proyecto / código)", claves, format_func=lambda x: " / ".join(x))
            c1, c2, c3 = st.columns(3)
            fecha = c1.date_input("Fecha de registro", value=hasta, format="YYYY-MM-DD")
            programado = c2.number_input("Metrado programado del período", min_value=0.0, step=1.0, format="%.3f")
            ejecutado = c3.number_input("Metrado ejecutado del período", min_value=0.0, step=1.0, format="%.3f")
            st.caption("Si ya existe esa fecha, edite su registro. Los avances fuera de las fechas "
                       "contractuales se admiten y se señalan como advertencia.")
            enviado = st.form_submit_button("Registrar avance", type="primary")
        if enviado:
            fila = pd.DataFrame([[clave[0], fecha, clave[1], programado, ejecutado]], columns=AVANCES)
            try:
                nuevas_p, nuevas_a = incorporar(p, st.session_state.avances, fila, "avances")
                guardar(nuevas_p, nuevas_a, "Avance registrado correctamente.")
            except ErrorDatos as exc:
                _error(exc)
    st.markdown("**Avance por trabajo al corte · alcance filtrado**")
    st.dataframe(avance_por_trabajo(partidas, avances, hasta), hide_index=True, width="stretch")
    with st.expander("Registro completo de avances", expanded=True):
        st.dataframe(st.session_state.avances, hide_index=True, width="stretch")
    tabla_editor("avances")
    importar("avances")


def dashboard(partidas, avances, desde, hasta, moneda):
    ind = calcular_indicadores(partidas, avances, desde, hasta)
    monto = lambda x: f"{moneda} {x:,.2f}"
    c = st.columns(4)
    c[0].metric("Presupuesto contratado", monto(ind["presupuesto_contratado"]))
    c[1].metric("Ejecutado acumulado", monto(ind["ejecutado_acumulado"]))
    c[2].metric("Saldo por valorizar", monto(ind["saldo_por_valorizar"]))
    c[3].metric("Avance real", f"{ind['avance_real_pct']:.2f}%")
    c = st.columns(4)
    c[0].metric("Avance programado", f"{ind['avance_programado_pct']:.2f}%")
    c[1].metric("Desviación", f"{ind['desviacion_pp']:+.2f} pp")
    c[2].metric("Trabajos registrados", ind["trabajos_registrados"])
    c[3].metric("Trabajos atrasados", ind["trabajos_atrasados"])
    st.caption(f"Avance físico ponderado por presupuesto · Corte inclusivo: {hasta:%Y-%m-%d} · "
               f"Trabajos pendientes: {ind['trabajos_pendientes']} · "
               f"Ejecutado en el período: {monto(ind['ejecutado_periodo'])}")
    if ind["presupuesto_contratado"] == 0:
        st.warning("Presupuesto cero: el avance ponderado se muestra como 0%; no es un avance medible.")
    trabajos = avance_por_trabajo(partidas, avances, hasta)
    c1, c2 = st.columns(2)
    c1.plotly_chart(grafico_curva_s(curva_acumulada(partidas, avances, hasta)), width="stretch")
    c2.plotly_chart(grafico_avance_frente(avance_por_frente(trabajos)), width="stretch")
    c1, c2 = st.columns(2)
    c1.plotly_chart(grafico_valorizaciones(valorizaciones_mensuales(partidas, avances, desde, hasta), moneda), width="stretch")
    c2.plotly_chart(grafico_desviaciones(trabajos), width="stretch")
    st.markdown("**Detalle de trabajos al corte**")
    st.dataframe(trabajos[["proyecto", "codigo", "descripcion", "frente", "unidad", "avance_programado",
                           "avance_real", "desviacion_pp", "metrado_pendiente", "estado"]],
                 hide_index=True, width="stretch")
    with st.expander("Cómo interpretar los resultados"):
        st.write("Los porcentajes generales y por frente se ponderan por presupuesto; no son promedios "
                 "simples. La desviación se expresa en puntos porcentuales (pp). Una partida está atrasada "
                 "si queda metrado y su ejecución es menor a la programada, o venció su fecha fin. "
                 "Las fechas no generan programación automática: cargue los metrados programados.")
        st.write("El presupuesto conserva todo el alcance contratado filtrado. Los acumulados y la curva S "
                 "usan toda la historia hasta Hasta. Desde limita únicamente los montos del período y "
                 "las barras mensuales. Los meses extremos pueden ser parciales.")


def valorizaciones(partidas, avances, desde, hasta, moneda):
    st.subheader("Valorizaciones")
    ind = calcular_indicadores(partidas, avances, desde, hasta)
    c1, c2, c3 = st.columns(3)
    c1.metric("Ejecutado en el período", f"{moneda} {ind['ejecutado_periodo']:,.2f}")
    c2.metric("Acumulado al corte", f"{moneda} {ind['ejecutado_acumulado']:,.2f}")
    c3.metric("Saldo contractual", f"{moneda} {ind['saldo_por_valorizar']:,.2f}")
    mensual = valorizaciones_mensuales(partidas, avances, desde, hasta)
    st.plotly_chart(grafico_valorizaciones(mensual, moneda), width="stretch")
    st.dataframe(mensual, hide_index=True, width="stretch")
    detalle = detalle_valorizaciones(partidas, avances)
    st.markdown("**Registros del período seleccionado**")
    st.dataframe(detalle.loc[detalle.fecha.between(pd.Timestamp(desde), pd.Timestamp(hasta))],
                 hide_index=True, width="stretch")
    st.info("Metrado ejecutado × precio unitario. Montos brutos, sin IGV, adelantos, amortizaciones, "
            "retenciones ni penalidades. La unidad monetaria es una etiqueta, no convierte valores.")


def reportes(partidas, avances, desde, hasta, moneda, alcance, carpeta):
    st.subheader("Reportes y exportación")
    st.write(f"Alcance: {alcance}. Período: {desde:%Y-%m-%d} a {hasta:%Y-%m-%d}.")
    st.caption("El Excel incluye las partidas filtradas y el historial hasta el corte para reproducir "
               "los acumulados. Resumen mensual incluye solo el período seleccionado.")
    contenido = exportar_reporte(partidas, avances, desde, hasta, moneda, st.session_state.origen, alcance)
    st.download_button("Descargar reporte Excel", contenido, file_name=f"NEXA_CONTROL_{hasta:%Y%m%d}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    st.markdown("**Respaldo completo de la sesión**")
    st.caption("Este respaldo conserva también los registros fuera de los filtros o posteriores al corte. "
               "Para restaurarlo: sesión vacía → importar partidas → importar avances.")
    from .exportacion import libro_excel
    respaldo = libro_excel({"Partidas": st.session_state.partidas, "Avances": st.session_state.avances})
    st.download_button("Descargar respaldo completo", respaldo, file_name="NEXA_respaldo.xlsx")
    # Cada tabla se descarga por separado para que pueda importarse directamente.
    for tipo in ["partidas", "avances"]:
        tabla = st.session_state[tipo]
        st.download_button(f"Descargar {tipo} de la sesión (CSV)",
                           tabla.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8-sig"),
                           file_name=f"{tipo}_sesion.csv", mime="text/csv")
    st.markdown("**Plantillas con datos ficticios**")
    for tipo in ["partidas", "avances"]:
        ruta = carpeta / f"{tipo}_ejemplo.xlsx"
        st.download_button(f"Descargar ejemplo de {tipo}", ruta.read_bytes(), file_name=ruta.name)
    with st.expander("Importar el respaldo completo"):
        archivo = st.file_uploader("Respaldo NEXA (hojas Partidas y Avances)", type=["xlsx"], key="respaldo")
        if archivo:
            try:
                hojas = pd.read_excel(BytesIO(archivo.getvalue()), sheet_name=["Partidas", "Avances"],
                                      dtype={"codigo": str}, engine="openpyxl")
                p, a = validar_datos(hojas["Partidas"], hojas["Avances"])
                st.dataframe(p, hide_index=True, width="stretch")
                st.dataframe(a, hide_index=True, width="stretch")
                if st.button("Restaurar respaldo revisado"):
                    guardar(p, a, "Respaldo restaurado correctamente.")
            except Exception as exc:
                if isinstance(exc, ErrorDatos):
                    _error(exc)
                else:
                    st.error("Respaldo inválido. Se requieren las hojas Partidas y Avances con sus columnas originales.")
