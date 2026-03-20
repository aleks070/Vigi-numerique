from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.ingestion.prim_client import fetch_stop_monitoring, fetch_general_message
from app.ingestion.persistence import save_observed_passages, save_official_incidents
from app.detection.engine import run_detection_cycle
import asyncio
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def collect_data():
    """Wrapper synchrone pour le scheduler."""
    asyncio.run(_collect_data_async())


async def _collect_data_async():
    logger.info("─── Collecte PRIM démarrée ───")

    # 1. Incidents officiels → récupération + persistence
    incidents = await fetch_general_message(line_ref="STIF:Line::C01742:")
    logger.info(f"Incidents récupérés : {len(incidents)}")
    await save_official_incidents(incidents)

    # 2. Passages temps réel → récupération + persistence
    test_stops = [
        "STIF:StopPoint:Q:41027:",
    ]
    total_passages = 0
    for stop_ref in test_stops:
        passages = await fetch_stop_monitoring(stop_ref)
        total_passages += len(passages)
        await save_observed_passages(passages)

    logger.info(f"Passages temps réel récupérés : {total_passages}")
    logger.info("─── Collecte PRIM terminée ───")

    # 3. Moteur de détection
    logger.info("─── Moteur de détection démarré ───")
    events_count = await run_detection_cycle()
    logger.info(f"─── Détection terminée — {events_count} événement(s) ───")


def start_scheduler():
    scheduler.add_job(
        collect_data,
        trigger="interval",
        seconds=settings.ALERT_POLL_INTERVAL,
        id="collect_prim",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler démarré — collecte toutes les {settings.ALERT_POLL_INTERVAL}s")