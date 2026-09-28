import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from wrapped import generate_card, FORMATS, playful_phrase
from test_metrics import _fake_row
from etl import clean
from metrics import compute_all_metrics
from archetypes import classify
import pandas as pd


def sample():
    rows = [_fake_row(f'2025-01-01T{h:02}:00:00Z', f'Track {h}', artist)
            for h, artist in enumerate(['Radiohead', 'Björk', 'Tyler, The Creator']*7)]
    df = clean(pd.DataFrame(rows))
    metrics = compute_all_metrics(df)
    return metrics, classify(metrics)


@pytest.mark.parametrize('format_name', FORMATS)
def test_png_dimensions_and_long_names(format_name):
    m, result = sample()
    m['top_artists'] = {'Nombre de artista exageradamente largo '*10: 100}
    content = generate_card(m, result, '01/01/2024 — 01/01/2026', format_name)
    with Image.open(BytesIO(content)) as image:
        assert image.format == 'PNG' and image.size == FORMATS[format_name]
        image.verify()


def test_phrase_uses_observed_data():
    m, _ = sample()
    m['skip_rate'] = .65
    assert '65%' in playful_phrase(m)
    m['skip_rate'] = 0
    m['top_artist_concentration'] = .8
    assert '80%' in playful_phrase(m)


def test_card_generate_download_and_invalidation(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    file = BytesIO(json.dumps([_fake_row('2025-01-01T12:00:00Z', 'Song', 'Björk')]).encode())
    file.name = 'history.json'
    monkeypatch.setattr(st, 'file_uploader', lambda *a, **k: [file])
    app = AppTest.from_file(str(Path(__file__).with_name('app.py')))
    app.session_state["data_source"] = "Subir mis archivos"
    app.run(timeout=20)
    app.button[0].click().run()
    assert not app.exception
    assert len(app.get('download_button')) == 1
    first = app.session_state['wrapped_card']
    assert Image.open(BytesIO(first[1])).size == (1080, 1920)
    app.radio[1].set_value('LinkedIn · 4:5').run()
    assert len(app.get('download_button')) == 0
    app.button[0].click().run()
    assert not app.exception
    second = app.session_state['wrapped_card']
    assert second[0] != first[0]
    assert Image.open(BytesIO(second[1])).size == (1080, 1350)
    app.selectbox[0].set_value('UTC').run()
    # Data-driven signature invalidates the old card when the time-slot metrics change.
    assert len(app.get('download_button')) == 0


if __name__ == '__main__':
    m, result = sample()
    result['arquetipo'] = 'El Coleccionista Ecléctico'
    output = Path(__file__).parent
    for name in FORMATS:
        suffix = 'story' if name.startswith('Historia') else 'linkedin'
        (output / f'preview-{suffix}.png').write_bytes(generate_card(m, result, '01/01/2024 — 19/09/2026', name))
