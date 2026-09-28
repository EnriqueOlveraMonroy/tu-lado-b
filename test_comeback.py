import pandas as pd
from musical_comeback import musical_comebacks


def data(events):
    return pd.DataFrame([dict(ts=pd.Timestamp(date,tz='UTC'),track=title,artist=artist) for date,title,artist in events])


def test_return_window_count_and_exact_boundaries():
    d=data([('2024-01-01','X','A'),('2024-03-31','X','A'),('2024-04-01','X','A'),
            ('2024-04-02','X','A'),('2024-04-30','X','A')])
    r=musical_comebacks(d)
    assert len(r)==1 and r.iloc[0]['gap_days']==90
    assert r.iloc[0]['plays']==3  # April 30 is the exclusive window end.
    assert not r.iloc[0]['partial']


def test_identity_and_minimum_and_incomplete_window():
    d=data([('2024-01-01','X','A'),('2024-04-01','X','B'),('2024-04-02','X','B'),('2024-04-03','X','B')])
    assert musical_comebacks(d).empty  # Not the same artist.
    d['artist']='A'
    r=musical_comebacks(d.iloc[::-1])
    assert len(r)==1 and r.iloc[0]['plays']==3 and r.iloc[0]['partial']
    assert musical_comebacks(d.iloc[:3]).empty  # Only 2 return plays.
    assert musical_comebacks(d.iloc[:0]).empty


def test_an_intermediate_listen_breaks_the_absence():
    d=data([('2024-01-01','X','A'),('2024-02-15','X','A'),('2024-04-01','X','A'),
            ('2024-04-02','X','A'),('2024-04-03','X','A')])
    assert musical_comebacks(d).empty


def test_comeback_view_has_song_and_partial_notice():
    from streamlit.testing.v1 import AppTest
    script='''
import pandas as pd
from musical_comeback import render_comeback
df = pd.DataFrame({'ts': pd.to_datetime(['2024-01-01','2024-04-01','2024-04-02','2024-04-03'],utc=True), 'track':['Mi canción']*4, 'artist':['Mi artista']*4})
render_comeback(df)
'''
    app=AppTest.from_string(script).run(timeout=20)
    assert not app.exception
    assert app.metric[2].value=='3'
    assert any('Mi canción' in m.value for m in app.markdown)
    assert any('parcial' in m.value for m in app.info)
