"""
Cálculo de KPIs de comportamiento sobre el DataFrame limpio.
Todas las funciones son puras: reciben un DataFrame y devuelven
un valor o una Serie, sin efectos secundarios.
"""
import numpy as np
import pandas as pd


def skip_rate(df: pd.DataFrame) -> float:
    return df["skipped"].mean()


def skip_rate_by_hour(df: pd.DataFrame) -> pd.Series:
    return df.groupby("hour")["skipped"].mean()


def artist_entropy(df: pd.DataFrame) -> float:
    """
    Entropía de Shannon normalizada (0-1) sobre la distribución de artistas.
    0 = escucha siempre al/a los mismos artistas (loop).
    1 = máxima diversidad, cada reproducción es de un artista distinto.
    """
    counts = df["artist"].value_counts()
    probs = counts / counts.sum()
    entropy = -(probs * np.log2(probs)).sum()
    max_entropy = np.log2(len(counts)) if len(counts) > 1 else 1
    return entropy / max_entropy if max_entropy > 0 else 0.0


def shuffle_pct(df: pd.DataFrame) -> float:
    return df["shuffle"].mean()


def offline_pct(df: pd.DataFrame) -> float:
    return df["offline"].mean()


def incognito_pct(df: pd.DataFrame) -> float:
    return df["incognito_mode"].mean()


def ghost_play_pct(df: pd.DataFrame) -> float:
    """% de reproducciones fugaces (<5s), señal de navegación impaciente."""
    return df["is_ghost_play"].mean()


def time_slot_distribution(df: pd.DataFrame) -> pd.Series:
    return df["time_slot"].value_counts(normalize=True)


def dominant_time_slot(df: pd.DataFrame) -> str:
    return time_slot_distribution(df).idxmax()


def repeat_streaks(df: pd.DataFrame) -> pd.Series:
    """
    Longitud de rachas consecutivas del mismo track (ordenado por tiempo).
    Devuelve la serie de longitudes de racha (una por racha detectada).
    """
    d = df.sort_values("ts").reset_index(drop=True)
    same_as_prev = d[["track", "artist"]].eq(d[["track", "artist"]].shift()).all(axis=1)
    streak_id = (~same_as_prev).cumsum()
    return d.groupby(streak_id).size()


def avg_repeat_streak(df: pd.DataFrame) -> float:
    streaks = repeat_streaks(df)
    return streaks.mean()


def max_repeat_streak(df: pd.DataFrame) -> int:
    streaks = repeat_streaks(df)
    return int(streaks.max())


def top_artists(df: pd.DataFrame, n: int = 10) -> pd.Series:
    return df["artist"].value_counts().head(n)


def top_artist_concentration(df: pd.DataFrame) -> float:
    """% de reproducciones que pertenecen al artista más escuchado.
    Alta concentración = 'leal a un artista' aunque salte entre canciones."""
    counts = df["artist"].value_counts()
    return counts.iloc[0] / counts.sum() if len(counts) > 0 else 0.0


def artist_repeat_streaks(df: pd.DataFrame) -> pd.Series:
    """Rachas consecutivas del mismo ARTISTA (no track). Mide maratones."""
    d = df.sort_values("ts").reset_index(drop=True)
    same_as_prev = d["artist"] == d["artist"].shift()
    streak_id = (~same_as_prev).cumsum()
    return d.groupby(streak_id).size()


def max_artist_streak(df: pd.DataFrame) -> int:
    return int(artist_repeat_streaks(df).max())


def total_minutes(df: pd.DataFrame) -> float:
    return df.loc[~df["is_ghost_play"], "minutes_played"].sum()


def reason_end_distribution(df: pd.DataFrame) -> pd.Series:
    return df["reason_end"].value_counts(normalize=True)


def weekday_vs_weekend_minutes(df: pd.DataFrame) -> dict:
    weekend_days = {"Saturday", "Sunday"}
    is_weekend = df["day_of_week"].isin(weekend_days)
    return {
        "weekday_avg_min": df.loc[~is_weekend, "minutes_played"].sum(),
        "weekend_avg_min": df.loc[is_weekend, "minutes_played"].sum(),
    }


def compute_all_metrics(df: pd.DataFrame) -> dict:
    """Calcula el set completo de KPIs y devuelve un dict plano."""
    return {
        "n_plays": len(df),
        "total_minutes": round(total_minutes(df), 1),
        "unique_artists": df["artist"].nunique(),
        "unique_tracks": len(df[["track", "artist"]].drop_duplicates()),
        "skip_rate": round(skip_rate(df), 3),
        "artist_entropy": round(artist_entropy(df), 3),
        "shuffle_pct": round(shuffle_pct(df), 3),
        "offline_pct": round(offline_pct(df), 3),
        "incognito_pct": round(incognito_pct(df), 3),
        "ghost_play_pct": round(ghost_play_pct(df), 3),
        "dominant_time_slot": dominant_time_slot(df),
        "time_slot_distribution": time_slot_distribution(df).round(3).to_dict(),
        "avg_repeat_streak": round(avg_repeat_streak(df), 2),
        "max_repeat_streak": max_repeat_streak(df),
        "top_artist_concentration": round(top_artist_concentration(df), 3),
        "max_artist_streak": max_artist_streak(df),
        "top_artists": top_artists(df, 5).to_dict(),
    }


if __name__ == "__main__":
    from etl import load_clean
    df = load_clean("/mnt/project/Streaming_History_Audio_2024.json")
    import json as _json
    print(_json.dumps(compute_all_metrics(df), indent=2, ensure_ascii=False))
