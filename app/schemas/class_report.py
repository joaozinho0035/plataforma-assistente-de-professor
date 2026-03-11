"""
Canal Educação v3.0 — Schemas de Relatório de Aula (ClassReport).
DTOs Pydantic com validação completa conforme spec v3.0.
Inclui PaginatedReportsResponse para server-side pagination (§5.3).
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class ClassReportCreate(BaseModel):
    """
    Request para criar um relatório de aula (rascunho).
    Campos do contexto operacional (B) podem vir auto-preenchidos pelo frontend.
    """

    # --- B. Contexto Operacional ---
    data_aula: date
    turno: str
    estudio: str
    turma_id: UUID
    disciplina_id: UUID
    professor_id: UUID
    horario_aula: str
    regular: str = "Sim"

    # --- C. Detalhes da Execução ---
    tipo_aula: str
    canal_utilizado: str
    conteudo_ministrado: str
    interacao_professor_aluno: str = "Não"
    interacao_outras_desc: Optional[str] = None
    atividade_pratica: Optional[str] = None
    observacoes: Optional[str] = None

    # --- D. Recursos e Materiais ---
    tipo_recursos_utilizados: Optional[List[str]] = None
    recursos_outro_desc: Optional[str] = None
    problema_material: str = "Não"
    problema_material_outro_desc: Optional[str] = None

    # --- E. Ocorrências Operacionais ---
    teve_substituicao: bool = False
    professor_substituto_id: Optional[UUID] = None
    teve_atraso: bool = False
    minutos_atraso: Optional[int] = None
    observacao_atraso: Optional[str] = None

    @field_validator("conteudo_ministrado")
    @classmethod
    def validate_conteudo(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("Conteúdo ministrado deve ter no máximo 100 caracteres.")
        return v.strip()

    @field_validator("minutos_atraso")
    @classmethod
    def validate_minutos(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 5 or v > 60 or v % 5 != 0):
            raise ValueError(
                "Minutos de atraso devem ser múltiplos de 5, entre 5 e 60."
            )
        return v


class ClassReportFinalize(BaseModel):
    """Request para finalizar um relatório (muda status para FINALIZADO)."""

    pass


class ClassReportCancel(BaseModel):
    """Request para cancelar um relatório."""

    justificativa: str


class ClassReportResponse(BaseModel):
    """Response completa de um relatório de aula."""

    # A. Metadados
    id: UUID
    created_by: UUID
    created_at: datetime
    status: str

    # B. Contexto
    data_aula: date
    turno: str
    estudio: str
    turma_id: UUID
    disciplina_id: UUID
    professor_id: UUID
    horario_aula: str
    regular: str

    # C. Execução
    tipo_aula: str
    canal_utilizado: str
    conteudo_ministrado: str
    interacao_professor_aluno: str
    interacao_outras_desc: Optional[str] = None
    atividade_pratica: Optional[str] = None
    observacoes: Optional[str] = None

    # D. Recursos
    tipo_recursos_utilizados: Optional[List[str]] = None
    recursos_outro_desc: Optional[str] = None
    problema_material: str
    problema_material_outro_desc: Optional[str] = None

    # E. Ocorrências
    teve_substituicao: bool
    professor_substituto_id: Optional[UUID] = None
    teve_atraso: bool
    minutos_atraso: Optional[int] = None
    observacao_atraso: Optional[str] = None

    # F. Auditoria
    nome_ficheiro_gerado: Optional[str] = None
    conflito_geminada_resolvido: bool

    # G. Compliance Digital (§6)
    video_link: Optional[str] = None
    video_folder_link: Optional[str] = None
    status_compliance: str = "Pendente"

    class Config:
        from_attributes = True


class PaginatedReportsResponse(BaseModel):
    """Response paginada para listagem de relatórios (§5.3)."""
    items: List[ClassReportResponse]
    total: int
    limit: int
    offset: int

    class Config:
        from_attributes = True
