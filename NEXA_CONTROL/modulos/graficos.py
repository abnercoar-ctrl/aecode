"""Cuatro gráficos Plotly generados únicamente a partir de tablas calculadas."""
import plotly.graph_objects as go

AZUL = "#377cf5"
VERDE = "#008577"
ROJO = "#d94d5b"


def _estilo(fig, titulo, eje_y="", eje_x=""):
    fig.update_layout(title=dict(text=titulo, font=dict(size=18)), template="plotly_white",
                      font=dict(family="Arial, sans-serif", color="#162d46", size=12),
                      height=350, margin=dict(l=10, r=20, t=55, b=35),
                      legend=dict(orientation="h", y=1.12, x=0),
                      xaxis_title=eje_x, yaxis_title=eje_y,
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(gridcolor="#edf1f5")
    fig.update_yaxes(gridcolor="#edf1f5", automargin=True)
    if not fig.data or all(len(traza.x) == 0 for traza in fig.data):
        fig.add_annotation(text="Sin registros para este alcance", showarrow=False, x=.5, y=.5,
                           xref="paper", yref="paper")
    return fig


def grafico_curva_s(serie):
    fig = go.Figure()
    for columna, nombre, color in [("avance_programado", "Programado", AZUL), ("avance_real", "Real", VERDE)]:
        fig.add_trace(go.Scatter(x=serie.fecha, y=serie[columna], mode="lines+markers", name=nombre,
                                line=dict(color=color, width=3), hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}%<extra>%{fullData.name}</extra>"))
    fig = _estilo(fig, "Curva S · historial al corte", "Avance ponderado (%)", "Fecha")
    fig.update_xaxes(tickformat="%Y-%m-%d", nticks=5)
    if len(serie) > 1:
        fig.update_xaxes(range=[serie.fecha.min(), serie.fecha.max()])
    return fig


def grafico_avance_frente(frentes):
    fig = go.Figure()
    etiquetas = frentes.proyecto + " / " + frentes.frente
    for columna, nombre, color in [("avance_programado", "Programado", AZUL), ("avance_real", "Real", VERDE)]:
        fig.add_trace(go.Bar(x=frentes[columna], y=etiquetas, orientation="h", name=nombre,
                            marker_color=color, hovertemplate="%{y}<br>%{x:.2f}%<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group", height=max(350, len(frentes) * 65 + 100))
    fig = _estilo(fig, "Avance por frente", eje_x="Avance ponderado (%)")
    fig.update_layout(height=max(350, len(frentes) * 65 + 100))
    return fig


def grafico_valorizaciones(mensuales, moneda="UM"):
    fig = go.Figure(go.Bar(x=mensuales.periodo, y=mensuales.valor_ejecutado, name="Ejecutado",
                           marker_color=VERDE, hovertemplate="%{x}<br>%{y:,.2f}<extra>Ejecutado</extra>"))
    fig = _estilo(fig, "Valorizaciones mensuales · período", f"Monto ({moneda})", "Mes")
    # Evita que Plotly interprete AAAA-MM como instantes y rotule semanas ajenas al período.
    fig.update_xaxes(type="category")
    return fig


def grafico_desviaciones(trabajos):
    etiquetas = trabajos.proyecto + " / " + trabajos.codigo
    fig = go.Figure(go.Bar(x=trabajos.desviacion_pp, y=etiquetas, orientation="h", name="Desviación",
                           marker_color=[VERDE if x >= 0 else ROJO for x in trabajos.desviacion_pp],
                           hovertemplate="%{y}<br>%{x:+.2f} pp<extra></extra>"))
    fig.add_vline(x=0, line_color="#94a3b8", line_width=1)
    fig = _estilo(fig, "Desviación por trabajo", eje_x="Real − programado (pp)")
    fig.update_layout(height=max(350, len(trabajos) * 30 + 110))
    return fig
