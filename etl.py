"""
ETL para el historial de streaming de Spotify.
Convierte el JSON crudo en un DataFrame limpio y tipado, listo para métricas.
"""
import json
import pandas as pd
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REQUIRED_COLS = [
    "ts", "platform", "ms_played", "master_metadata_track_name",
    "master_metadata_album_artist_name", "master_metadata_album_album_name",
    "reason_start", "reason_end", "shuffle", "skipped", "offline",
    "incognito_mode",
]


def load_raw(path: str) -> pd.DataFrame:
    """Carga el JSON crudo de Spotify Extended Streaming History."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return df


def clean(df: pd.DataFrame, min_ms_played: int = 5000, timezone: str = "America/Mexico_City") -> pd.DataFrame:
    """
    Limpia y enriquece el DataFrame crudo.

    - Filtra filas sin pista de audio (episodios de podcast / audiobooks)
    - Marca reproducciones "fantasma" (ms_played muy bajo, típico de
      navegación rápida con back/fwd que no representan escucha real)
    - Deriva columnas temporales y de comportamiento
    """
    missing = sorted(set(REQUIRED_COLS) - set(df.columns))
    if missing:
        raise ValueError("Faltan columnas del historial ampliado de Spotify: " + ", ".join(missing))
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Zona horaria no válida: " + timezone) from exc
    df = df.copy()

    # Solo tracks de música (excluye podcasts/audiobooks si los hubiera)
    df = df[df["master_metadata_track_name"].notna()].copy()

    # Tipado temporal
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    if df["ts"].isna().any():
        raise ValueError("El historial contiene fechas vacías o inválidas.")
    df["ts"] = df["ts"].dt.tz_convert(zone)
    df["ms_played"] = pd.to_numeric(df["ms_played"], errors="coerce")
    if (df["ms_played"].isna() | (df["ms_played"] < 0) | df["ms_played"].isin([float("inf"), -float("inf")])).any():
        raise ValueError("El historial contiene duraciones inválidas.")
    df["date"] = df["ts"].dt.date
    df["hour"] = df["ts"].dt.hour
    df["day_of_week"] = df["ts"].dt.day_name()
    df["month"] = df["ts"].dt.tz_localize(None).dt.to_period("M").astype(str)

    # Tiempo de escucha
    df["minutes_played"] = df["ms_played"] / 60000

    # Reproducciones "fantasma": navegación tipo backbtn/fwdbtn con ms_played
    # casi 0. Las marcamos pero no las eliminamos del todo (son señal de
    # comportamiento "impaciente"), solo las excluimos de minutos totales.
    df["is_ghost_play"] = df["ms_played"] < min_ms_played

    # Renombrar para comodidad
    df = df.rename(columns={
        "master_metadata_track_name": "track",
        "master_metadata_album_artist_name": "artist",
        "master_metadata_album_album_name": "album",
    })

    # Slot horario (para arquetipos tipo "night owl")
    def time_slot(h):
        if 5 <= h < 12:
            return "mañana"
        elif 12 <= h < 18:
            return "tarde"
        elif 18 <= h < 23:
            return "noche"
        else:
            return "madrugada"
    df["time_slot"] = df["hour"].apply(time_slot)

    cols = [
        "ts", "date", "hour", "day_of_week", "month", "time_slot",
        "platform", "track", "artist", "album",
        "ms_played", "minutes_played", "is_ghost_play",
        "reason_start", "reason_end", "shuffle", "skipped",
        "offline", "incognito_mode",
    ]
    for column in ["track", "artist", "album", "platform", "reason_start", "reason_end", "month", "day_of_week", "time_slot"]:
        df[column] = df[column].astype("category").astype(object)
    return df[cols].reset_index(drop=True)


def load_clean(path: str, min_ms_played: int = 5000, timezone: str = "America/Mexico_City") -> pd.DataFrame:
    """Pipeline completo: carga + limpieza en un paso."""
    return clean(load_raw(path), min_ms_played=min_ms_played, timezone=timezone)


if __name__ == "__main__":
    df = load_clean("/mnt/project/Streaming_History_Audio_2024.json")
    print(df.shape)
    print(df.head())
    print(df.dtypes)
