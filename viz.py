"""
Funciones de visualización con Plotly, listas para insertar en Streamlit
con st.plotly_chart(fig, use_container_width=True).
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from rich_charts import polish


DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_LABELS_ES = {
    "Monday": "Lun", "Tuesday": "Mar", "Wednesday": "Mié", "Thursday": "Jue",
    "Friday": "Vie", "Saturday": "Sáb", "Sunday": "Dom",
}


def hourly_heatmap(df: pd.DataFrame) -> go.Figure:
    """Mapa de calor: día de la semana x hora, intensidad = # de reproducciones."""
    pivot = (
        df.groupby(["day_of_week", "hour"])
        .size()
        .reset_index(name="plays")
        .pivot(index="day_of_week", columns="hour", values="plays")
        .reindex(index=DAY_ORDER, columns=range(24))
        .fillna(0)
    )
    pivot.index = [DAY_LABELS_ES[d] for d in pivot.index]

    fig = px.imshow(
        pivot,
        labels=dict(x="Hora del día", y="Día", color="Reproducciones"),
        color_continuous_scale="Greens",
        aspect="auto",
    )
    fig.update_layout(
        title="Cuándo escuchas música",
        xaxis=dict(tickmode="linear", dtick=2),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return polish(fig)


def archetype_radar(scores: dict) -> go.Figure:
    """Radar chart comparando el score de todos los arquetipos evaluados."""
    labels = list(scores.keys())
    values = list(scores.values())
    # Cerrar el polígono
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        line_color="#1DB954",  # verde Spotify
        name="Tu perfil",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        title="Comparativa de arquetipos",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return polish(fig)


def top_artists_bar(df: pd.DataFrame, n: int = 10) -> go.Figure:
    counts = df["artist"].value_counts().head(n).sort_values()
    fig = px.bar(
        x=counts.values,
        y=counts.index,
        orientation="h",
        labels={"x": "Reproducciones", "y": ""},
        color=counts.values,
        color_continuous_scale="Greens",
    )
    fig.update_layout(
        title=f"Tus {n} artistas más escuchados",
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return polish(fig)


def time_slot_pie(df: pd.DataFrame) -> go.Figure:
    dist = df["time_slot"].value_counts()
    fig = px.pie(
        values=dist.values,
        names=dist.index,
        color_discrete_sequence=["#B5F56B", "#54D6CD", "#A99CFF", "#FFBC75"],
        hole=0.45,
    )
    fig.update_layout(title="Distribución por franja horaria", margin=dict(l=10, r=10, t=40, b=10))
    return polish(fig)


def monthly_minutes_line(df: pd.DataFrame) -> go.Figure:
    monthly = df.loc[~df["is_ghost_play"]].groupby("month")["minutes_played"].sum().reset_index()
    fig = px.line(
        monthly, x="month", y="minutes_played", markers=True,
        labels={"month": "Mes", "minutes_played": "Minutos escuchados"},
    )
    fig.update_traces(line_color="#1DB954")
    fig.update_layout(title="Minutos escuchados por mes", margin=dict(l=10, r=10, t=40, b=10))
    return polish(fig)
