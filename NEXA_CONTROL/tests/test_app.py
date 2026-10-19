from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_navegacion_dashboard_y_filtros():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 4
    assert app.metric[0].value == "UM 130,000.00"
    app.selectbox[0].select("Proyecto DEMO A").run()
    assert not app.exception
    assert app.metric[0].value == "UM 100,000.00"
    for seccion in ["Registro de trabajos", "Seguimiento de avances", "Valorizaciones", "Reportes y exportación"]:
        next(x for x in app.radio if x.label == "Navegación").set_value(seccion).run()
        assert not app.exception, seccion


def test_registro_manual_y_rechazo_sin_perder_sesion():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    next(x for x in app.radio if x.label == "Navegación").set_value("Registro de trabajos").run()
    # Unidad monetaria es el primer text_input; los siguientes son del formulario.
    for label, valor in [("Proyecto", "PROYECTO TEST"), ("Código de trabajo", "TEST-01"),
                          ("Frente de trabajo", "Norte"), ("Descripción del trabajo", "Prueba manual")]:
        next(x for x in app.text_input if x.label == label).set_value(valor)
    next(x for x in app.button if x.label == "Registrar trabajo").click().run()
    assert not app.exception
    assert len(app.session_state["partidas"]) == 9
    # Repetir el código no añade una segunda partida.
    next(x for x in app.button if x.label == "Registrar trabajo").click().run()
    assert len(app.session_state["partidas"]) == 9
    assert app.error
    next(x for x in app.radio if x.label == "Navegación").set_value("Seguimiento de avances").run()
    trabajo = next(x for x in app.selectbox if x.label == "Trabajo (proyecto / código)")
    trabajo.set_value(("PROYECTO TEST", "TEST-01"))
    next(x for x in app.number_input if x.label == "Metrado programado del período").set_value(20)
    next(x for x in app.number_input if x.label == "Metrado ejecutado del período").set_value(10)
    next(x for x in app.button if x.label == "Registrar avance").click().run()
    assert not app.exception
    assert len(app.session_state["avances"]) == 19
    next(x for x in app.radio if x.label == "Navegación").set_value("Dashboard general").run()
    assert not app.exception
    assert len(app.session_state["partidas"]) == 9


def test_sesion_vacia_y_rango_invalido():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    next(x for x in app.button if x.label == "Iniciar sesión vacía").click().run()
    assert not app.exception
    assert app.metric[0].value == "UM 0.00"
    assert len(app.get("plotly_chart")) == 4
    from datetime import date
    next(x for x in app.date_input if x.label == "Desde").set_value(date(2027, 1, 1)).run()
    assert app.error
    assert not app.exception
