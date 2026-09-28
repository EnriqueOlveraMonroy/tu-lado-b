"""Reencuentros con canciones, calculados sobre los registros disponibles."""
import pandas as pd


def musical_comebacks(df, min_gap_days=90, window_days=30, min_return_plays=3):
    columns = ['track', 'artist', 'previous', 'returned', 'gap_days', 'plays', 'window_end', 'partial']
    if df.empty:
        return pd.DataFrame(columns=columns)
    d = df.dropna(subset=['track', 'artist', 'ts']).sort_values('ts', kind='stable')
    coverage_end = df['ts'].max()
    records = []
    for (track, artist), group in d.groupby(['track', 'artist'], sort=False):
        if not str(track).strip() or not str(artist).strip():
            continue
        times = group['ts'].reset_index(drop=True)
        gaps = times.diff()
        for index in gaps[gaps >= pd.Timedelta(days=min_gap_days)].index:
            returned = times.iloc[index]
            end = returned + pd.Timedelta(days=window_days)
            # Count the return and subsequent plays in [return, return + 30 days).
            count = int(times.searchsorted(end, side='left') - index)
            if count < min_return_plays:
                continue
            records.append(dict(track=track, artist=artist, previous=times.iloc[index-1],
                                returned=returned, gap_days=int(gaps.iloc[index].days),
                                plays=count, window_end=end, partial=coverage_end < end))
    return pd.DataFrame(records, columns=columns).sort_values(
        ['plays', 'gap_days', 'returned'], ascending=[False, False, True]
    ).reset_index(drop=True)


def render_comeback(df):
    import streamlit as st
    st.markdown('### El regreso del ex musical')
    st.caption('Esa canción que desapareció de tu historial y volvió con ganas de quedarse.')
    results = musical_comebacks(df)
    if results.empty:
        st.info('Todavía no encontramos un regreso con al menos 90 días sin registros y 3 reproducciones en los 30 días posteriores. Prueba cargar más años de tu historial.')
    else:
        row = results.iloc[0]
        st.write(f"{row['track']} — {row['artist']}")
        gap, date, plays = st.columns(3)
        gap.metric('Días entre escuchas registradas', int(row['gap_days']))
        date.metric('Fecha del regreso', row['returned'].strftime('%d/%m/%Y'))
        plays.metric('Reproducciones tras el regreso', int(row['plays']))
        st.write(f"Pasaron {int(row['gap_days'])} días… y todavía te sabías el camino de vuelta.")
        st.caption(f"Registro anterior: {row['previous']:%d/%m/%Y %H:%M}. Ventana del regreso: {row['returned']:%d/%m/%Y %H:%M} a antes del {row['window_end']:%d/%m/%Y %H:%M}. Incluye la reproducción del regreso.")
        if row['partial']:
            st.info('Tus archivos terminan antes de completar los 30 días de este regreso. El conteo mostrado es parcial.')
    st.caption('Buscamos pausas de al menos 90 días y un mínimo de 3 reproducciones en los siguientes 30 días. Destacamos el regreso con más reproducciones; en empate, la pausa más larga. Se distingue por canción y artista y se incluyen escuchas breves. La ausencia de registros no prueba que no la hayas escuchado: podrían faltar archivos.')
