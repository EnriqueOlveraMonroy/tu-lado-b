from design import chart as show_chart
"""Gráficos interactivos adicionales con agregaciones verificables."""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

COLORS = ['#B5F56B', '#54D6CD', '#A99CFF', '#FFBC75', '#F58FB5']


def polish(fig, height=420):
    fig.update_layout(template='plotly_dark', paper_bgcolor='#111916', plot_bgcolor='#111916',
                      font=dict(family='Arial, sans-serif', size=13, color='#EAF0E9'),
                      colorway=COLORS, height=height, margin=dict(l=30, r=30, t=75, b=55),
                      legend=dict(orientation='h', y=-.22), hoverlabel=dict(bgcolor='#26372D'),
                      title=dict(font=dict(size=21)), hovermode='closest')
    fig.update_xaxes(gridcolor='#25342D', zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor='#25342D', zeroline=False, automargin=True)
    return fig


def daily_data(df, year):
    d = df[df['ts'].dt.year == year]
    if d.empty:
        return pd.DataFrame(columns=['date', 'minutes', 'average'])
    dates = pd.date_range(pd.Timestamp(d['date'].min()), pd.Timestamp(d['date'].max()), freq='D')
    totals = d.loc[~d['is_ghost_play']].groupby('date')['minutes_played'].sum()
    result = pd.DataFrame({'date': dates, 'minutes': totals.reindex(dates.date, fill_value=0).values})
    result['average'] = result['minutes'].rolling(7, min_periods=1).mean()
    return result


def listening_calendar(df, year):
    d = daily_data(df, year)
    fig = go.Figure()
    if d.empty:
        return polish(fig)
    start = d['date'].min() - pd.Timedelta(days=d['date'].min().dayofweek)
    d['week'] = ((d['date']-start).dt.days//7).astype(int)
    d['weekday'] = d['date'].dt.dayofweek
    grid = d.pivot(index='weekday', columns='week', values='minutes').reindex(index=range(7))
    labels = d.assign(label=d['date'].dt.strftime('%d/%m/%Y')).pivot(index='weekday', columns='week', values='label').reindex(index=range(7)).fillna('')
    fig.add_trace(go.Heatmap(z=grid.values, x=list(grid.columns), y=['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'],
                            customdata=labels.values, colorscale=['#1B2922','#366643','#71B34D','#B5F56B'],
                            xgap=3, ygap=3, colorbar=dict(title='Minutos'),
                            hoverongaps=False, hovertemplate='%{customdata}<br>%{z:.1f} minutos<extra></extra>'))
    months = d.groupby(d['date'].dt.month).first()
    names = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    fig.update_xaxes(tickvals=months['week'], ticktext=[names[m-1] for m in months.index], showgrid=False)
    fig.update_yaxes(autorange='reversed', showgrid=False)
    fig.update_layout(title=f'Tu calendario musical · {year}')
    return polish(fig, 340)


def listening_trend(df, year):
    d = daily_data(df, year)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d['date'], y=d['minutes'], name='Minutos diarios', marker_color='#366643',
                        hovertemplate='%{x|%d/%m/%Y}<br>%{y:.1f} min<extra></extra>'))
    fig.add_trace(go.Scatter(x=d['date'], y=d['average'], name='Promedio móvil · 7 días', line=dict(color=COLORS[0], width=3),
                            hovertemplate='%{y:.1f} min/día<extra>Promedio móvil</extra>'))
    fig.update_layout(title='La intensidad de tu escucha', yaxis_title='Minutos', hovermode='x unified')
    polish(fig)
    fig.update_layout(hovermode='x unified')
    return fig


def hourly_profile(df):
    d = df.copy()
    d['known_skip'] = pd.to_numeric(d['skipped'], errors='coerce').where(d['skipped'].isin([True,False]))
    h = d.groupby('hour').agg(plays=('ts','size'), skips=('known_skip','mean'), known=('known_skip','count')).reindex(range(24))
    fig = go.Figure()
    fig.add_trace(go.Bar(x=h.index, y=h['plays'].fillna(0), name='Reproducciones', marker_color='#54D6CD'))
    fig.add_trace(go.Scatter(x=h.index, y=h['skips']*100, customdata=h['known'], name='Saltos (%)', yaxis='y2',
                            mode='lines+markers', connectgaps=False, line=dict(color='#F58FB5',width=3),
                            hovertemplate='%{x}:00 · %{y:.1f}% de saltos<br>%{customdata} registros conocidos<extra></extra>'))
    fig.update_layout(title='Tu reloj musical: volumen y saltos', xaxis=dict(title='Hora local',dtick=2),
                      yaxis_title='Reproducciones', yaxis2=dict(title='Saltos (%)', overlaying='y',side='right',range=[0,100],showgrid=False))
    return polish(fig)


def artist_year_map(df):
    d = df.assign(year=df['ts'].dt.year)
    leaders = d['artist'].value_counts().head(12).index
    counts = pd.crosstab(d['artist'],d['year']).reindex(leaders,fill_value=0)
    shares = counts.div(d.groupby('year').size(),axis=1)*100
    fig = go.Figure(go.Heatmap(z=shares.values, x=[str(y) for y in shares.columns], y=shares.index,
                              customdata=counts.values, colorscale=['#192722','#416B57','#54D6CD'],
                              colorbar=dict(title='% anual'),
                              hovertemplate='%{y} · %{x}<br>%{z:.1f}% del año<br>%{customdata} reproducciones<extra></extra>'))
    fig.update_layout(title='Tus artistas a través de los años', yaxis=dict(autorange='reversed'))
    return polish(fig, max(380,len(leaders)*34+130))


def top_tracks(df):
    counts = df.groupby(['track','artist']).size().nlargest(12).sort_values().rename('Reproducciones').reset_index()
    counts['Canción / artista'] = counts['track']+' — '+counts['artist']
    fig = px.bar(counts,x='Reproducciones',y='Canción / artista',orientation='h',text='Reproducciones',
                 color_discrete_sequence=['#A99CFF'],title='Las canciones que no sueltas')
    fig.update_traces(hovertemplate='%{y}<br>%{x} reproducciones<extra></extra>',textposition='outside',cliponaxis=False)
    return polish(fig, max(380,len(counts)*34+130))


def discovery_curve(df):
    d = df.sort_values('ts',kind='stable').dropna(subset=['artist']).copy()
    d['new'] = ~d['artist'].duplicated()
    monthly = d.groupby('month').agg(new=('new','sum'), unique=('artist','nunique'))
    fig = go.Figure()
    for column, name, color in [('unique','Artistas escuchados',COLORS[1]), ('new','Primera aparición en tu historial',COLORS[0])]:
        fig.add_trace(go.Scatter(x=monthly.index,y=monthly[column],name=name,mode='lines+markers',line=dict(color=color,width=3)))
    fig.update_layout(title='Exploración vs. favoritos', yaxis_title='Artistas',xaxis_title='Mes')
    polish(fig)
    fig.update_layout(hovermode='x unified')
    return fig


def render_calendar_section(df):
    st.subheader('Un año de música, día por día')
    years = sorted(df['ts'].dt.year.unique(), reverse=True)
    if st.session_state.get('calendar_year') not in years:
        st.session_state['calendar_year'] = years[0]
    year = st.selectbox('Año del calendario',years,key='calendar_year')
    show_chart(listening_calendar(df,year),use_container_width=True)
    show_chart(listening_trend(df,year),use_container_width=True)
    st.caption('Solo se muestra el intervalo entre el primer y último registro del año cargado. Cero significa sin minutos registrados, no prueba de inactividad. Minutos excluyen reproducciones de menos de 5 segundos. El promedio usa hasta 7 días disponibles.')


def render_discovery(df):
    show_chart(discovery_curve(df),use_container_width=True)
    st.caption('“Primera aparición” se refiere a los archivos cargados, no necesariamente al momento en que descubriste al artista. Los meses sin registros no se añaden como ceros.')
