"""
Canal Educação v3.0 — Modelos Auxiliares / Fundação.
Tabelas base: Unit, Professor, Disciplina, Grade, ProfessorDisciplina (M:N).
"""

import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Unit(Base):
    __tablename__ = "units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)

    turmas = relationship("Turma", back_populates="unit")


class ProfessorDisciplina(Base):
    """Tabela associativa M:N entre Professor e Disciplina."""

    __tablename__ = "professor_disciplinas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professor_id = Column(
        UUID(as_uuid=True), ForeignKey("professores.id"), nullable=False
    )
    disciplina_id = Column(
        UUID(as_uuid=True), ForeignKey("disciplinas.id"), nullable=False
    )


class Professor(Base):
    __tablename__ = "professores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False, unique=True)

    # M:N com Disciplina
    disciplinas = relationship(
        "Disciplina",
        secondary="professor_disciplinas",
        back_populates="professores",
    )


class Disciplina(Base):
    __tablename__ = "disciplinas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    nomenclatura_padrao = Column(String(255), nullable=True)

    # M:N com Professor
    professores = relationship(
        "Professor",
        secondary="professor_disciplinas",
        back_populates="disciplinas",
    )


class Grade(Base):
    __tablename__ = "grades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Relacionamentos ---
    turma_id = Column(UUID(as_uuid=True), ForeignKey("turmas.id"), nullable=True)
    disciplina_id = Column(
        UUID(as_uuid=True), ForeignKey("disciplinas.id"), nullable=True
    )
    professor_id = Column(
        UUID(as_uuid=True), ForeignKey("professores.id"), nullable=True
    )

    # --- Horários ---
    dia_semana = Column(String(20), nullable=False)
    horario_inicio = Column(Time, nullable=False)
    horario_fim = Column(Time, nullable=False)
    turno_aula = Column(String(20), nullable=False)

    # --- Canal ---
    canal_iptv = Column(Integer, nullable=True)
    descricao = Column(String(255), nullable=True)

    # --- Relationships ---
    turma = relationship("Turma", backref="grades")
    disciplina = relationship("Disciplina", backref="grades")
    professor = relationship("Professor", backref="grades")