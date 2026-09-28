"""Filtros anuales independientes, basados en la zona horaria del historial."""
import streamlit as st

ALL_YEARS = 'Todos los años'


def filter_year(df, selection):
    if selection == ALL_YEARS:
        return df
    return df.loc[df['ts'].dt.year.eq(int(selection))].copy()


def year_selector(df, section):
    options = [ALL_YEARS] + [str(year) for year in sorted(df['ts'].dt.year.unique(), reverse=True)]
    key = f'year_{section}'
    if st.session_state.get(key, ALL_YEARS) not in options:
        st.session_state[key] = ALL_YEARS
    selected = st.selectbox('Año a analizar', options, key=key,
                            help='Este filtro solo cambia esta sección. Los años se calculan con tu zona horaria.')
    filtered = filter_year(df, selected)
    st.caption(f"{selected} · {len(filtered):,} reproducciones · Del {filtered['ts'].min():%d/%m/%Y} al {filtered['ts'].max():%d/%m/%Y}")
    return filtered
