import pandas as pd
from etl import clean
from test_metrics import _fake_row
from insights import curious_findings, yearly_evolution, night_contrast, playback_signals


def frame(rows):
    return clean(pd.DataFrame(rows), timezone='UTC')


def test_night_boundaries_and_interruption():
    rows = [_fake_row(f'2025-01-01T{hour}', song, 'A') for hour, song in
            [('01:59:00Z', 'X'), ('02:00:00Z', 'X'), ('02:03:00Z', 'X'),
             ('02:06:00Z', 'Y'), ('02:09:00Z', 'X'), ('02:12:00Z', 'X'),
             ('02:15:00Z', 'X'), ('04:00:00Z', 'X'), ('05:00:00Z', 'X')]]
    r = curious_findings(frame(rows))
    assert r['nocturnal']['plays'] == 6
    assert r['loops'].iloc[0]['plays'] == 3


def test_chaos_threshold_missing_skips_and_love_hate():
    rows = [_fake_row(f'2025-01-01T12:{i:02}:00Z', 'X', 'A', skipped=i<7) for i in range(10)]
    assert curious_findings(frame(rows))['chaos'].empty  # exactly 70% is excluded
    rows[7]['skipped'] = True
    rows.append(_fake_row('2025-01-01T13:00:00Z', 'X', 'A', skipped=None))
    r = curious_findings(frame(rows))
    assert r['chaos'].iloc[0]['rate'] == .8
    assert r['love_hate'].index[0] == 'A'
    assert r['love_hate'].iloc[0]['known'] == 10


def test_years_shares_and_coverage():
    rows = [_fake_row(f'{y}-01-01T12:00:00Z', 'X', a) for y,a in [(2020,'A'),(2020,'A'),(2022,'B')]]
    shares, summary = yearly_evolution(frame(rows))
    assert list(summary.index) == [2020,2022]
    assert list(summary['leader']) == ['A','B']
    assert shares.groupby('Año')['Porcentaje'].sum().tolist() == [100,100]


def test_missing_night_and_unknown_origin():
    d = frame([_fake_row('2025-01-01T12:00:00Z', 'X', 'A')])
    contrast = night_contrast(d)
    assert contrast.iloc[1]['Reproducciones'] == 0
    assert pd.isna(contrast.iloc[1]['Skip_pct'])
    d['reason_start'] = 'unexpected_code'
    signals, raw = playback_signals(d)
    assert signals.iloc[0]['Señal'] == 'Origen no identificable'
    assert signals.iloc[0]['Porcentaje'] == 100


def test_loops_do_not_bridge_dates_or_artists():
    d = frame([_fake_row('2025-01-01T02:00:00Z','X','A'),
               _fake_row('2025-01-01T02:03:00Z','X','B'),
               _fake_row('2025-01-02T02:06:00Z','X','B')])
    assert curious_findings(d)['loops'].empty


def test_populated_insights_views(monkeypatch):
    import json
    from io import BytesIO
    from pathlib import Path
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    rows = [_fake_row(f"{year}-01-01T08:{i:02}:00Z", "Song", "A", skipped=True)
            for year in [2024, 2025] for i in range(15)]
    upload = BytesIO(json.dumps(rows).encode())
    upload.name = "history.json"
    monkeypatch.setattr(st, "file_uploader", lambda *a, **k: [upload])
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")))
    app.session_state["data_source"] = "Subir mis archivos"
    app.run(timeout=20)
    assert not app.exception
    assert len(app.tabs) == 7
    assert any(m.label == "Reproducciones consecutivas" and m.value == "15" for m in app.metric)
