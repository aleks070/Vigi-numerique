"""
api/auth.py — Endpoints d'authentification

POST /auth/login   → retourne un token JWT
GET  /auth/me      → retourne l'agent connecté
POST /auth/agents  → crée un nouvel agent (admin uniquement)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Agent
from app.security.auth import (
    create_access_token,
    get_current_agent,
    hash_password,
    verify_password,
    require_role,
)

router = APIRouter()


# ─── Schémas Pydantic ──────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent_id: str
    full_name: str
    role: str


class AgentResponse(BaseModel):
    agent_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None


class CreateAgentRequest(BaseModel):
    agent_id: str
    email: str
    full_name: str
    password: str
    role: str = "operateur"


# ─── Login ────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Authentifie un agent par email + mot de passe.
    Retourne un token JWT à inclure dans les requêtes suivantes.
    """
    # Cherche l'agent par email (username = email dans OAuth2)
    result = await db.execute(
        select(Agent).where(Agent.email == form.username)
    )
    agent = result.scalar_one_or_none()

    if not agent or not verify_password(form.password, agent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé — contacter l'administrateur",
        )

    # Mise à jour du dernier login
    agent.last_login = datetime.utcnow()
    await db.commit()

    token = create_access_token(agent_id=agent.agent_id, role=agent.role)

    return TokenResponse(
        access_token=token,
        agent_id=agent.agent_id,
        full_name=agent.full_name,
        role=agent.role,
    )


# ─── Profil agent connecté ────────────────────────────────────
@router.get("/me", response_model=AgentResponse)
async def get_me(agent: Agent = Depends(get_current_agent)):
    """Retourne les informations de l'agent actuellement connecté."""
    return AgentResponse(
        agent_id=agent.agent_id,
        email=agent.email,
        full_name=agent.full_name,
        role=agent.role,
        is_active=agent.is_active,
        created_at=agent.created_at,
        last_login=agent.last_login,
    )


# ─── Création d'un agent (admin uniquement) ───────────────────
@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    payload: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    _: Agent = Depends(require_role("admin")),
):
    """Crée un nouvel agent. Réservé aux administrateurs."""
    # Vérification doublon
    existing = await db.execute(
        select(Agent).where(
            (Agent.agent_id == payload.agent_id) | (Agent.email == payload.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent ID ou email déjà utilisé",
        )

    if payload.role not in ("operateur", "superviseur", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rôle invalide — choisir parmi : operateur, superviseur, admin",
        )

    agent = Agent(
        agent_id=payload.agent_id,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(agent)
    await db.commit()

    return AgentResponse(
        agent_id=agent.agent_id,
        email=agent.email,
        full_name=agent.full_name,
        role=agent.role,
        is_active=agent.is_active,
        created_at=agent.created_at,
        last_login=agent.last_login,
    )