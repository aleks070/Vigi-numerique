# ─── backend/app/api/events.py ────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import Event, EventQualification

router = APIRouter()


# ── Schémas Pydantic ──────────────────────────────────────────
class QualificationPayload(BaseModel):
    agent_id: str
    qualification: str  # CONFIRME, FAUX_POSITIF, DEJA_CONNU, CLOS, EN_COURS_ANALYSE
    comment: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────
@router.get("")
async def list_events(
    line_id:  Optional[str] = Query(None, description="Filtrer par ligne"),
    status:   Optional[str] = Query(None, description="Filtrer par statut"),
    severity: Optional[str] = Query(None, description="Filtrer par gravité"),
    limit:    int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Liste des événements détectés, filtrables par ligne / statut / gravité."""
    query = select(Event).order_by(desc(Event.computed_at)).limit(limit)

    if line_id:
        query = query.where(Event.line_id == line_id)
    if status:
        query = query.where(Event.status == status)
    if severity:
        query = query.where(Event.severity == severity)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{event_id}")
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Détail d'un événement avec ses métriques et qualifications."""
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    return event


@router.post("/{event_id}/qualify")
async def qualify_event(
    event_id: int,
    payload: QualificationPayload,
    db: AsyncSession = Depends(get_db),
):
    """Qualification d'un événement par un agent."""
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")

    qualification = EventQualification(
        event_id=event_id,
        agent_id=payload.agent_id,
        qualification=payload.qualification,
        comment=payload.comment,
    )
    db.add(qualification)

    # Mettre à jour le statut de l'événement si qualifié CLOS
    if payload.qualification == "CLOS":
        event.status = "clos"

    await db.commit()
    return {"message": "Qualification enregistrée", "event_id": event_id}
