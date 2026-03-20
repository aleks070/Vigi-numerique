# ─── backend/app/api/network.py ───────────────────────────────
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db

router = APIRouter()


@router.get("/status")
async def get_network_status(db: AsyncSession = Depends(get_db)):
    """État global du réseau — score composite + top lignes dégradées."""
    # TODO: implémenter le calcul du score global
    return {
        "global_score": None,
        "network_state": "nominal",
        "top_degraded_lines": [],
        "active_events_count": 0,
        "last_updated": None,
    }
