"""
Canal Educação v3.0 — Modelo de Turma.
"""

import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Turma(Base):
    __tablename__ = "turmas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=True)

    nome = Column(String(255), nullable=False)
    modalidade = Column(String(100), nullable=False)
    serie_modulo = Column(String(100), nullable=False)
    turno = Column(String(50), nullable=False)
    nome_pasta_drive = Column(String(255), nullable=True)
    nomenclatura_padrao = Column(String(255), nullable=True)

    # --- Relationships ---
    unit = relationship("Unit", back_populates="turmas")