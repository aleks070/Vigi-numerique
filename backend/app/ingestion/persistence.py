import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from app.core.config import settings
from app.db.models import (
    ObservedPassage,
    OfficialIncident,
    ScheduledPassage,
)

logger = logging.getLogger(__name__)


def _get_session():
    """Crée un engine et une session frais à chaque appel du scheduler."""
    engine = create_async_engine(
        settings.POSTGRES_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return Session()


# ─── Passages temps réel ──────────────────────────────────────
async def save_observed_passages(passages: list[dict]) -> int:
    """
    Insère les passages temps réel dans observed_passages.
    Retourne le nombre de lignes insérées.
    """
    if not passages:
        return 0

    async with _get_session() as session:
        try:
            count = 0
            for p in passages:
                # On n'insère que si on a les champs obligatoires
                if not p.get("line_ref") or not p.get("stop_ref"):
                    continue
                if not p.get("observed_time"):
                    continue

                observed = ObservedPassage(
                    line_id=p["line_ref"],
                    stop_id=p["stop_ref"],
                    direction=p.get("direction"),
                    observed_time=_parse_dt(p["observed_time"]),
                    collected_at=datetime.utcnow(),
                    source_ref=p.get("trip_id"),
                    status=p.get("status"),
                    raw_payload=p.get("raw_payload"),
                )
                session.add(observed)
                count += 1

            await session.commit()
            logger.info(f"save_observed_passages → {count} passages sauvegardés")
            return count

        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur save_observed_passages: {e}")
            return 0


# ─── Incidents officiels ──────────────────────────────────────
async def save_official_incidents(incidents: list[dict]) -> int:
    """
    Upsert les incidents officiels dans official_incidents.
    Met à jour si l'incident existe déjà (même incident_id).
    Retourne le nombre de lignes traitées.
    """
    if not incidents:
        return 0

    async with _get_session() as session:
        try:
            count = 0
            for inc in incidents:
                incident_id = inc.get("incident_id")
                if not incident_id:
                    continue

                # Upsert — on met à jour si l'incident existe déjà
                stmt = insert(OfficialIncident).values(
                    incident_id=incident_id,
                    line_id=inc.get("line_id"),
                    stop_id=inc.get("stop_id"),
                    severity=inc.get("severity"),
                    start_time=_parse_dt(inc.get("start_time")) or datetime.utcnow(),
                    end_time=_parse_dt(inc.get("end_time")),
                    label=inc.get("label"),
                    description=inc.get("description"),
                    source_payload=inc.get("raw_payload"),
                ).on_conflict_do_update(
                    index_elements=["incident_id"],
                    set_={
                        "severity":       inc.get("severity"),
                        "end_time":       _parse_dt(inc.get("end_time")),
                        "label":          inc.get("label"),
                        "description":    inc.get("description"),
                        "source_payload": inc.get("raw_payload"),
                    }
                )
                await session.execute(stmt)
                count += 1

            await session.commit()
            logger.info(f"save_official_incidents → {count} incidents sauvegardés")
            return count

        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur save_official_incidents: {e}")
            return 0


# ─── Passages théoriques ──────────────────────────────────────
async def save_scheduled_passages(passages: list[dict]) -> int:
    """
    Insère les passages théoriques dans scheduled_passages.
    Ignore les doublons (même trip_id + stop_ref + scheduled_time).
    Retourne le nombre de lignes insérées.
    """
    if not passages:
        return 0

    async with _get_session() as session:
        try:
            count = 0
            for p in passages:
                if not p.get("line_ref") or not p.get("stop_ref"):
                    continue
                if not p.get("scheduled_time"):
                    continue

                # Vérifie si ce passage théorique existe déjà
                existing = await session.execute(
                    select(ScheduledPassage).where(
                        ScheduledPassage.trip_id == p.get("trip_id"),
                        ScheduledPassage.stop_id == p["stop_ref"],
                        ScheduledPassage.scheduled_time == _parse_dt(p["scheduled_time"]),
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # déjà en base, on skip

                scheduled = ScheduledPassage(
                    line_id=p["line_ref"],
                    stop_id=p["stop_ref"],
                    direction=p.get("direction"),
                    trip_id=p.get("trip_id"),
                    scheduled_time=_parse_dt(p["scheduled_time"]),
                    service_date=_parse_date(p.get("service_date")),
                )
                session.add(scheduled)
                count += 1

            await session.commit()
            logger.info(f"save_scheduled_passages → {count} passages théoriques sauvegardés")
            return count

        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur save_scheduled_passages: {e}")
            return 0


# ─── Utilitaires ──────────────────────────────────────────────
def _parse_dt(value: str | None) -> datetime | None:
    """Parse une date ISO 8601 en datetime UTC naïf (sans timezone)."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Convertit en datetime naïf UTC pour PostgreSQL TIMESTAMP WITHOUT TIME ZONE
        return dt.replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


def _parse_date(value: str | None):
    """Parse une date YYYY-MM-DD, retourne None si invalide."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None
