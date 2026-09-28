"""
Motor de arquetipos de personalidad musical.

Enfoque: cada arquetipo se define como un conjunto de "señales" (funciones
que devuelven un score 0-1 a partir de las métricas ya calculadas). El
arquetipo final es el de mayor score promedio ponderado. Este diseño es
transparente y auditable: se puede imprimir el desglose de por qué un
usuario recibió determinado arquetipo, en vez de una caja negra.
"""
import numpy as np
from archetype_lore import LORE, description


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _ramp(x: float, low: float, high: float) -> float:
    """Score 0-1: 0 por debajo de `low`, 1 por encima de `high`, lineal entre medio."""
    if high == low:
        return 1.0 if x >= high else 0.0
    return _clip01((x - low) / (high - low))


def _inverse_ramp(x: float, low: float, high: float) -> float:
    return 1.0 - _ramp(x, low, high)


# Cada arquetipo: nombre -> (descripción, dict de señal -> (peso, función(metrics)->score))
def _signals_fiel_de_culto(m: dict) -> dict:
    return {
        "concentración de artista": (0.4, _ramp(m["top_artist_concentration"], 0.15, 0.5)),
        "racha larga del mismo artista": (0.35, _ramp(m["max_artist_streak"] / max(m["n_plays"], 1), 0.05, 0.2)),
        "baja diversidad": (0.25, _inverse_ramp(m["artist_entropy"], 0.5, 0.85)),
    }


def _signals_explorador_impaciente(m: dict) -> dict:
    return {
        "porcentaje de saltos alta": (0.5, _ramp(m["skip_rate"], 0.15, 0.45)),
        "reproducciones fugaces": (0.3, _ramp(m["ghost_play_pct"], 0.05, 0.25)),
        "alta diversidad de artistas": (0.2, _ramp(m["artist_entropy"], 0.5, 0.85)),
    }


def _signals_arquitecto_madrugada(m: dict) -> dict:
    dist = m["time_slot_distribution"]
    madrugada = dist.get("madrugada", 0.0)
    noche = dist.get("noche", 0.0)
    return {
        "% escucha en madrugada": (0.6, _ramp(madrugada, 0.15, 0.4)),
        "% escucha nocturna": (0.4, _ramp(noche, 0.15, 0.35)),
    }


def _signals_coleccionista_eclectico(m: dict) -> dict:
    return {
        "alta entropía de artista": (0.5, _ramp(m["artist_entropy"], 0.6, 0.9)),
        "baja concentración en un artista": (0.3, _inverse_ramp(m["top_artist_concentration"], 0.15, 0.4)),
        "muchos artistas únicos": (0.2, _ramp(m["unique_artists"] / max(m["n_plays"], 1), 0.15, 0.5)),
    }


def _signals_ritualista_sereno(m: dict) -> dict:
    return {
        "porcentaje de saltos bajo": (0.4, _inverse_ramp(m["skip_rate"], 0.1, 0.3)),
        "pocas reproducciones fugaces": (0.3, _inverse_ramp(m["ghost_play_pct"], 0.05, 0.2)),
        "reproducción aleatoria desactivada": (0.3, 1.0 - m["shuffle_pct"]),
    }


ARCHETYPES = {
    "El Fiel de Culto": {
        "signals_fn": _signals_fiel_de_culto,
        "descripcion": (
            "No repites la misma canción en repetición, pero cuando un artista te "
            "atrapa, te quedas horas ahí. Maratones largas de un solo artista, "
            "saltando entre sus canciones, son tu forma de fidelidad."
        ),
    },
    "El Explorador Impaciente": {
        "signals_fn": _signals_explorador_impaciente,
        "descripcion": (
            "Saltas rápido si algo no te convence en los primeros segundos. "
            "Tu biblioteca es amplia porque siempre estás probando, no porque "
            "te quedes con lo primero que suena."
        ),
    },
    "El Arquitecto de la Madrugada": {
        "signals_fn": _signals_arquitecto_madrugada,
        "descripcion": (
            "Tu música vive de noche. Una porción importante de tu escucha "
            "ocurre después de medianoche — la madrugada es tu estudio, tu "
            "auto o tu momento de desconexión real."
        ),
    },
    "El Coleccionista Ecléctico": {
        "signals_fn": _signals_coleccionista_eclectico,
        "descripcion": (
            "Tu historial no tiene un centro de gravedad claro: pasas de "
            "género en género y de artista en artista sin que ninguno domine. "
            "La curiosidad manda sobre la fidelidad."
        ),
    },
    "El Ritualista Sereno": {
        "signals_fn": _signals_ritualista_sereno,
        "descripcion": (
            "Escuchas con calma, casi sin saltar canciones y sin reproducción aleatoria: "
            "eliges lo que vas a escuchar y lo dejas correr. La música es "
            "un ritual, no un ruido de fondo que se ajusta al azar."
        ),
    },
}


for _name in ARCHETYPES:
    ARCHETYPES[_name]["descripcion"] = description(_name)


def score_archetype(name: str, metrics: dict) -> dict:
    signals = ARCHETYPES[name]["signals_fn"](metrics)
    total_weight = sum(w for w, _ in signals.values())
    weighted_score = sum(w * s for w, s in signals.values()) / total_weight
    return {
        "score": round(weighted_score, 3),
        "signals": {k: round(s, 3) for k, (w, s) in signals.items()},
    }


def classify(metrics: dict) -> dict:
    """Devuelve el arquetipo dominante + el desglose completo de todos."""
    breakdown = {name: score_archetype(name, metrics) for name in ARCHETYPES}
    winner = max(breakdown, key=lambda k: breakdown[k]["score"])
    return {
        "arquetipo": winner,
        "descripcion": ARCHETYPES[winner]["descripcion"],
        "score": breakdown[winner]["score"],
        "por_que": breakdown[winner]["signals"],
        "todos_los_scores": {k: v["score"] for k, v in breakdown.items()},
    }


if __name__ == "__main__":
    from etl import load_clean
    from metrics import compute_all_metrics
    import json

    df = load_clean("/mnt/project/Streaming_History_Audio_2024.json")
    m = compute_all_metrics(df)
    result = classify(m)
    print(json.dumps(result, indent=2, ensure_ascii=False))
