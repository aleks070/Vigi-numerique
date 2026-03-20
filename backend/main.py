import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import network, events, lines, stations, map_layers, auth
from app.db.database import init_db
from app.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield


app = FastAPI(
    title="Vigi Numérique API",
    description="API de supervision du trafic Île-de-France — détection d'anomalies en quasi temps réel",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/auth",     tags=["Auth"])
app.include_router(network.router,    prefix="/network",  tags=["Réseau"])
app.include_router(events.router,     prefix="/events",   tags=["Événements"])
app.include_router(lines.router,      prefix="/lines",    tags=["Lignes"])
app.include_router(stations.router,   prefix="/stations", tags=["Stations"])
app.include_router(map_layers.router, prefix="/map",      tags=["Carte"])


@app.get("/health", tags=["Système"])
async def health():
    return {"status": "ok", "service": "vigi-numerique-api"}