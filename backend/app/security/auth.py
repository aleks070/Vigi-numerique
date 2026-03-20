"""
auth.py — Sécurité : hachage des mots de passe et gestion des tokens JWT

- Hachage bcrypt pour les mots de passe
- Tokens JWT signés avec HS256
- Dépendance FastAPI pour protéger les endpoints
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Agent

# ─── Configuration ────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALGORITHM = "HS256"


# ─── Mots de passe ────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hache un mot de passe en clair avec bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké."""
    return pwd_context.verify(plain, hashed)


# ─── Tokens JWT ───────────────────────────────────────────────
def create_access_token(agent_id: str, role: str) -> str:
    """Génère un token JWT signé valable JWT_EXPIRY secondes."""
    expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRY)
    payload = {
        "sub": agent_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Décode et valide un token JWT. Lève une exception si invalide."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Dépendance FastAPI ───────────────────────────────────────
async def get_current_agent(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """
    Dépendance à injecter dans les endpoints protégés.
    Vérifie le token et retourne l'agent connecté.
    """
    payload = decode_token(token)
    agent_id = payload.get("sub")

    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
        )

    result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent or not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent introuvable ou désactivé",
        )

    return agent


def require_role(required_role: str):
    """Dépendance pour restreindre par rôle (RBAC)."""
    async def _check(agent: Agent = Depends(get_current_agent)):
        roles_hierarchy = ["operateur", "superviseur", "admin"]
        agent_level = roles_hierarchy.index(agent.role) if agent.role in roles_hierarchy else -1
        required_level = roles_hierarchy.index(required_role) if required_role in roles_hierarchy else 99

        if agent_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle '{required_role}' requis",
            )
        return agent
    return _check