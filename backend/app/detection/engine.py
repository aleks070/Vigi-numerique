"""
engine.py — Orchestrateur du moteur de détection

Appelé à chaque cycle du scheduler (toutes les 60s).
Pour chaque ligne active :
  1. Calcule les métriques (metrics.py)
  2. Calcule le score d'anomalie (scorer.py)
  3. Sauvegarde dans network_metrics
  4. Génère un événement si score >= seuil
  5. Gère l'historique 24h (supprime les vieux événements)
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.detection.metrics import (
    compute_mean_delay,
    compute_regularity,
    compute_persistence,
    compute_spatial_propagation,
    has_official_incident,
    is_peak_hour,
)
from app.detection.scorer import compute_anomaly_score, compute_line_score

logger = logging.getLogger(__name__)

# ─── Seuils de génération d'événements ───────────────────────
MIN_SCORE_FOR_EVENT = 26.0      # score minimum pour créer un événement
DEDUP_WINDOW_MINUTES = 10       # pas de doublon sur la même ligne/stop dans cette fenêtre
HISTORY_HOURS = 24              # conservation des événements sur 24h


def _get_session():
    engine = create_async_engine(
        settings.POSTGRES_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return Session()


# ─── Point d'entrée principal ─────────────────────────────────
async def run_detection_cycle():
    """Lance un cycle complet de détection pour toutes les lignes actives."""
    logger.info("── Moteur de détection démarré ──")
    start_time = datetime.utcnow()

    async with _get_session() as session:
        # 1. Récupérer toutes les lignes actives
        lines_result = await session.execute(
            text("SELECT line_id, line_name FROM lines WHERE is_active = TRUE")
        )
        lines = lines_result.fetchall()
        logger.info(f"Analyse de {len(lines)} ligne(s)")

        events_generated = 0

        for line_id, line_name in lines:
            try:
                count = await _process_line(session, line_id, line_name)
                events_generated += count
            except Exception as e:
                logger.error(f"Erreur sur ligne {line_id}: {e}")
                await session.rollback()

        # 2. Nettoyage historique 24h
        await _cleanup_old_events(session)
        await session.commit()

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"── Détection terminée — {events_generated} événement(s) généré(s) en {elapsed:.1f}s ──")
    return events_generated


# ─── Traitement d'une ligne ───────────────────────────────────
async def _process_line(
    session: AsyncSession,
    line_id: str,
    line_name: str,
) -> int:
    """Analyse une ligne et génère les événements si nécessaire."""

    # Récupérer les stops de cette ligne
    stops_result = await session.execute(
        text("""
            SELECT DISTINCT stop_id FROM observed_passages
            WHERE line_id = :line_id
              AND observed_time >= NOW() - INTERVAL '1 hour'
            UNION
            SELECT DISTINCT stop_id FROM scheduled_passages
            WHERE line_id = :line_id
              AND scheduled_time >= NOW() - INTERVAL '1 hour'
            LIMIT 20
        """),
        {"line_id": line_id}
    )
    stops = [r[0] for r in stops_result]

    # Si pas de données granulaires, analyse au niveau ligne
    if not stops:
        stops = [None]

    events_count = 0
    for stop_id in stops:
        generated = await _process_line_stop(session, line_id, line_name, stop_id)
        if generated:
            events_count += 1

    return events_count


# ─── Traitement d'une (ligne, station) ───────────────────────
async def _process_line_stop(
    session: AsyncSession,
    line_id: str,
    line_name: str,
    stop_id: str | None,
) -> bool:
    """
    Calcule les métriques et génère un événement si nécessaire.
    Retourne True si un événement a été créé.
    """

    # ── Calcul des métriques ───────────────────────────────────
    delay_metrics = await compute_mean_delay(session, line_id, stop_id, window_minutes=5)
    regularity_metrics = await compute_regularity(session, line_id, stop_id, window_minutes=10)
    persistence = await compute_persistence(session, line_id, stop_id, window_minutes=15)
    neighbor_count = await compute_spatial_propagation(session, line_id, window_minutes=10)
    official_incident = await has_official_incident(session, line_id)

    mean_delay = delay_metrics.get("mean_delay")
    missing = delay_metrics.get("missing_passages", 0)
    regularity = regularity_metrics.get("regularity_score")
    headway_gap = regularity_metrics.get("headway_gap")
    punctuality = delay_metrics.get("punctuality_score")

    # ── Score d'anomalie ───────────────────────────────────────
    result = compute_anomaly_score(
        mean_delay=mean_delay,
        abs_mean_delay=delay_metrics.get("abs_mean_delay"),
        missing_passages=missing,
        regularity_score=regularity,
        headway_gap=headway_gap,
        persistence=persistence,
        neighbor_anomaly_count=neighbor_count,
        official_incident=official_incident,
    )

    score = result["anomaly_score"]
    network_state = result["network_state"]
    now = datetime.utcnow()

    # ── Sauvegarde dans network_metrics ───────────────────────
    await session.execute(text("""
        INSERT INTO network_metrics (
            computed_at, line_id, stop_id, window_size_min,
            mean_delay, abs_mean_delay, punctuality_score, regularity_score,
            missing_passages, headway_gap, anomaly_score, network_state
        ) VALUES (
            :computed_at, :line_id, :stop_id, :window_size_min,
            :mean_delay, :abs_mean_delay, :punctuality_score, :regularity_score,
            :missing_passages, :headway_gap, :anomaly_score, :network_state
        )
    """), {
        "computed_at":       now,
        "line_id":           line_id,
        "stop_id":           stop_id,
        "window_size_min":   5,
        "mean_delay":        mean_delay,
        "abs_mean_delay":    delay_metrics.get("abs_mean_delay"),
        "punctuality_score": punctuality,
        "regularity_score":  regularity,
        "missing_passages":  missing,
        "headway_gap":       headway_gap,
        "anomaly_score":     score,
        "network_state":     network_state,
    })

    # ── Génération d'événement si score suffisant ─────────────
    if score < MIN_SCORE_FOR_EVENT:
        return False

    # Vérification doublon récent
    dedup_start = now - timedelta(minutes=DEDUP_WINDOW_MINUTES)
    dedup_result = await session.execute(text("""
        SELECT COUNT(*) FROM events
        WHERE line_id = :line_id
          AND (CAST(:stop_id AS VARCHAR) IS NULL OR stop_id = CAST(:stop_id AS VARCHAR))
          AND status = 'ouvert'
          AND computed_at >= :dedup_start
          AND event_type = :event_type
    """), {
        "line_id":    line_id,
        "stop_id":    stop_id,
        "dedup_start": dedup_start,
        "event_type": result["event_type"],
    })

    if dedup_result.scalar() > 0:
        return False  # événement similaire déjà ouvert récemment

    # Insertion de l'événement
    await session.execute(text("""
        INSERT INTO events (
            computed_at, line_id, stop_id, event_type, severity,
            anomaly_score, network_state, status,
            official_incident_flag, description, justification
        ) VALUES (
            :computed_at, :line_id, :stop_id, :event_type, :severity,
            :anomaly_score, :network_state, 'ouvert',
            :official_incident_flag, :description, :justification
        )
    """), {
        "computed_at":           now,
        "line_id":               line_id,
        "stop_id":               stop_id,
        "event_type":            result["event_type"],
        "severity":              result["severity"],
        "anomaly_score":         score,
        "network_state":         network_state,
        "official_incident_flag": official_incident,
        "description":           result["justification"],
        "justification":         str(result["components"]),
    })

    logger.info(
        f"Événement généré — {line_id} {stop_id or ''} "
        f"score={score} état={network_state} type={result['event_type']}"
    )
    return True


# ─── Nettoyage historique 24h ─────────────────────────────────
async def _cleanup_old_events(session: AsyncSession):
    """
    Clôture les événements de plus de 24h et supprime les
    network_metrics de plus de 24h pour garder la base légère.
    """
    cutoff = datetime.utcnow() - timedelta(hours=HISTORY_HOURS)

    # Clôture des vieux événements ouverts
    closed = await session.execute(text("""
        UPDATE events
        SET status = 'clos'
        WHERE status = 'ouvert'
          AND computed_at < :cutoff
    """), {"cutoff": cutoff})

    # Suppression des vieilles métriques
    await session.execute(text("""
        DELETE FROM network_metrics
        WHERE computed_at < :cutoff
    """), {"cutoff": cutoff})

    logger.info(f"Nettoyage 24h — {closed.rowcount} événement(s) clôturé(s)")


# ─── Score réseau global ──────────────────────────────────────
async def compute_global_network_status() -> dict:
    """
    Calcule l'état global du réseau pour le endpoint /network/status.
    """
    async with _get_session() as session:
        # Événements actifs
        active_result = await session.execute(text("""
            SELECT COUNT(*) FROM events WHERE status = 'ouvert'
        """))
        active_count = active_result.scalar() or 0

        # Score moyen des dernières métriques par ligne
        metrics_result = await session.execute(text("""
            SELECT line_id, AVG(anomaly_score) as avg_score, MAX(network_state) as state
            FROM network_metrics
            WHERE computed_at >= NOW() - INTERVAL '5 minutes'
            GROUP BY line_id
            ORDER BY avg_score DESC NULLS LAST
        """))
        line_metrics = metrics_result.fetchall()

        # Top 5 lignes dégradées
        top_degraded = [
            {"line_id": row[0], "score": round(row[1] or 0, 1), "state": row[2]}
            for row in line_metrics[:5]
            if row[1] and row[1] >= 26
        ]

        # Score global = moyenne pondérée
        scores = [row[1] for row in line_metrics if row[1] is not None]
        global_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        # État global dérivé du score
        if global_score >= 76:
            global_state = "perturbe"
        elif global_score >= 51:
            global_state = "degrade"
        elif global_score >= 26:
            global_state = "sous_surveillance"
        else:
            global_state = "nominal"

        # Incidents officiels actifs
        incidents_result = await session.execute(text("""
            SELECT COUNT(*) FROM official_incidents
            WHERE start_time <= NOW()
              AND (end_time IS NULL OR end_time >= NOW())
        """))
        incidents_count = incidents_result.scalar() or 0

        return {
            "global_score": global_score,
            "network_state": global_state,
            "active_events_count": active_count,
            "official_incidents_count": incidents_count,
            "top_degraded_lines": top_degraded,
            "last_updated": datetime.utcnow().isoformat(),
        }
