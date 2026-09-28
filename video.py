"""Vista sencilla para archivos Streaming_History_Video de Spotify."""
import hashlib
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from design import chart
from section_export import download_section


def clean_video(content, timezone):
    try:
        raw = json.loads(content.decode('utf-8-sig'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('El archivo no contiene un JSON válido.') from exc
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise ValueError('Se esperaba una lista de reproducciones de video.')
    if not raw:
        raise ValueError('El historial está vacío.')
    d = pd.DataFrame(raw)
    required = {'ts', 'ms_played'}
    if not required.issubset(d.columns):
        raise ValueError('Faltan los campos de fecha o duración (ts, ms_played). Usa el historial ampliado de video.')
    try:
        zone = ZoneInfo(timezone)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ValueError('La zona horaria no es válida.') from exc
    timestamps = pd.to_datetime(d['ts'], utc=True, errors='coerce', format='mixed')
    durations = pd.to_numeric(d['ms_played'], errors='coerce')
    valid = timestamps.notna() & durations.notna() & np.isfinite(durations) & (durations >= 0)
    omitted = int((~valid).sum())
    d = d.loc[valid].copy()
    if d.empty:
        raise ValueError('No hay reproducciones con fecha y duración válidas.')
    d['ts'] = timestamps.loc[valid].dt.tz_convert(zone)
    d['minutes'] = durations.loc[valid] / 60000
    d['month'] = d['ts'].dt.strftime('%Y-%m')
    d['hour'] = d['ts'].dt.hour
    d['weekday'] = d['ts'].dt.dayofweek
    # Export variants may identify video as an episode or music track.
    def first_text(columns):
        values = pd.Series('', index=d.index, dtype='object')
        for column in columns:
            if column in d:
                candidate = d[column].map(lambda value: value.strip() if isinstance(value, str) else '')
                values = values.where(values.ne(''), candidate)
        return values
    d['title'] = first_text(['video_title', 'video_name', 'episode_name', 'master_metadata_track_name'])
    d['creator'] = first_text(['episode_show_name', 'master_metadata_album_artist_name', 'show_name', 'creator_name'])
    d['video_id'] = first_text(['spotify_video_uri', 'spotify_episode_uri', 'spotify_track_uri', 'video_uri'])
    return d[['ts', 'minutes', 'month', 'hour', 'weekday', 'title', 'creator', 'video_id']], omitted


def process_videos(files, timezone):
    frames, accepted, warnings, seen = [], [], [], set()
    for name, content in files:
        if not name.lower().startswith('streaming_history_video'):
            warnings.append(f'{name}: selecciona archivos Streaming_History_Video_*.json para evitar mezclar audio y video.')
            continue
        digest = hashlib.sha256(content).digest()
        if digest in seen:
            warnings.append(f'{name}: archivo idéntico a otro ya incluido; se omitió.')
            continue
        seen.add(digest)
        try:
            frame, omitted = clean_video(content, timezone)
        except ValueError as exc:
            warnings.append(f'{name}: {exc}')
            continue
        frames.append(frame)
        accepted.append(name)
        if omitted:
            warnings.append(f'{name}: se omitieron {omitted} registros con fecha o duración inválida.')
    return (pd.concat(frames, ignore_index=True).sort_values('ts').reset_index(drop=True)
            if frames else pd.DataFrame()), accepted, warnings


def video_figures(d):
    monthly = d.groupby('month').agg(Minutos=('minutes', 'sum'), Reproducciones=('ts', 'size')).reset_index().rename(columns={'month': 'Mes'})
    hourly = d.groupby('hour').size().reindex(range(24), fill_value=0).rename('Reproducciones').reset_index().rename(columns={'hour': 'Hora'})
    weekdays = d.groupby('weekday')['minutes'].sum().reindex(range(7), fill_value=0)
    weekly = pd.DataFrame({'Día': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'], 'Minutos': weekdays.values})
    figures = [px.bar(monthly, x='Mes', y='Reproducciones', title='Reproducciones de video por mes'),
               px.line(monthly, x='Mes', y='Minutos', markers=True, title='Minutos de video por mes'),
               px.bar(hourly, x='Hora', y='Reproducciones', title='A qué hora reproduces videos'),
               px.bar(weekly, x='Día', y='Minutos', title='Minutos por día de la semana')]
    for fig in figures:
        fig.update_traces(marker_color='#1ED760')
        fig.update_layout(height=360, showlegend=False)
    figures[1].update_traces(line_color='#1ED760')
    figures[2].update_xaxes(dtick=2)
    return figures


def video_ranking(d):
    """Group by URI when available, otherwise title + creator. Never merge unknowns."""
    d = d.copy()
    # Recover missing titles only when the same exported URI has a named record.
    for column in ['title', 'creator']:
        known = d[d['video_id'].ne('') & d[column].ne('')].drop_duplicates('video_id')
        lookup = known.set_index('video_id')[column]
        d[column] = d[column].where(d[column].ne(''), d['video_id'].map(lookup).fillna(''))
    missing = int(d['title'].eq('').sum())
    d = d[d['title'].ne('')].copy()
    d['identity'] = [json.dumps(['uri', uri] if uri else ['title', title, creator], ensure_ascii=False)
                     for uri, title, creator in zip(d['video_id'], d['title'], d['creator'])]
    ranking = d.groupby('identity', sort=False).agg(
        Título=('title', 'first'), Creador=('creator', 'first'),
        Reproducciones=('ts', 'size'), Minutos=('minutes', 'sum'),
        Última_reproducción=('ts', 'max'), Identificador=('video_id', 'first'),
    ).reset_index(drop=True)
    ranking = ranking.sort_values(['Reproducciones', 'Minutos', 'Título'], ascending=[False, False, True]).reset_index(drop=True)
    ranking['Creador'] = ranking['Creador'].replace('', 'No disponible')
    return ranking, missing


def ranking_figure(ranking):
    top = ranking.head(10).copy()
    # Ordinal prefix keeps homonymous videos on separate bars.
    top['Video'] = [f"{i+1}. {title[:52]}{'…' if len(title)>52 else ''}"
                    for i, title in enumerate(top['Título'])]
    fig = px.bar(top, x='Reproducciones', y='Video', orientation='h',
                 text='Reproducciones', custom_data=['Título', 'Creador', 'Minutos'],
                 title='Tus 10 videos más reproducidos', color_discrete_sequence=['#1ED760'])
    fig.update_traces(hovertemplate='%{customdata[0]}<br>%{customdata[1]}<br>%{x} reproducciones<br>%{customdata[2]:.1f} minutos<extra></extra>')
    fig.update_layout(height=max(360, len(top)*42+130), yaxis=dict(autorange='reversed'), showlegend=False)
    return fig


def render_video_ranking(d):
    st.subheader('¿Cuáles videos reproduces más?')
    ranking, missing = video_ranking(d)
    if missing:
        st.warning(f'{missing:,} reproducciones no incluyen un título identificable. Se conservan en las gráficas de actividad, pero se excluyen del ranking por video.')
    if ranking.empty:
        st.info('Estos archivos no incluyen títulos reconocibles de videos o episodios. Podemos mostrar tu actividad, pero no identificar los videos por nombre.')
        return
    chart(ranking_figure(ranking), use_container_width=True)
    st.caption('Ordenados por reproducciones; en caso de empate, por minutos. Cada registro cuenta como una reproducción, aunque sea breve: no necesariamente viste el video completo.')
    table = ranking.rename(columns={'Creador': 'Programa o creador', 'Última_reproducción': 'Última reproducción'}).copy()
    table['Última reproducción'] = table['Última reproducción'].dt.strftime('%d/%m/%Y %H:%M')
    table['Minutos'] = table['Minutos'].round(1)
    table.insert(0, 'Lugar', range(1, len(table)+1))
    st.dataframe(table, hide_index=True, use_container_width=True)


def render_video(timezone, example_uploads=None):
    st.subheader('Tu historial de video')
    st.caption('Carga uno o varios archivos Streaming_History_Video_*.json. Aquí verás tus videos más reproducidos y gráficas sencillas de actividad.')
    if example_uploads is None:
        st.caption("Tus archivos se envían al servidor para analizarlos durante la sesión. No se publican como ejemplos ni se guardan como archivos.")
        files = st.file_uploader('Archivos de historial de video (.json)', type=['json'],
                                 accept_multiple_files=True, key='video_uploads')
        st.caption(f"Hasta {st.get_option('server.maxUploadSize')} MB por archivo. Selecciona todos los años que quieras analizar.")
    else:
        files = example_uploads
    if not files:
        st.info('Selecciona tus archivos de video para ver las gráficas.')
        return
    with st.spinner('Procesando los historiales de video...'):
        d, accepted, warnings = process_videos(((f.name, f.getvalue()) for f in files), timezone)
    for warning in warnings:
        st.warning(warning)
    if d.empty:
        st.error('No hay registros de video válidos para graficar.')
        return
    st.caption(f"{len(accepted)} archivos incluidos · Del {d['ts'].min():%d/%m/%Y} al {d['ts'].max():%d/%m/%Y}")
    download_section("Historial de video", "videos", video=True)
    render_video_ranking(d)
    figures = video_figures(d)
    for index in (0, 2):
        columns = st.columns(2)
        for column, fig in zip(columns, figures[index:index+2]):
            with column:
                chart(fig, use_container_width=True)
    st.caption('Horarios en tu zona seleccionada, según el fin de cada reproducción. Se suma todo el tiempo registrado, incluso reproducciones breves. Los meses sin registros no se inventan como ceros. El historial no permite confirmar cuánto tiempo miraste la pantalla.')
