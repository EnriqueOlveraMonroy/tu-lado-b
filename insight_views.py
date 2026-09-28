from design import chart as show_chart
import streamlit as st
import plotly.express as px
from musical_comeback import render_comeback
from insights import curious_findings, yearly_evolution, night_contrast, playback_signals


def render_findings(df):
    st.subheader('Hallazgos insólitos')
    minimum = st.slider('Mínimo de reproducciones con dato de salto conocido por día o artista', 5, 50, 10)
    findings = curious_findings(df, minimum)
    st.caption('Horarios de la zona seleccionada. Madrugada: desde las 02:00 hasta antes de las 05:00. Se incluyen reproducciones breves.')
    left, right = st.columns(2)
    with left:
        st.markdown('### La canción de la madrugada')
        song = findings['nocturnal']
        if song:
            st.write(f"{song['track']} — {song['artist']}")
            st.metric('Reproducciones entre las 02 y las 05 h', song['plays'])
        else:
            st.info('No hay canciones identificadas en esa franja.')
        st.markdown('### Bucle insomne')
        if findings['loops'].empty:
            st.info('No encontramos rachas de al menos 3 reproducciones de una canción en esa franja.')
        else:
            row = findings['loops'].iloc[0]
            st.write(f"{row['track']} — {row['artist']}")
            st.metric('Reproducciones consecutivas', int(row['plays']))
            st.caption(f"{row['start']:%d/%m/%Y %H:%M} – {row['end']:%H:%M}")
        st.caption('La racha termina si cambia la canción o el artista, cambia la fecha, sale de la franja o pasan más de 30 minutos entre registros.')
    with right:
        st.markdown('### El día de mayor caos')
        if findings['chaos'].empty:
            st.info('Ningún día supera el 70% de saltos con la muestra mínima elegida.')
        else:
            row = findings['chaos'].iloc[0]
            st.write(f"{findings['chaos'].index[0]:%d/%m/%Y}")
            st.metric('Porcentaje de saltos', f"{row['rate']:.1%}")
            st.caption(f"{int(row['skips'])} saltos / {int(row['known'])} registros conocidos; {int(row['plays'])} reproducciones totales.")
        st.markdown('### Tu artista amor-odio')
        if findings['love_hate'].empty:
            st.info('No hay suficientes reproducciones con saltos para identificarlo.')
        else:
            row = findings['love_hate'].iloc[0]
            st.write(str(findings['love_hate'].index[0]))
            st.metric('Reproducciones', int(row['plays']))
            st.caption(f"{int(row['skips'])} saltos; tasa {row['rate']:.1%} sobre {int(row['known'])} registros conocidos.")
        st.caption('Entre los 10 artistas más reproducidos que cumplen la muestra mínima, elegimos el de más saltos. No implica que te disguste.')
    render_comeback(df)
    artists = findings['artists'].dropna(subset=['rate']).reset_index()
    artists = artists[artists['known'] >= minimum].copy()
    if not artists.empty:
        artists['Saltos (%)'] = artists['rate']*100
        show_chart(px.scatter(artists, x='plays', y='Saltos (%)', hover_name='artist', size='skips',
                                  labels={'plays': 'Reproducciones', 'skips': 'Saltos'}, title='Amor-odio: volumen vs. porcentaje de saltos'), use_container_width=True)


def render_evolution(df):
    st.subheader('Cómo han cambiado tus artistas favoritos')
    st.caption('Comparación por artistas: estos archivos no aportan géneros ni ritmo fiables. Cada año se calcula solo con los archivos cargados; un año puede estar incompleto.')
    shares, summary = yearly_evolution(df)
    if len(summary) < 2:
        st.info('Carga al menos dos años para comparar la evolución. Aquí puedes ver el año disponible.')
    shares['Año'] = shares['Año'].astype(str)
    show_chart(px.bar(shares, x='Año', y='Porcentaje', color='Artista', barmode='stack',
                          title='Participación anual de los artistas · % de reproducciones'), use_container_width=True)
    table = summary.reset_index().rename(columns={'year': 'Año', 'plays': 'Reproducciones', 'days': 'Días con escucha',
                                                  'leader': 'Artista principal', 'leader_share': 'Cuota principal (%)',
                                                  'first': 'Primer registro', 'last': 'Último registro'})
    for col in ['Primer registro', 'Último registro']:
        table[col] = table[col].dt.strftime('%d/%m/%Y')
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.caption('Se muestran los cinco líderes de cada año; los demás se agrupan. Un año sin archivos no se interpreta como cero escucha.')


def render_contrast(df):
    st.subheader('Tu contraste nocturno')
    st.write('¿Saltas más canciones de madrugada? ¿Repites más? Compara comportamientos de escucha, sin convertirlos en un diagnóstico.')
    table = night_contrast(df)
    st.dataframe(table.rename(columns={'Skip_pct': 'Saltos (%)', 'Repetición_pct': 'Repetición consecutiva (%)',
                                      'Segundos_escuchados': 'Segundos escuchados por reproducción', 'Saltos_conocidos': 'Registros con dato de salto conocido'}), hide_index=True)
    if (table['Reproducciones'] < 10).any():
        st.info('Alguna franja tiene menos de 10 reproducciones. La comparación es limitada.')
    chart = table.melt(id_vars='Franja', value_vars=['Skip_pct', 'Repetición_pct'], var_name='Métrica', value_name='Porcentaje').dropna()
    if not chart.empty:
        chart['Métrica'] = chart['Métrica'].replace({'Skip_pct': 'Saltos', 'Repetición_pct': 'Repetición consecutiva'})
        show_chart(px.bar(chart, x='Franja', y='Porcentaje', color='Métrica', barmode='group'), use_container_width=True)
    st.caption('La duración es tiempo realmente escuchado, no duración total de la canción. Repetición: misma canción y artista que el registro anterior, misma fecha y hasta 30 min de separación. Estos datos no indican depresión, ansiedad, insomnio ni si la música es triste o acelerada.')


def render_playback(df):
    st.subheader('¿Elección propia o piloto automático?')
    st.info('El historial no distingue de forma fiable tus listas de reproducción, búsquedas, radios y recomendaciones. No calculamos un porcentaje de “resistencia al algoritmo” que estos datos no pueden demostrar.')
    st.write('Estas son las señales de inicio disponibles:')
    table, raw = playback_signals(df)
    show_chart(px.bar(table, x='Porcentaje', y='Señal', orientation='h', hover_data=['Reproducciones']), use_container_width=True)
    st.caption('Un clic puede elegir una recomendación; continuar al terminar una pista puede ocurrir en tu propia lista. La reproducción aleatoria tampoco identifica el origen de la música.')
    with st.expander('Ver motivos de inicio originales'):
        st.dataframe(raw, hide_index=True)
