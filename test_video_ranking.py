import json
from io import BytesIO
from pathlib import Path
from video import clean_video, video_ranking, ranking_figure


def fixture(rows):
    return json.dumps([dict(ts='2025-01-01T12:00:00Z', ms_played=60000, **row) for row in rows]).encode()


def test_titles_group_by_id_and_keep_different_creators():
    raw=fixture([
        dict(episode_name='Episodio uno',episode_show_name='Programa A',spotify_episode_uri='spotify:episode:a'),
        dict(episode_name=None,episode_show_name=None,spotify_episode_uri='spotify:episode:a'),
        dict(episode_name='Episodio uno',episode_show_name='Programa B',spotify_episode_uri='spotify:episode:b'),
        dict(video_title='Video sin URI',creator_name='C'),
        dict(video_title='Video sin URI',creator_name='D'),
        {},
    ])
    d,_=clean_video(raw,'UTC')
    ranking,missing=video_ranking(d)
    assert missing==1 and len(ranking)==4
    assert ranking.iloc[0]['Título']=='Episodio uno'
    assert ranking.iloc[0]['Creador']=='Programa A'
    assert ranking.iloc[0]['Reproducciones']==2
    assert ranking['Minutos'].sum()==5
    assert ranking['Reproducciones'].sum()+missing==len(d)
    fig=ranking_figure(ranking)
    assert len(set(fig.data[0].y))==4


def test_blank_titles_fallback_to_music_fields():
    raw=fixture([dict(video_title='  ',episode_name=None,master_metadata_track_name='Canción',master_metadata_album_artist_name='Artista')])
    d,_=clean_video(raw,'UTC')
    ranking,missing=video_ranking(d)
    assert missing==0 and ranking.iloc[0]['Título']=='Canción'
    assert ranking.iloc[0]['Creador']=='Artista'


def test_video_ranking_visible_in_app(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    upload=BytesIO(fixture([dict(episode_name='Mi video',episode_show_name='Mi programa')]*3))
    upload.name='Streaming_History_Video_2025.json'
    monkeypatch.setattr(st,'file_uploader',lambda *a,**k:[upload] if k.get('key')=='video_uploads' else [])
    app=AppTest.from_file(str(Path(__file__).with_name('app.py')))
    app.session_state["data_source"] = "Subir mis archivos"
    app.run(timeout=20)
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert len(app.get('plotly_chart'))==5
    assert app.dataframe[0].value.iloc[0]['Título']=='Mi video'
    assert app.dataframe[0].value.iloc[0]['Reproducciones']==3
