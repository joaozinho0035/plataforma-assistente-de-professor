"""
Canal Educação v3.0 — Módulo de Segurança.
JWT, hashing de senhas, tokens de convite.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


# ─── Hashing de Senhas ───────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica a senha usando bcrypt."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Gera o hash bcrypt da senha."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ─── JWT Access Tokens ───────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica e valida um JWT. Retorna payload ou None se inválido."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ─── Tokens de Convite ───────────────────────────────────────────────

def generate_invite_token() -> str:
    """Gera um token UUID único para convites de utilizadores."""
    return str(uuid.uuid4())


def get_invite_expiration() -> datetime:
    """Retorna a data/hora de expiração do convite (24h por padrão)."""
    return datetime.now(timezone.utc) + timedelta(
        hours=settings.INVITE_TOKEN_EXPIRE_HOURS
    )