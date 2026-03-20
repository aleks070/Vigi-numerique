from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.detection.engine import compute_global_network_status

router = APIRouter()


@router.get("/status")
async def get_network_status():
    """État global du réseau — score composite + top lignes dégradées."""
    return await compute_global_network_status()