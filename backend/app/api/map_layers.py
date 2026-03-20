from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.database import get_db

router = APIRouter()


@router.get("/layers")
async def get_map_layers(db: AsyncSession = Depends(get_db)):
    """
    Retourne les données GeoJSON pour la carte :
    - stations colorées par état réseau (dernière métrique connue)
    - incidents officiels actifs
    """

    # ── Stations avec leur dernier état connu ──────────────────
    stations_result = await db.execute(text("""
        SELECT
            s.stop_id,
            s.stop_name,
            s.lat,
            s.lon,
            s.zone_id,
            s.nature,
            COALESCE(nm.network_state, 'nominal') as network_state,
            COALESCE(nm.anomaly_score, 0) as anomaly_score
        FROM stations s
        LEFT JOIN LATERAL (
            SELECT network_state, anomaly_score
            FROM network_metrics
            WHERE stop_id = s.stop_id
            ORDER BY computed_at DESC
            LIMIT 1
        ) nm ON true
        WHERE s.lat IS NOT NULL AND s.lon IS NOT NULL
    """))

    stations = stations_result.fetchall()

    # ── Incidents officiels actifs ─────────────────────────────
    incidents_result = await db.execute(text("""
        SELECT
            i.incident_id,
            i.line_id,
            i.label,
            i.description,
            i.severity,
            s.lat,
            s.lon,
            s.stop_name
        FROM official_incidents i
        LEFT JOIN stations s ON s.stop_id = i.stop_id
        WHERE i.start_time <= NOW()
          AND (i.end_time IS NULL OR i.end_time >= NOW())
    """))

    incidents = incidents_result.fetchall()

    # ── Construction GeoJSON ───────────────────────────────────
    station_features = []
    for row in stations:
        if row.lat is None or row.lon is None:
            continue
        station_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row.lon, row.lat],
            },
            "properties": {
                "stop_id":      row.stop_id,
                "stop_name":    row.stop_name,
                "zone_id":      row.zone_id,
                "nature":       row.nature,
                "network_state": row.network_state,
                "anomaly_score": float(row.anomaly_score),
            }
        })

    incident_features = []
    for row in incidents:
        if row.lat is None or row.lon is None:
            continue
        incident_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row.lon, row.lat],
            },
            "properties": {
                "incident_id": row.incident_id,
                "line_id":     row.line_id,
                "label":       row.label,
                "description": row.description,
                "severity":    row.severity,
                "stop_name":   row.stop_name,
                "type":        "incident",
            }
        })

    return {
        "stations": {
            "type": "FeatureCollection",
            "features": station_features,
        },
        "incidents": {
            "type": "FeatureCollection",
            "features": incident_features,
        },
        "meta": {
            "stations_count": len(station_features),
            "incidents_count": len(incident_features),
        }
    }