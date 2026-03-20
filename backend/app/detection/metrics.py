"""
metrics.py — Calcul des KPIs de qualité réseau

Pour chaque (line_id, stop_id, fenêtre temporelle) on calcule :
- retard moyen et écart absolu moyen
- score de ponctualité
- score de régularité (headway)
- taux de suppression probable
- persistance de la dégradation
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ─── Seuils métier ────────────────────────────────────────────
DELAY_THRESHOLD_SECONDS = 180       # 3 min → passage non conforme
SUPPRESSION_WINDOW_MINUTES = 10     # fenêtre pour détecter un passage manquant
HEADWAY_TOLERANCE = 0.30            # ±30% d'écart au headway théorique acceptable
PEAK_HOURS = [(7, 9), (17, 20)]     # tranches heures de pointe


def is_peak_hour(dt: datetime) -> bool:
    h = dt.hour
    return any(start <= h < end for start, end in PEAK_HOURS)


# ─── Fenêtre temporelle ───────────────────────────────────────
def get_window(minutes: int = 5) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    return now - timedelta(minutes=minutes), now


# ─── Retard moyen sur une fenêtre ────────────────────────────
async def compute_mean_delay(
    session: AsyncSession,
    line_id: str,
    stop_id: Optional[str],
    window_minutes: int = 5,
) -> dict:
    """
    Compare passages observés vs théoriques sur la fenêtre.
    Retourne mean_delay, abs_mean_delay, missing_passages, punctuality_score.
    """
    start, end = get_window(window_minutes)

    # Passages observés sur la fenêtre
    obs_query = text("""
        SELECT observed_time
        FROM observed_passages
        WHERE line_id = :line_id
          AND (CAST(:stop_id AS VARCHAR) IS NULL OR stop_id = CAST(:stop_id AS VARCHAR))
          AND observed_time BETWEEN :start AND :end
        ORDER BY observed_time
    """)

    # Passages théoriques sur la fenêtre
    sched_query = text("""
        SELECT scheduled_time
        FROM scheduled_passages
        WHERE line_id = :line_id
          AND (CAST(:stop_id AS VARCHAR) IS NULL OR stop_id = CAST(:stop_id AS VARCHAR))
          AND scheduled_time BETWEEN :start AND :end
        ORDER BY scheduled_time
    """)

    params = {"line_id": line_id, "stop_id": stop_id, "start": start, "end": end}

    obs_result = await session.execute(obs_query, params)
    sched_result = await session.execute(sched_query, params)

    observed = [r[0] for r in obs_result]
    scheduled = [r[0] for r in sched_result]

    if not scheduled:
        return {
            "mean_delay": None,
            "abs_mean_delay": None,
            "missing_passages": 0,
            "punctuality_score": None,
            "window_minutes": window_minutes,
        }

    # Appariement simple : on matche chaque passage théorique avec le plus proche observé
    delays = []
    matched_obs = set()
    for sched_time in scheduled:
        best_match = None
        best_diff = float("inf")
        for i, obs_time in enumerate(observed):
            if i in matched_obs:
                continue
            diff = abs((obs_time - sched_time).total_seconds())
            if diff < best_diff and diff < 600:  # max 10 min d'écart pour matcher
                best_diff = diff
                best_match = i
        if best_match is not None:
            matched_obs.add(best_match)
            delay = (observed[best_match] - sched_time).total_seconds()
            delays.append(delay)

    n = len(scheduled)
    missing = n - len(delays)
    mean_delay = sum(delays) / len(delays) if delays else 0.0
    abs_mean_delay = sum(abs(d) for d in delays) / len(delays) if delays else 0.0

    # Ponctualité = % passages dans le seuil
    on_time = sum(1 for d in delays if abs(d) <= DELAY_THRESHOLD_SECONDS)
    punctuality_score = on_time / n if n > 0 else 1.0

    return {
        "mean_delay": mean_delay,
        "abs_mean_delay": abs_mean_delay,
        "missing_passages": missing,
        "punctuality_score": round(punctuality_score, 3),
        "window_minutes": window_minutes,
        "n_scheduled": n,
        "n_observed": len(observed),
    }


# ─── Régularité (headway) ─────────────────────────────────────
async def compute_regularity(
    session: AsyncSession,
    line_id: str,
    stop_id: Optional[str],
    window_minutes: int = 10,
) -> dict:
    """
    Calcule l'écart entre le headway observé et le headway théorique.
    Retourne regularity_score et headway_gap.
    """
    start, end = get_window(window_minutes)

    obs_query = text("""
        SELECT observed_time
        FROM observed_passages
        WHERE line_id = :line_id
          AND (CAST(:stop_id AS VARCHAR) IS NULL OR stop_id = CAST(:stop_id AS VARCHAR))
          AND observed_time BETWEEN :start AND :end
        ORDER BY observed_time
    """)

    sched_query = text("""
        SELECT scheduled_time
        FROM scheduled_passages
        WHERE line_id = :line_id
          AND (CAST(:stop_id AS VARCHAR) IS NULL OR stop_id = CAST(:stop_id AS VARCHAR))
          AND scheduled_time BETWEEN :start AND :end
        ORDER BY scheduled_time
    """)

    params = {"line_id": line_id, "stop_id": stop_id, "start": start, "end": end}
    obs_result = await session.execute(obs_query, params)
    sched_result = await session.execute(sched_query, params)

    observed = sorted([r[0] for r in obs_result])
    scheduled = sorted([r[0] for r in sched_result])

    def headway_list(times):
        if len(times) < 2:
            return []
        return [(times[i+1] - times[i]).total_seconds() for i in range(len(times)-1)]

    obs_headways = headway_list(observed)
    sched_headways = headway_list(scheduled)

    if not sched_headways:
        return {
            "regularity_score": None,
            "headway_gap": None,
            "observed_headway_mean": None,
            "theoretical_headway_mean": None,
        }

    theoretical_hw = sum(sched_headways) / len(sched_headways)
    observed_hw = sum(obs_headways) / len(obs_headways) if obs_headways else theoretical_hw

    # Régularité = 1 - |headway_réel - headway_théo| / headway_théo
    headway_gap = abs(observed_hw - theoretical_hw)
    regularity_score = max(0.0, 1.0 - headway_gap / theoretical_hw) if theoretical_hw > 0 else 1.0

    return {
        "regularity_score": round(regularity_score, 3),
        "headway_gap": round(headway_gap, 1),
        "observed_headway_mean": round(observed_hw, 1),
        "theoretical_headway_mean": round(theoretical_hw, 1),
    }


# ─── Persistance de la dégradation ───────────────────────────
async def compute_persistence(
    session: AsyncSession,
    line_id: str,
    stop_id: Optional[str],
    window_minutes: int = 15,
    threshold_score: float = 50.0,
) -> float:
    """
    Mesure si la dégradation persiste dans le temps.
    Regarde les network_metrics récentes et calcule
    le ratio de fenêtres en état dégradé.
    """
    start = datetime.utcnow() - timedelta(minutes=window_minutes)

    query = text("""
        SELECT anomaly_score
        FROM network_metrics
        WHERE line_id = :line_id
          AND (CAST(:stop_id AS VARCHAR) IS NULL OR stop_id = CAST(:stop_id AS VARCHAR))
          AND computed_at >= :start
        ORDER BY computed_at DESC
        LIMIT 10
    """)

    result = await session.execute(query, {
        "line_id": line_id,
        "stop_id": stop_id,
        "start": start,
    })

    scores = [r[0] for r in result if r[0] is not None]
    if not scores:
        return 0.0

    degraded = sum(1 for s in scores if s >= threshold_score)
    return round(degraded / len(scores), 3)


# ─── Propagation spatiale ─────────────────────────────────────
async def compute_spatial_propagation(
    session: AsyncSession,
    line_id: str,
    window_minutes: int = 10,
) -> int:
    """
    Compte le nombre de stations voisines sur la même ligne
    qui ont aussi un score d'anomalie élevé récemment.
    """
    start = datetime.utcnow() - timedelta(minutes=window_minutes)

    query = text("""
        SELECT COUNT(DISTINCT stop_id)
        FROM network_metrics
        WHERE line_id = :line_id
          AND anomaly_score >= 50
          AND computed_at >= :start
    """)

    result = await session.execute(query, {"line_id": line_id, "start": start})
    row = result.fetchone()
    return int(row[0]) if row else 0


# ─── Incident officiel actif ──────────────────────────────────
async def has_official_incident(
    session: AsyncSession,
    line_id: str,
) -> bool:
    """Vérifie si un incident officiel est actif sur cette ligne."""
    now = datetime.utcnow()
    query = text("""
        SELECT COUNT(*)
        FROM official_incidents
        WHERE line_id = :line_id
          AND start_time <= :now
          AND (end_time IS NULL OR end_time >= :now)
    """)
    result = await session.execute(query, {"line_id": line_id, "now": now})
    row = result.fetchone()
    return int(row[0]) > 0 if row else False
