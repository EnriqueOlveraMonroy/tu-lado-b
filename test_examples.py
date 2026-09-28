import json
from pathlib import Path
import pytest
import examples
from test_metrics import _fake_row
from streamlit.testing.v1 import AppTest


@pytest.fixture
def demo_data(tmp_path, monkeypatch):
    for number in range(1, 5):
        folder = tmp_path / f'Usuario {number}' / 'nested'
        folder.mkdir(parents=True)
        rows = [_fake_row(f'{2020+number}-01-01T12:00:00Z', 'Song', f'Artist {number}')] * number
        (folder/'Streaming_History_Audio_test.json').write_text(json.dumps(rows))
        (folder/'Streaming_History_Video_test.json').write_text(json.dumps([{'ts':'2025-01-01T12:00:00Z','ms_played':60000}]))
        (folder/'ignore.json').write_text('[]')
    monkeypatch.setattr(examples, 'DATA_DIR', tmp_path)
    return tmp_path


def test_discovery_and_mode_isolation(demo_data):
    assert len(examples.available_profiles()) == 4
    assert len(examples.example_files('Usuario 1')) == 1
    assert 'Audio' in examples.example_files('Usuario 1')[0].name
    assert 'Video' in examples.example_files('Usuario 1', video=True)[0].name
    with pytest.raises(ValueError):
        examples.example_files('../Usuario 1')
    assert examples.available_profiles(demo_data/'missing') == []


def test_profile_switch_upload_and_video(demo_data):
    app = AppTest.from_file(str(Path(examples.__file__).with_name('app.py'))).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == '1'
    assert app.selectbox(key='example_profile').value == 'Usuario 1'
    app.selectbox(key='year_summary').set_value('2021').run()
    for number in range(2, 5):
        app.selectbox(key='example_profile').set_value(f'Usuario {number}').run(timeout=30)
        assert not app.exception
        assert app.metric[0].value == str(number)
        assert app.selectbox(key='year_summary').value == 'Todos los años'
    app.toggle[0].set_value(True).run(timeout=30)
    assert not app.exception and len(app.get('plotly_chart')) == 4
    app.radio(key='data_source').set_value('Subir mis archivos').run()
    assert not app.exception and not app.tabs
    assert len(app.get('file_uploader')) == 1


def test_missing_video_profile(demo_data):
    for file in (demo_data/'Usuario 1').rglob('*Video*.json'):
        file.unlink()
    app = AppTest.from_file(str(Path(examples.__file__).with_name('app.py')))
    app.session_state['video_mode'] = True
    app.run(timeout=30)
    assert not app.exception
    assert any('no tiene historiales de video' in item.value for item in app.info)
