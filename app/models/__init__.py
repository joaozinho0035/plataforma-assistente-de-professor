"""
Canal Educação v3.0 — Models package init.
Importa todos os modelos para garantir que o SQLAlchemy os registra.
"""

from app.models.audit_log import AuditLog
from app.models.auxiliares import (
    Disciplina,
    Grade,
    Professor,
    ProfessorDisciplina,
    Unit,
)
from app.models.class_report import ClassReport
from app.models.turma import Turma
from app.models.user import User

__all__ = [
    "AuditLog",
    "User",
    "Turma",
    "ClassReport",
    "Professor",
    "Disciplina",
    "Grade",
    "Unit",
    "ProfessorDisciplina",
]
