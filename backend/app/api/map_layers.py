from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

router = APIRouter()


@router.get("/layers")
async def get_map_layers(db: AsyncSession = Depends(get_db)):
    """Données GeoJSON pour la carte — stations et segments colorés par état."""
    # TODO: générer le GeoJSON depuis PostGIS
    return {
        "type": "FeatureCollection",
        "features": []
    }