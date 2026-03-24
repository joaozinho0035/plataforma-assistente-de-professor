"""
Canal Educação v3.0 — Modelo de Relatório de Aula (class_reports).
29 campos conforme especificação técnica v3.0.
"""

import uuid
from datetime import datetime, timezone
from app.core.config import get_settings

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClassReport(Base):
    __tablename__ = "class_reports"

    # ─── A. Metadados do Registo (Automáticos) ───────────────────────
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status = Column(
        String(20), default="RASCUNHO", nullable=False
    )  # RASCUNHO, FINALIZADO, CANCELADO

    # ─── B. Contexto Operacional ─────────────────────────────────────
    data_aula = Column(Date, nullable=False)
    turno = Column(String(20), nullable=False)  # Manhã, Tarde, Noite
    estudio = Column(String(50), nullable=False)  # Estúdio 01..09, Externo
    turma_id = Column(UUID(as_uuid=True), ForeignKey("turmas.id"), nullable=False)
    disciplina_id = Column(
        UUID(as_uuid=True), ForeignKey("disciplinas.id"), nullable=False
    )
    professor_id = Column(
        UUID(as_uuid=True), ForeignKey("professores.id"), nullable=False
    )
    horario_aula = Column(String(50), nullable=False)
    regular = Column(String(10), default="Sim", nullable=False)  # Sim / Não

    # ─── C. Detalhes da Execução ─────────────────────────────────────
    tipo_aula = Column(String(100), nullable=False)
    canal_utilizado = Column(String(50), nullable=False)
    conteudo_ministrado = Column(String(100), nullable=False)
    interacao_professor_aluno = Column(
        String(50), default="Não", nullable=False
    )
    interacao_outras_desc = Column(Text, nullable=True)
    atividade_pratica = Column(String(50), nullable=True)
    observacoes = Column(Text, nullable=True)

    # ─── D. Recursos e Materiais ─────────────────────────────────────
    tipo_recursos_utilizados = Column(JSON, nullable=True)  # Array de strings
    recursos_outro_desc = Column(Text, nullable=True)
    problema_material = Column(String(50), default="Não", nullable=False)
    problema_material_outro_desc = Column(Text, nullable=True)

    # ─── E. Ocorrências Operacionais ─────────────────────────────────
    teve_substituicao = Column(Boolean, default=False, nullable=False)
    professor_substituto_id = Column(
        UUID(as_uuid=True), ForeignKey("professores.id"), nullable=True
    )
    teve_atraso = Column(Boolean, default=False, nullable=False)
    minutos_atraso = Column(Integer, nullable=True)
    observacao_atraso = Column(Text, nullable=True)

    # ─── F. Auditoria e Faturamento ──────────────────────────────────
    nome_ficheiro_gerado = Column(String(500), nullable=True)
    conflito_geminada_resolvido = Column(Boolean, default=False, nullable=False)
    
    # ─── G. Compliance Digital (§6) ──────────────────────────────────
    video_link = Column(String(1000), nullable=True)
    status_compliance = Column(String(20), default="Pendente", nullable=False) # Verde, Vermelho, Pendente
    md5_checksum = Column(String(32), nullable=True)

    @property
    def video_folder_link(self) -> str:
        settings = get_settings()
        folder_id = settings.GOOGLE_DRIVE_VIDEOS_FOLDER_ID
        if not folder_id or folder_id == "id_pendente":
            return None
        return f"https://drive.google.com/drive/folders/{folder_id}"

    # ─── Relationships ───────────────────────────────────────────────
    creator = relationship("User", foreign_keys=[created_by])
    turma = relationship("Turma")
    disciplina = relationship("Disciplina")
    professor = relationship("Professor", foreign_keys=[professor_id])
    professor_substituto = relationship(
        "Professor", foreign_keys=[professor_substituto_id]
    )
