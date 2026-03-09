"""
Canal Educação v3.0 — Modelo de Utilizador (IAM).
Suporta login por email, convites, confirmação e RBAC.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Autenticação ---
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Null até confirmar convite

    # --- Perfil ---
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # --- RBAC ---
    role = Column(String(50), default="assistente", nullable=False)

    # --- Confirmação de Email ---
    email_confirmed = Column(Boolean, default=False, nullable=False)
    invite_token = Column(String(255), nullable=True, unique=True, index=True)
    invite_expires_at = Column(DateTime(timezone=True), nullable=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # --- Auditoria ---
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relationships ---
    inviter = relationship("User", remote_side=[id], foreign_keys=[invited_by])