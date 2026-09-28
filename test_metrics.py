"""
Tests sobre datos sintéticos (no dependen del archivo real del usuario),
para que el pipeline sea verificable en cualquier entorno.
"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from etl import clean  # noqa: E402
from metrics import (  # noqa: E402
    skip_rate, artist_entropy, top_artist_concentration,
    max_artist_streak, shuffle_pct,
)
from archetypes import classify  # noqa: E402


def _fake_row(ts, track, artist, ms=180000, skipped=False, shuffle=False):
    return {
        "ts": ts, "platform": "test", "ms_played": ms,
        "master_metadata_track_name": track,
        "master_metadata_album_artist_name": artist,
        "master_metadata_album_album_name": "Album",
        "reason_start": "trackdone", "reason_end": "trackdone",
        "shuffle": shuffle, "skipped": skipped, "offline": False,
        "incognito_mode": False,
    }


def make_loyalist_df() -> pd.DataFrame:
    """20 reproducciones seguidas del mismo artista, sin skips, sin shuffle."""
    rows = [
        _fake_row(f"2024-01-01T{h:02d}:00:00Z", f"Track {i}", "Same Artist")
        for i, h in enumerate(range(20))
    ]
    return clean(pd.DataFrame(rows))


def make_explorer_df() -> pd.DataFrame:
    """20 reproducciones de artistas distintos, con alta tasa de skip."""
    rows = [
        _fake_row(
            f"2024-01-01T{h:02d}:00:00Z", f"Track {i}", f"Artist {i}",
            ms=8000, skipped=True,
        )
        for i, h in enumerate(range(20))
    ]
    return clean(pd.DataFrame(rows))


def test_skip_rate_bounds():
    df = make_explorer_df()
    assert skip_rate(df) == 1.0


def test_loyalist_has_high_artist_concentration():
    df = make_loyalist_df()
    assert top_artist_concentration(df) == 1.0
    assert max_artist_streak(df) == 20


def test_explorer_has_high_entropy():
    df = make_explorer_df()
    assert artist_entropy(df) > 0.9  # cada reproducción es de un artista distinto


def test_shuffle_pct_zero_when_disabled():
    df = make_loyalist_df()
    assert shuffle_pct(df) == 0.0


def test_classify_returns_valid_archetype():
    df = make_loyalist_df()
    from metrics import compute_all_metrics
    result = classify(compute_all_metrics(df))
    assert result["arquetipo"] in [
        "El Fiel de Culto", "El Explorador Impaciente",
        "El Arquitecto de la Madrugada", "El Coleccionista Ecléctico",
        "El Ritualista Sereno",
    ]
    assert 0 <= result["score"] <= 1


def test_classify_loyalist_scores_high_on_fiel_de_culto():
    df = make_loyalist_df()
    from metrics import compute_all_metrics
    result = classify(compute_all_metrics(df))
    assert result["todos_los_scores"]["El Fiel de Culto"] > 0.7





def test_local_timezone_crosses_day_and_month():
    row = _fake_row("2024-02-01T02:00:00Z", "Song", "Artist")
    df = clean(pd.DataFrame([row]), timezone="America/Mexico_City")
    assert df.iloc[0]["hour"] == 20
    assert df.iloc[0]["month"] == "2024-01"
    assert df.iloc[0]["time_slot"] == "noche"
    assert clean(pd.DataFrame([row]), timezone="UTC").iloc[0]["hour"] == 2


def test_same_title_different_artist_is_not_repeat():
    from metrics import compute_all_metrics
    rows = [_fake_row("2024-01-01T12:00:00Z", "Song", "A"),
            _fake_row("2024-01-01T13:00:00Z", "Song", "B")]
    m = compute_all_metrics(clean(pd.DataFrame(rows)))
    assert m["unique_tracks"] == 2
    assert m["max_repeat_streak"] == 1


def test_monthly_minutes_exclude_ghost_plays():
    from metrics import total_minutes
    from viz import monthly_minutes_line
    rows = [_fake_row("2024-01-01T12:00:00Z", "Song", "A"),
            _fake_row("2024-01-01T13:00:00Z", "Other", "A", ms=1000)]
    df = clean(pd.DataFrame(rows))
    assert sum(monthly_minutes_line(df).data[0].y) == total_minutes(df) == 3


def test_missing_columns_and_invalid_values_have_clear_errors():
    import pytest
    with pytest.raises(ValueError, match="Faltan columnas"):
        clean(pd.DataFrame([{"ts": "2024-01-01"}]))
    for field, value, message in [("ts", "bad-date", "fechas"),
                                   ("ms_played", -1, "duraciones")]:
        row = _fake_row("2024-01-01T12:00:00Z", "Song", "A")
        row[field] = value
        with pytest.raises(ValueError, match=message):
            clean(pd.DataFrame([row]))


def test_upload_validation_and_timezone_cache():
    import json
    import pytest
    from app import process_upload
    for content, message in [(b"[]", "vacío"), (b"{}", "lista"),
                             (b"not json", "JSON"), (b"[1]", "lista"),
                             (b"[{}]", "Faltan columnas")]:
        with pytest.raises(ValueError, match=message):
            process_upload(content, "UTC")
    content = json.dumps([_fake_row("2024-02-01T02:00:00Z", "Song", "A")]).encode()
    assert process_upload(content, "UTC").iloc[0]["hour"] == 2
    assert process_upload(content, "America/Mexico_City").iloc[0]["hour"] == 20


def test_app_starts_with_timezone_selector():
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")))
    app.session_state["data_source"] = "Subir mis archivos"
    app.run(timeout=20)
    assert not app.exception
    assert app.selectbox[0].value == "America/Mexico_City"


def test_multiple_uploads_combine_years_parts_and_sort():
    import json
    from app import process_uploads
    from metrics import compute_all_metrics
    rows = [_fake_row("2025-01-01T12:00:00Z", "One", "A"),
            _fake_row("2024-01-01T12:00:00Z", "Two", "B"),
            _fake_row("2025-02-01T12:00:00Z", "Three", "A")]
    files = [(name, json.dumps([row]).encode()) for name, row in zip(
        ["Streaming_History_Audio_2025.json", "Streaming_History_Audio_2024.json",
         "Streaming_History_Audio_2025_1.json"], rows)]
    df, accepted, warnings = process_uploads(files, "UTC")
    assert len(accepted) == 3 and not warnings
    assert df["ts"].is_monotonic_increasing
    assert df["track"].tolist() == ["Two", "One", "Three"]
    metrics = compute_all_metrics(df)
    assert metrics["n_plays"] == 3 and metrics["total_minutes"] == 9


def test_multiple_uploads_skip_invalid_video_and_duplicate_files():
    import json
    from app import process_uploads
    row = _fake_row("2024-01-01T12:00:00Z", "One", "A")
    content = json.dumps([row, row]).encode()
    podcast = dict(row, master_metadata_track_name=None)
    df, accepted, warnings = process_uploads([
        ("valid.json", content), ("copy.json", content),
        ("broken.json", b"invalid"), ("empty.json", b"[]"),
        ("Streaming_History_Video_2025.json", b"[]"),
        ("podcast.json", json.dumps([podcast]).encode()),
    ], "UTC")
    assert accepted == ["valid.json"] and len(df) == 2
    assert len(warnings) == 5
    for name in ["copy.json", "broken.json", "empty.json", "Streaming_History_Video_2025.json", "podcast.json"]:
        assert any(name in warning for warning in warnings)
    empty, accepted, warnings = process_uploads([("bad.json", b"{}")], "UTC")
    assert empty.empty and not accepted and len(warnings) == 1


def test_multiple_uploads_render_combined_dashboard(monkeypatch):
    import json
    import streamlit as st
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from io import BytesIO
    files = []
    for year in [2024, 2025]:
        file = BytesIO(json.dumps([_fake_row(f"{year}-01-01T12:00:00Z", "Song", "A")]).encode())
        file.name = f"Streaming_History_Audio_{year}.json"
        files.append(file)
    def uploader(*args, **kwargs):
        assert kwargs["accept_multiple_files"] is True
        return files
    monkeypatch.setattr(st, "file_uploader", uploader)
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")))
    app.session_state["data_source"] = "Subir mis archivos"
    app.run(timeout=20)
    assert not app.exception
    assert "2 de 2 archivos incluidos" in app.success[0].value
    assert app.metric[0].value == "2"


if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], check=True)
