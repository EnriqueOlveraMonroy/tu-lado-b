import pandas as pd
import pytest
from etl import clean
from test_metrics import _fake_row
from rich_charts import daily_data, listening_calendar, listening_trend, hourly_profile, artist_year_map, top_tracks, discovery_curve
from viz import hourly_heatmap


def data():
    return clean(pd.DataFrame([
        _fake_row('2024-01-01T12:00:00Z','Same','A',ms=180000),
        _fake_row('2024-01-03T12:00:00Z','Same','B',ms=1000),
        _fake_row('2025-01-01T12:00:00Z','Same','A',ms=60000),
    ]),timezone='UTC')


def test_daily_totals_gaps_and_average():
    d=daily_data(data(),2024)
    assert d['minutes'].tolist()==[3,0,0]
    assert d['average'].tolist()==[3,1.5,1]
    assert daily_data(data(),2023).empty


def test_hourly_axes_and_unknown_skips():
    d=data(); d['skipped']=None
    f=hourly_profile(d)
    assert len(f.data[0].x)==24
    assert sum(f.data[0].y)==3
    assert all(pd.isna(v) for v in f.data[1].y)
    assert len(hourly_heatmap(d).data[0].x)==24


def test_artist_shares_and_song_identity():
    f=artist_year_map(data())
    assert f.data[0].z.sum(axis=0).tolist()==[100,100]
    f=top_tracks(data())
    assert len(f.data[0].y)==2
    assert sum(f.data[0].x)==3


@pytest.mark.parametrize('fn',[lambda d:listening_calendar(d,2024),lambda d:listening_trend(d,2024),hourly_profile,artist_year_map,top_tracks,discovery_curve])
def test_figures_serialize_with_one_record(fn):
    fig=fn(data().iloc[:1])
    assert fig.to_json()
    assert fig.layout.height>=340
