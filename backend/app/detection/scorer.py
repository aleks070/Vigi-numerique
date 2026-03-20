"""
scorer.py — Score d'anomalie composite et inférence de l'état réseau

Formule du document technique :
anomaly_score = 0.35·D + 0.25·M + 0.20·H + 0.10·P + 0.10·S

où :
  D = score de retard normalisé        (35%)
  M = score de passages manquants      (25%)
  H = score d'irrégularité de headway  (20%)
  P = score de persistance             (10%)
  S = score de propagation spatiale    (10%)

États réseau dérivés du score :
  0–25   → nominal
  26–50  → sous_surveillance
  51–75  → degrade
  76–90  → perturbe
  91–100 → incident_majeur
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Pondérations ─────────────────────────────────────────────
WEIGHTS = {
    "delay":       0.35,
    "missing":     0.25,
    "headway":     0.20,
    "persistence": 0.10,
    "spatial":     0.10,
}

# ─── Seuils de normalisation ──────────────────────────────────
MAX_DELAY_SECONDS   = 600.0   # 10 min → score retard = 100
MAX_MISSING         = 5       # 5 passages manquants → score = 100
MAX_HEADWAY_GAP     = 300.0   # 5 min d'écart headway → score = 100
MAX_NEIGHBOR_COUNT  = 5       # 5 stations voisines dégradées → score = 100

# ─── Seuils états réseau ──────────────────────────────────────
STATE_THRESHOLDS = [
    (91, "incident_majeur"),
    (76, "perturbe"),
    (51, "degrade"),
    (26, "sous_surveillance"),
    (0,  "nominal"),
]

# ─── Règles métier ────────────────────────────────────────────
RULES = {
    "mean_delay_degrade":      180.0,   # > 3 min sur 3 fenêtres → dégradé
    "missing_suppression":     1,       # >= 1 passage manquant → suppression probable
    "headway_gap_irregularite": 120.0,  # > 2 min d'écart headway → irrégularité
}


def normalize(value: float, max_value: float) -> float:
    """Normalise une valeur entre 0 et 100."""
    if value is None or max_value <= 0:
        return 0.0
    return min(100.0, (value / max_value) * 100.0)


def compute_anomaly_score(
    mean_delay: Optional[float],
    abs_mean_delay: Optional[float],
    missing_passages: int,
    regularity_score: Optional[float],
    headway_gap: Optional[float],
    persistence: float,
    neighbor_anomaly_count: int,
    official_incident: bool = False,
) -> dict:
    """
    Calcule le score d'anomalie composite [0-100] et dérive l'état réseau.
    Retourne le score, l'état, les composantes et la justification.
    """

    # ── Composante D : retard ──────────────────────────────────
    delay_val = abs(mean_delay) if mean_delay is not None else 0.0
    D = normalize(delay_val, MAX_DELAY_SECONDS)

    # ── Composante M : passages manquants ─────────────────────
    M = normalize(missing_passages, MAX_MISSING)

    # ── Composante H : irrégularité headway ───────────────────
    if regularity_score is not None:
        H = (1.0 - regularity_score) * 100.0
    elif headway_gap is not None:
        H = normalize(headway_gap, MAX_HEADWAY_GAP)
    else:
        H = 0.0

    # ── Composante P : persistance ────────────────────────────
    P = persistence * 100.0

    # ── Composante S : propagation spatiale ───────────────────
    S = normalize(neighbor_anomaly_count, MAX_NEIGHBOR_COUNT)

    # ── Score composite ───────────────────────────────────────
    score = (
        WEIGHTS["delay"]       * D +
        WEIGHTS["missing"]     * M +
        WEIGHTS["headway"]     * H +
        WEIGHTS["persistence"] * P +
        WEIGHTS["spatial"]     * S
    )
    score = round(min(100.0, max(0.0, score)), 1)

    # ── Bonus incident officiel ───────────────────────────────
    # Si un incident officiel est actif, on monte le score minimum à 40
    if official_incident and score < 40:
        score = 40.0

    # ── État réseau ───────────────────────────────────────────
    network_state = "nominal"
    for threshold, state in STATE_THRESHOLDS:
        if score >= threshold:
            network_state = state
            break

    # ── Règles métier → type d'événement ─────────────────────
    event_type, severity = infer_event_type(
        mean_delay=mean_delay,
        missing_passages=missing_passages,
        headway_gap=headway_gap,
        official_incident=official_incident,
        neighbor_anomaly_count=neighbor_anomaly_count,
        score=score,
    )

    # ── Justification lisible ─────────────────────────────────
    justification = build_justification(
        mean_delay=mean_delay,
        missing_passages=missing_passages,
        headway_gap=headway_gap,
        persistence=persistence,
        neighbor_anomaly_count=neighbor_anomaly_count,
        official_incident=official_incident,
    )

    return {
        "anomaly_score": score,
        "network_state": network_state,
        "event_type": event_type,
        "severity": severity,
        "justification": justification,
        "components": {
            "D_retard":      round(D, 1),
            "M_manquants":   round(M, 1),
            "H_headway":     round(H, 1),
            "P_persistance": round(P, 1),
            "S_spatial":     round(S, 1),
        },
    }


def infer_event_type(
    mean_delay: Optional[float],
    missing_passages: int,
    headway_gap: Optional[float],
    official_incident: bool,
    neighbor_anomaly_count: int,
    score: float,
) -> tuple[str, str]:
    """
    Détermine le type d'événement et la sévérité selon les règles métier.
    Retourne (event_type, severity).
    """

    # Règle 1 : suppression probable
    if missing_passages >= RULES["missing_suppression"]:
        if mean_delay is not None and mean_delay > RULES["mean_delay_degrade"]:
            return "suppression_probable", _severity(score)

    # Règle 2 : propagation spatiale
    if neighbor_anomaly_count >= 2:
        return "propagation", _severity(score)

    # Règle 3 : dérive non déclarée (anomalie sans incident officiel)
    if score >= 51 and not official_incident:
        return "derive_non_declaree", _severity(score)

    # Règle 4 : retard anormal
    if mean_delay is not None and mean_delay > RULES["mean_delay_degrade"]:
        return "retard", _severity(score)

    # Règle 5 : irrégularité de fréquence
    if headway_gap is not None and headway_gap > RULES["headway_gap_irregularite"]:
        return "irregularite", _severity(score)

    # Règle 6 : incident déclaré
    if official_incident:
        return "incident_officiel", _severity(score)

    return "anomalie_generique", _severity(score)


def _severity(score: float) -> str:
    if score >= 76:
        return "critique"
    if score >= 51:
        return "fort"
    if score >= 26:
        return "moyen"
    return "faible"


def build_justification(
    mean_delay: Optional[float],
    missing_passages: int,
    headway_gap: Optional[float],
    persistence: float,
    neighbor_anomaly_count: int,
    official_incident: bool,
) -> str:
    """Construit une description lisible pour les agents."""
    parts = []

    if mean_delay is not None and abs(mean_delay) > 60:
        sign = "avance" if mean_delay < 0 else "retard"
        parts.append(f"Retard moyen {abs(mean_delay)/60:.1f} min ({sign})")

    if missing_passages > 0:
        parts.append(f"{missing_passages} passage(s) théorique(s) absent(s)")

    if headway_gap is not None and headway_gap > 60:
        parts.append(f"Écart headway {headway_gap/60:.1f} min vs théorique")

    if persistence > 0.5:
        parts.append(f"Dégradation persistante ({int(persistence*100)}% des fenêtres récentes)")

    if neighbor_anomaly_count > 0:
        parts.append(f"{neighbor_anomaly_count} station(s) voisine(s) également dégradée(s)")

    if official_incident:
        parts.append("Incident officiel actif sur cette ligne")

    if not parts:
        return "Anomalie détectée par score composite"

    return " — ".join(parts)


def compute_line_score(
    punctuality: float,
    regularity: float,
    suppression_rate: float,
    incident_severity: float = 0.0,
) -> float:
    """
    Score composite par ligne (pour le dashboard global).
    score = 0.40·ponctualité + 0.30·régularité + 0.20·(1-suppression) + 0.10·(1-gravité incidents)
    """
    score = (
        0.40 * punctuality +
        0.30 * regularity +
        0.20 * (1.0 - suppression_rate) +
        0.10 * (1.0 - incident_severity)
    )
    return round(max(0.0, min(100.0, score * 100)), 1)
