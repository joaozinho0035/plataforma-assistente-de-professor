from pydantic import BaseModel
from datetime import date
from typing import Optional, List, Any
from uuid import UUID

class LessonCreate(BaseModel):
    turma_id: UUID
    disciplina: str
    data_aula: date
    conteudo: str
    
    # --- NOVOS CAMPOS DO ESCOPO EXPANDIDO ---
    professor_id: Optional[UUID] = None
    disciplina_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    bloco: Optional[int] = None
    canal_iptv: Optional[int] = None # Campo recém-aprovado
    
    status_transmissao: Optional[str] = "agendada"
    status_compliance: Optional[str] = "amarelo"
    is_draft: Optional[bool] = True
    is_locked: Optional[bool] = False
    
    professor_substituido: Optional[bool] = False
    motivo_substituicao: Optional[str] = None
    interacao_turma: Optional[bool] = False
    atividade_pratica: Optional[str] = None
    atraso_minutos: Optional[int] = 0
    obs_atraso: Optional[str] = None
    problema_material: Optional[str] = None
    recursos_utilizados: Optional[List[Any]] = None
    observacoes_gerais: Optional[str] = None
    
    video_link: Optional[str] = None
    pdf_link: Optional[str] = None

class LessonCancel(BaseModel):
    justificativa: str

class LessonResponse(LessonCreate):
    id: UUID
    nome_padronizado: str
    criado_por: Optional[UUID] = None

    class Config:
        from_attributes = True