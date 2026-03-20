from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Line

router = APIRouter()


@router.get("")
async def list_lines(db: AsyncSession = Depends(get_db)):
    """Référentiel de toutes les lignes actives."""
    result = await db.execute(select(Line).where(Line.is_active == True))
    return result.scalars().all()