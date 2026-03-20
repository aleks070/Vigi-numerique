from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import Station

router = APIRouter()


@router.get("")
async def list_stations(
    line_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Référentiel des stations, filtrables par ligne."""
    query = select(Station)
    result = await db.execute(query)
    return result.scalars().all()