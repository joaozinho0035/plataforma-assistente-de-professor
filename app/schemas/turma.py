from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# 1. O formato base exigido
class TurmaBase(BaseModel):
    nome: str
    modalidade: str
    serie_modulo: str
    turno: str
    nome_pasta_drive: Optional[str] = None

# 2. O que exigimos ao CRIAR uma turma (igual ao base por agora)
class TurmaCreate(TurmaBase):
    pass

# 3. O que DEVOLVEMOS ao utilizador (inclui o ID gerado pelo banco)
class TurmaResponse(TurmaBase):
    id: UUID

    class Config:
        from_attributes = True