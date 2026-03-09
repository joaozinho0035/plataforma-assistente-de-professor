"""
Canal Educação v3.0 — Modelo de Log de Auditoria (§5.4).
Registo inalterável das ações administrativas para rastreabilidade total.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    """
    Trilha de Auditoria (Security Log).
    Registo inalterável de ações de promoção de perfil,
    envio de convites e desativação de contas.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Quem executou a ação
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Tipo de ação (AuditActionEnum)
    action = Column(String(50), nullable=False, index=True)

    # Utilizador alvo da ação (ex: quem foi convidado/desativado)
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Detalhes adicionais em texto livre
    details = Column(Text, nullable=True)

    # Timestamp inalterável
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # IP do cliente (opcional, para segurança)
    ip_address = Column(String(45), nullable=True)

    # --- Relationships ---
    actor = relationship("User", foreign_keys=[actor_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
