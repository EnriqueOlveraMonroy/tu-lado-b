"""
Tu Lado B — Perfil de autoconocimiento conductual musical.

Ejecutar con: python -m streamlit run app.py
"""
from design import apply_design, hero, chart as show_chart
import json
import hashlib
from zoneinfo import available_timezones

import streamlit as st
import pandas as pd

from section_export import download_section
from video import render_video
from examples import available_profiles, example_files
from etl import clean  # noqa: E402
from metrics import compute_all_metrics  # noqa: E402
from insight_views import render_findings, render_evolution
from year_filters import year_selector
from rich_charts import render_calendar_section, render_discovery, hourly_profile, artist_year_map, top_tracks
from wrapped import FORMATS, generate_card
from archetype_lore import LORE, avatar_path
from archetypes import classify  # noqa: E402
from viz import (  # noqa: E402
    hourly_heatmap, archetype_radar, top_artists_bar,
    time_slot_pie, monthly_minutes_line,
)

st.set_page_config(
    page_title="Tu Lado B",
    page_icon="🎧",
    layout="wide",
)


@st.cache_data(show_spinner=False, ttl=1800, max_entries=8)
def process_upload(file_bytes: bytes, timezone: str) -> pd.DataFrame:
    """Carga el JSON subido por el usuario y aplica el ETL. Cacheado por contenido."""
    try:
        raw = json.loads(file_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("El archivo no es un JSON válido en UTF-8.") from exc
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise ValueError("Se esperaba una lista de reproducciones del historial ampliado de Spotify.")
    if not raw:
        raise ValueError("El archivo está vacío: no contiene reproducciones.")
    return clean(pd.DataFrame(raw), timezone=timezone)


def process_uploads(files: list[tuple[str, bytes]], timezone: str):
    """Combina archivos válidos y devuelve avisos por archivo omitido.

    Solo evita archivos idénticos; conserva las reproducciones repetidas
    dentro de un historial, que pueden ser escuchas legítimas.
    """
    frames, warnings, accepted = [], [], []
    seen = set()
    for name, content in files:
        if name.lower().startswith("streaming_history_video"):
            warnings.append(f"{name}: omitido; selecciona los historiales Audio para este análisis musical.")
            continue
        digest = hashlib.sha256(content).digest()
        if digest in seen:
            warnings.append(f"{name}: omitido porque su contenido es idéntico a otro archivo cargado.")
            continue
        seen.add(digest)
        try:
            frame = process_upload(content, timezone)
        except ValueError as exc:
            warnings.append(f"{name}: {exc}")
            continue
        if frame.empty:
            warnings.append(f"{name}: no contiene reproducciones de música.")
            continue
        frames.append(frame)
        accepted.append(name)
    combined = (pd.concat(frames, ignore_index=True).sort_values("ts", kind="stable")
                .reset_index(drop=True)) if frames else pd.DataFrame()
    return combined, accepted, warnings


def render_header():
    apply_design()
    hero()


def render_uploader():
    st.caption("Tus archivos se envían al servidor para analizarlos. No se publican como ejemplos ni se guardan como archivos; los datos procesados pueden permanecer temporalmente en memoria y en caché hasta 30 minutos.")
    files = st.file_uploader(
        "Archivos de historial de audio (.json)",
        type=["json"],
        accept_multiple_files=True,
        help="Selecciona todos los JSON Streaming_History_Audio, de cualquier año o parte. Puedes usar Ctrl o Shift, o arrastrarlos juntos. No necesitas el PDF ni los archivos Video.",
    )
    st.caption(f"Archivos JSON · Hasta {st.get_option('server.maxUploadSize')} MB por archivo. Selecciona varios con Ctrl o arrástralos juntos.")
    return files


def render_kpis(m: dict):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reproducciones", f"{m['n_plays']:,}")
    c2.metric("Minutos escuchados", f"{m['total_minutes']:,.0f}")
    c3.metric("Artistas únicos", m["unique_artists"])
    c4.metric("Canciones únicas", m["unique_tracks"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Porcentaje de saltos", f"{m['skip_rate']*100:.1f}%")
    c6.metric("Diversidad de artistas", f"{m['artist_entropy']*100:.0f}%")
    c7.metric("Reproducción aleatoria", f"{m['shuffle_pct']*100:.0f}%")
    c8.metric("Mayor racha de un artista", f"{m['max_artist_streak']} seguidas")


def render_archetype(result: dict):
    st.subheader(f"Tu arquetipo: {result['arquetipo']}")
    lore = LORE[result['arquetipo']]
    portrait, narrative = st.columns([1, 2])
    with portrait:
        st.image(str(avatar_path(result['arquetipo'])), use_container_width=True)
        st.caption(lore['symbol'])
    with narrative:
        st.markdown(f"*{lore['essence']}*")
        st.write(lore['story'])
        st.markdown(f"**Tu don:** {lore['gift']}")
        st.markdown(f"**Tu sombra:** {lore['shadow']}")
        st.markdown(f"**Tu ritual:** {lore['ritual']}")
    st.caption('Retratos simbólicos de hábitos de escucha. El tono místico es narrativo; no es una evaluación psicológica.')
    with st.expander('El atlas de los cinco arquetipos'):
        for name, entry in LORE.items():
            image_col, text_col = st.columns([1, 3])
            with image_col:
                st.image(str(avatar_path(name)), width=150)
            with text_col:
                st.markdown(f"**{name} · {entry['symbol']}**")
                st.write(entry['story'])
                st.caption('Señales: ' + entry['evidence'])
    st.progress(result["score"], text=f"Afinidad: {result['score']*100:.0f}%")

    with st.expander("¿Por qué este arquetipo? (desglose de señales)"):
        for signal, value in result["por_que"].items():
            st.write(f"- **{signal}**: {value*100:.0f}%")

    show_chart(archetype_radar(result["todos_los_scores"]), use_container_width=True)


def render_wrapped(df, metrics, result, timezone):
    st.subheader("Tu música merece su propia portada")
    st.caption("Tu arquetipo, tus 3 artistas principales y una frase basada en tus hábitos. Descarga y comparte donde quieras.")
    format_name = st.radio("Formato de tarjeta", list(FORMATS), horizontal=True)
    period = f"{df['ts'].min():%d/%m/%Y} — {df['ts'].max():%d/%m/%Y}"
    # The signature prevents downloading an old card after uploads/timezone/format change.
    signature = hashlib.sha256(json.dumps(
        ["tu-lado-b-v1", metrics, result, period, format_name, timezone], sort_keys=True, default=str
    ).encode()).hexdigest()
    if st.button("Crear mi tarjeta para historias o LinkedIn", type="primary"):
        with st.spinner("Diseñando tu tarjeta..."):
            st.session_state['wrapped_card'] = (signature, generate_card(metrics, result, period, format_name))
    stored = st.session_state.get('wrapped_card')
    if stored and stored[0] == signature:
        card = stored[1]
        st.image(card, width=360)
        suffix = 'historia' if format_name == 'Historia · 9:16' else 'linkedin'
        st.download_button("Descargar tarjeta PNG", data=card,
                           file_name=f"tu-lado-b-{suffix}.png", mime="image/png")
    else:
        st.info("Elige el formato y genera tu tarjeta para verla aquí.")


def main():
    render_header()
    video_mode = st.toggle("Analizar historiales de video", key="video_mode")
    with st.container(border=True):
        st.subheader("01 · Conecta con tu historia")
        st.caption("Elige tu zona horaria y carga los historiales del modo seleccionado. Puedes combinar varios años.")
        zones = sorted(available_timezones())
        timezone = st.selectbox("Tu zona horaria", zones,
                                index=zones.index("America/Mexico_City"),
                                help="Elige dónde escuchas música para interpretar correctamente tus horarios.")
        profiles = available_profiles()
        source_options = ["Explorar ejemplos", "Subir mis archivos"] if profiles else ["Subir mis archivos"]
        if st.session_state.get("data_source") not in source_options:
            st.session_state["data_source"] = source_options[0]
        source = st.radio("¿Cómo quieres explorar Tu Lado B?", source_options,
                          key="data_source", horizontal=True)
        profile = None
        if source == "Explorar ejemplos":
            if st.session_state.get("example_profile") not in profiles:
                st.session_state["example_profile"] = profiles[0]
            profile = st.selectbox("Elige un usuario de ejemplo", profiles, key="example_profile")
            st.info(f"Estás explorando {profile}. Sus datos son de ejemplo; no son tu historial. Puedes probar los filtros, arquetipos y descargas.")
        identity = (source, profile)
        if st.session_state.get("active_data_identity") != identity:
            for key in ("year_summary", "year_archetype", "year_time", "year_artists", "calendar_year", "wrapped_card"):
                st.session_state.pop(key, None)
            st.session_state["active_data_identity"] = identity
        if profile:
            try:
                files = example_files(profile, video=video_mode)
            except (OSError, ValueError):
                st.error("No se pudieron leer los archivos de este ejemplo.")
                return
            if not files:
                st.info("Este usuario no tiene historiales de video disponibles." if video_mode else "Este usuario no tiene historiales de audio disponibles.")
                return
        else:
            files = render_uploader() if not video_mode else []

    if video_mode:
        with st.container(key="video_report"):
            render_video(timezone, files if profile else None)
        return

    if not files:
        st.info("Selecciona uno o varios archivos de audio para analizar juntos.")
        st.markdown(
            "**¿Dónde consigo el archivo?** Spotify → Configuración → "
            "Privacidad de la cuenta → *Solicitar datos ampliados de streaming* "
            "(tarda unos días en llegar por correo electrónico)."
        )
        return

    with st.spinner("Combinando tus historiales..."):
        df, accepted, warnings = process_uploads(
            ((file.name, file.getvalue()) for file in files), timezone
        )
    for warning in warnings:
        st.warning(warning)
    if df.empty:
        st.error("No se encontraron reproducciones de música en los archivos seleccionados.")
        return
    st.success(f"{len(accepted)} de {len(files)} archivos incluidos · {len(df):,} reproducciones")
    st.caption(f"Período analizado: {df['ts'].min():%d/%m/%Y} a {df['ts'].max():%d/%m/%Y}")
    with st.expander("Archivos incluidos en el análisis"):
        for name in accepted:
            st.text(name)

    st.subheader("02 · Así suena tu mundo")
    metrics = compute_all_metrics(df)
    result = classify(metrics)

    tab_resumen, tab_arquetipo, tab_tiempo, tab_artistas, tab_wrapped, tab_findings, tab_evolution = st.tabs(
        ["📊 Resumen", "🧬 Tu arquetipo", "🕐 Cuándo escuchas", "🎤 Artistas", "✨ Mi Lado B · Wrapped", "🔎 Hallazgos insólitos", "📈 Evolución anual"]
    )

    with tab_resumen:
        download_section('Resumen', 'resumen')
        summary_df = year_selector(df, 'summary')
        render_kpis(compute_all_metrics(summary_df))
        show_chart(monthly_minutes_line(summary_df), use_container_width=True)
        render_calendar_section(summary_df)

    with tab_arquetipo:
        download_section('Tu arquetipo', 'arquetipo')
        archetype_df = year_selector(df, 'archetype')
        render_archetype(classify(compute_all_metrics(archetype_df)))

    with tab_tiempo:
        download_section('Cuándo escuchas', 'horarios')
        time_df = year_selector(df, 'time')
        col1, col2 = st.columns([2, 1])
        with col1:
            show_chart(hourly_heatmap(time_df), use_container_width=True)
        with col2:
            show_chart(time_slot_pie(time_df), use_container_width=True)

        show_chart(hourly_profile(time_df), use_container_width=True)
        st.caption("La línea de saltos usa solo registros con dato conocido; las horas sin datos quedan vacías. Cada eje tiene su propia unidad.")

    with tab_findings:
        download_section('Hallazgos insólitos', 'hallazgos')
        render_findings(df)
    with tab_evolution:
        download_section('Evolución anual', 'evolucion')
        render_evolution(df)
        show_chart(artist_year_map(df), use_container_width=True)
        st.caption("Los 12 artistas más reproducidos del historial completo; cada celda muestra su porcentaje en el año cargado.")

    with tab_wrapped:
        download_section('Mi Lado B · Wrapped', 'wrapped')
        st.caption("Esta tarjeta usa todos los años cargados. Los filtros de otras pestañas son independientes.")
        render_wrapped(df, metrics, result, timezone)

    with tab_artistas:
        download_section('Artistas', 'artistas')
        artists_df = year_selector(df, 'artists')
        show_chart(top_artists_bar(artists_df, n=15), use_container_width=True)
        show_chart(top_tracks(artists_df), use_container_width=True)
        render_discovery(artists_df)

    st.markdown('<div class="persona-footer">Hecho para quienes viven con audífonos. Proyecto independiente, sin afiliación con Spotify.</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
