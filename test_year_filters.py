import json
from io import BytesIO
from pathlib import Path
import pandas as pd
from etl import clean
from test_metrics import _fake_row
from metrics import compute_all_metrics
from archetypes import classify
from year_filters import filter_year, ALL_YEARS


def rows():
    return ([_fake_row(f'2024-06-01T12:{i:02}:00Z',f'Track {i}','A') for i in range(20)] +
            [_fake_row(f'2026-06-01T12:{i:02}:00Z',f'Track {i}',f'Artist {i}',ms=8000,skipped=True) for i in range(20)])


def test_yearly_archetypes_can_differ():
    df=clean(pd.DataFrame(rows()),timezone='UTC')
    assert len(filter_year(df,ALL_YEARS))==40
    a=classify(compute_all_metrics(filter_year(df,'2024')))
    b=classify(compute_all_metrics(filter_year(df,'2026')))
    assert a['arquetipo'] != b['arquetipo']


def test_independent_filters_and_removed_tabs(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    upload=BytesIO(json.dumps(rows()).encode());upload.name='history.json'
    monkeypatch.setattr(st,'file_uploader',lambda *a,**k:[upload])
    app=AppTest.from_file(str(Path(__file__).with_name('app.py')))
    app.session_state["data_source"] = "Subir mis archivos"
    app.run(timeout=30)
    assert not app.exception
    for key in ['summary','archetype','time','artists']:
        assert app.selectbox(key=f'year_{key}').value==ALL_YEARS
    assert app.metric[0].value=='40'
    assert not any('Contraste nocturno' in t.label or 'Origen de escucha' in t.label for t in app.tabs)
    app.selectbox(key='year_archetype').set_value('2024').run()
    first=next(h.value for h in app.subheader if h.value.startswith('Tu arquetipo:'))
    app.selectbox(key='year_archetype').set_value('2026').run()
    second=next(h.value for h in app.subheader if h.value.startswith('Tu arquetipo:'))
    assert first != second and app.metric[0].value=='40'
    app.selectbox(key='year_summary').set_value('2024').run()
    assert not app.exception and app.metric[0].value=='20'
    assert app.selectbox(key='calendar_year').value==2024
    assert app.selectbox(key='year_archetype').value=='2026'
    for key in ['time','artists']:
        app.selectbox(key=f'year_{key}').set_value('2024').run()
        assert not app.exception
    # Replacing the upload with a single available year resets stale choices.
    upload.seek(0);upload.truncate();upload.write(json.dumps(rows()[:20]).encode())
    app.run()
    assert not app.exception
    assert app.selectbox(key='year_archetype').value==ALL_YEARS
