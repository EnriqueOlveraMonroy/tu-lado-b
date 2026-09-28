import json
from io import BytesIO
from pathlib import Path
import pytest
from video import clean_video, process_videos, video_figures


def content(rows):
    return json.dumps(rows).encode()


def test_video_without_music_metadata_and_local_timezone():
    d, omitted = clean_video(content([{'ts':'2025-02-01T02:00:00Z','ms_played':60000}]),'America/Mexico_City')
    assert omitted == 0
    assert d.iloc[0]['month']=='2025-01' and d.iloc[0]['hour']==20
    assert d.iloc[0]['minutes']==1


def test_multiple_video_files_and_duplicate_audio_rejection():
    a=content([{'ts':'2024-01-01T00:00:00Z','ms_played':60000}])
    b=content([{'ts':'2025-01-01T00:00:00Z','ms_played':120000}])
    d, accepted, warnings=process_videos([('Streaming_History_Video_2024.json',a),('Streaming_History_Video_2025.json',b),
                                        ('Streaming_History_Video_copy.json',a),('Streaming_History_Audio_2024.json',a)],'UTC')
    assert len(accepted)==2 and len(warnings)==2 and len(d)==2
    assert d['minutes'].sum()==3
    figures=video_figures(d)
    assert len(figures)==4
    assert sum(figures[0].data[0].y)==2
    assert sum(figures[1].data[0].y)==3
    assert len(figures[2].data[0].x)==24
    assert len(figures[3].data[0].x)==7


@pytest.mark.parametrize('raw',[b'[]', b'{}', b'no json', b'[{}]'])
def test_invalid_video(raw):
    with pytest.raises(ValueError):
        clean_video(raw,'UTC')


def test_bad_rows_reported_and_zero_duration_kept():
    raw=content([{'ts':'bad','ms_played':1000},{'ts':'2024-01-01','ms_played':-1},
                 {'ts':'2024-01-01','ms_played':0}])
    d, omitted=clean_video(raw,'UTC')
    assert omitted==2 and len(d)==1 and d['minutes'].sum()==0


def test_video_mode_has_only_four_charts(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    upload=BytesIO(content([{'ts':'2025-01-01T12:00:00Z','ms_played':120000}]))
    upload.name='Streaming_History_Video_2025.json'
    monkeypatch.setattr(st,'file_uploader',lambda *a,**k:[upload] if k.get('key')=='video_uploads' else [])
    app=AppTest.from_file(str(Path(__file__).with_name('app.py')))
    app.session_state["data_source"] = "Subir mis archivos"
    app.run(timeout=20)
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert len(app.get('plotly_chart'))==4
    assert not app.tabs and not app.metric and not app.button
