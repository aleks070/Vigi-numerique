import httpx
import logging
from datetime import datetime
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

PRIM_BASE_URL = settings.PRIM_BASE_URL
HEADERS = {"apikey": settings.IDFM_API_KEY}


# ─── Client HTTP réutilisable ─────────────────────────────────
async def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=PRIM_BASE_URL,
        headers=HEADERS,
        timeout=10.0,
    )


# ─── 1. Passages temps réel sur un arrêt ─────────────────────
async def fetch_stop_monitoring(stop_ref: str) -> list[dict]:
    """
    Récupère les prochains passages en temps réel pour un arrêt donné.
    stop_ref : identifiant IDFM ex. "STIF:StopPoint:Q:41027:"
    Retourne une liste de passages normalisés.
    """
    async with await get_client() as client:
        try:
            response = await client.get(
                "/stop-monitoring",
                params={"MonitoringRef": stop_ref},
            )
            response.raise_for_status()
            data = response.json()

            deliveries = (
                data.get("Siri", {})
                    .get("ServiceDelivery", {})
                    .get("StopMonitoringDelivery", [])
            )

            passages = []
            for delivery in deliveries:
                for visit in delivery.get("MonitoredStopVisit", []):
                    passages.append(_normalize_stop_visit(visit))

            logger.info(f"fetch_stop_monitoring({stop_ref}) → {len(passages)} passages")
            return passages

        except httpx.HTTPError as e:
            logger.error(f"Erreur PRIM stop-monitoring: {e}")
            return []


# ─── 2. Perturbations / incidents officiels ───────────────────
async def fetch_general_message(line_ref: Optional[str] = None) -> list[dict]:
    """
    Récupère les messages de perturbation officiels sur le réseau.
    line_ref : ex. "STIF:Line::C01742:" (obligatoire pour PRIM)
    """
    async with await get_client() as client:
        try:
            params = {}
            if line_ref:
                params["LineRef"] = line_ref

            response = await client.get("/general-message", params=params)
            response.raise_for_status()
            data = response.json()

            messages = (
                data.get("Siri", {})
                    .get("ServiceDelivery", {})
                    .get("GeneralMessageDelivery", [])
            )

            incidents = []
            for delivery in messages:
                for msg in delivery.get("InfoMessage", []):
                    incidents.append(_normalize_incident(msg))

            logger.info(f"fetch_general_message() → {len(incidents)} incidents")
            return incidents

        except httpx.HTTPError as e:
            logger.error(f"Erreur PRIM general-message: {e}")
            return []


# ─── 3. Passages théoriques (offre planifiée) ─────────────────
async def fetch_line_timetable(line_ref: str, stop_ref: str) -> list[dict]:
    """
    Récupère les horaires théoriques pour une ligne et un arrêt.
    line_ref : ex. "STIF:Line::C01742:"
    stop_ref : ex. "STIF:StopPoint:Q:41027:"
    """
    async with await get_client() as client:
        try:
            response = await client.get(
                "/line-timetable",
                params={
                    "LineRef": line_ref,
                    "MonitoringRef": stop_ref,
                },
            )
            response.raise_for_status()
            data = response.json()

            deliveries = (
                data.get("Siri", {})
                    .get("ServiceDelivery", {})
                    .get("TimetabledStoppingVisitDelivery", [])
            )

            passages = []
            for delivery in deliveries:
                for visit in delivery.get("TimetabledStoppingVisit", []):
                    passages.append(_normalize_timetable_visit(visit))

            logger.info(f"fetch_line_timetable({line_ref}) → {len(passages)} passages théoriques")
            return passages

        except httpx.HTTPError as e:
            logger.error(f"Erreur PRIM line-timetable: {e}")
            return []


# ─── Normalisation des réponses SIRI ─────────────────────────
def _normalize_stop_visit(visit: dict) -> dict:
    """Transforme un MonitoredStopVisit SIRI en dict normalisé."""
    mvj = visit.get("MonitoredVehicleJourney", {})
    call = mvj.get("MonitoredCall", {})

    # Heure réelle ou estimée
    observed_time = (
        call.get("ExpectedArrivalTime")
        or call.get("ExpectedDepartureTime")
        or call.get("AimedArrivalTime")
        or call.get("AimedDepartureTime")
    )

    # Heure théorique
    scheduled_time = (
        call.get("AimedArrivalTime")
        or call.get("AimedDepartureTime")
    )

    return {
        "line_ref":       mvj.get("LineRef", {}).get("value", ""),
        "stop_ref":       visit.get("MonitoringRef", {}).get("value", ""),
        "direction":      mvj.get("DirectionName", [{}])[0].get("value", ""),
        "trip_id":        mvj.get("FramedVehicleJourneyRef", {}).get("DatedVehicleJourneyRef", ""),
        "observed_time":  observed_time,
        "scheduled_time": scheduled_time,
        "status":         call.get("ArrivalStatus", ""),
        "collected_at":   datetime.utcnow().isoformat(),
        "raw_payload":    visit,
    }


def _normalize_incident(msg: dict) -> dict:
    """Transforme un InfoMessage SIRI en dict normalisé."""
    content = msg.get("Content", {})
    line_refs = content.get("LineRef", [])
    stop_refs = content.get("StopPointRef", [])

    return {
        "incident_id":  msg.get("InfoMessageIdentifier", {}).get("value", ""),
        "line_id":      line_refs[0].get("value", "") if line_refs else None,
        "stop_id":      stop_refs[0].get("value", "") if stop_refs else None,
        "severity":     content.get("Severity", "unknown"),
        "start_time":   msg.get("ValidUntilTime", None),
        "label":        content.get("Summary", [{}])[0].get("value", ""),
        "description":  content.get("Description", [{}])[0].get("value", ""),
        "raw_payload":  msg,
    }


def _normalize_timetable_visit(visit: dict) -> dict:
    """Transforme un TimetabledStoppingVisit en dict normalisé."""
    return {
        "line_ref":        visit.get("LineRef", {}).get("value", ""),
        "stop_ref":        visit.get("StopPointRef", {}).get("value", ""),
        "direction":       visit.get("DirectionName", [{}])[0].get("value", ""),
        "trip_id":         visit.get("DatedVehicleJourneyRef", ""),
        "scheduled_time":  (
            visit.get("TimetabledArrivalTime")
            or visit.get("TimetabledDepartureTime")
        ),
        "service_date":    visit.get("ServiceDate", ""),
    }