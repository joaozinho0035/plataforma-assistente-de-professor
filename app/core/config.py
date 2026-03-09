"""
Canal Educação v3.0 — Configuração centralizada via Pydantic Settings.
Todas as variáveis sensíveis são carregadas do .env.
"""

import json
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação. Valores carregados do .env automaticamente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # --- Aplicação ---
    APP_NAME: str = "Canal Educação API"
    APP_VERSION: str = "3.0"
    DEBUG: bool = False

    # --- Base de Dados ---
    DATABASE_URL: str = "postgresql://admin:senha_super_secreta@db:5432/canal_edu"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- Segurança JWT ---
    SECRET_KEY: str = "chave_secreta_provisoria_desenvolvimento"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas

    # --- Tokens de Convite ---
    INVITE_TOKEN_EXPIRE_HOURS: int = 24

    # --- SMTP (Email Transacional) ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@canaleducacao.com"
    SMTP_USE_TLS: bool = True

    # --- Domínios permitidos (vazio = qualquer email) ---
    ALLOWED_EMAIL_DOMAINS: List[str] = []

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost:3000"]

    # --- Google Drive ---
    GOOGLE_DRIVE_VIDEOS_FOLDER_ID: str = "id_pendente"
    GOOGLE_DRIVE_PDFS_FOLDER_ID: str = "id_pendente"
    GOOGLE_APPLICATION_CREDENTIALS: str = "credentials.json"

    @field_validator("ALLOWED_EMAIL_DOMAINS", "CORS_ORIGINS", mode="before")
    @classmethod
    def parse_list_from_string(cls, v):
        """Handles empty strings and JSON-encoded lists from .env."""
        if isinstance(v, list):
            return v
        if not v or v.strip() == "":
            return []
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except (json.JSONDecodeError, TypeError):
            # Comma-separated fallback
            return [s.strip() for s in v.split(",") if s.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Singleton cacheado da configuração."""
    return Settings()
