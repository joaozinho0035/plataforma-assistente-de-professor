"""
Canal Educação v3.0 — Rotas de Gestão de Turmas.
CRUD de turmas com validação de regras de negócio e RBAC.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.turma import Turma
from app.models.user import User


router = APIRouter(prefix="/api/v1/turmas", tags=["Gestão de Turmas"])


# ─── Schemas ──────────────────────────────────────────────────────────


class TurmaCreate(BaseModel):
    unit_id: Optional[UUID] = None
    nome: str
    modalidade: str
    serie_modulo: str
    turno: str
    nomenclatura_padrao: Optional[str] = None


class TurmaResponse(TurmaCreate):
    id: UUID
    nome_pasta_drive: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Rotas ────────────────────────────────────────────────────────────


@router.post("/", response_model=TurmaResponse, status_code=status.HTTP_201_CREATED)
def criar_turma(
    turma: TurmaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Cria uma nova turma no sistema.
    Apenas utilizadores autenticados podem criar turmas.
    """
    turno_upper = turma.turno.strip().upper()
    modalidade_upper = turma.modalidade.strip().upper()
    serie_upper = turma.serie_modulo.strip().upper()
    nome_upper = turma.nome.strip().upper()

    # Validação de turno
    turnos_validos = {"MANHÃ", "TARDE", "NOITE", "INTEGRAL"}
    if turno_upper not in turnos_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Turno inválido ('{turma.turno}'). Escolha entre: {', '.join(turnos_validos)}.",
        )

    # Regra EJA: obrigatoriamente noite
    if "GRAVAÇÃO" not in modalidade_upper and "GRAVAÇÃO" not in nome_upper:
        if any(
            "EJA" in s
            for s in [serie_upper, modalidade_upper, nome_upper]
        ):
            if turno_upper != "NOITE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Regra de Negócio: Turmas de EJA devem ocorrer no turno NOITE.",
                )

        # Regra Integral: não pode ser noite
        if any(
            "INTEGRAL" in s for s in [serie_upper, nome_upper]
        ):
            if turno_upper == "NOITE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Regra de Negócio: Turmas Integrais ocorrem apenas MANHÃ ou TARDE.",
                )

    # Verificação de duplicidade
    turma_existente = (
        db.query(Turma)
        .filter(
            Turma.nome == turma.nome,
            Turma.turno == turma.turno,
            Turma.modalidade == turma.modalidade,
        )
        .first()
    )
    if turma_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe turma '{turma.nome}' no turno '{turma.turno}' / modalidade '{turma.modalidade}'.",
        )

    nova_turma = Turma(
        unit_id=turma.unit_id,
        nome=turma.nome,
        modalidade=turma.modalidade,
        serie_modulo=turma.serie_modulo,
        turno=turno_upper,
        nomenclatura_padrao=turma.nomenclatura_padrao,
    )

    db.add(nova_turma)
    try:
        db.commit()
        db.refresh(nova_turma)
        return nova_turma
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Colisão de dados ao gravar turma.",
        )


@router.get("/", response_model=List[TurmaResponse])
def listar_turmas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista todas as turmas cadastradas."""
    return db.query(Turma).all()


@router.get("/{turma_id}", response_model=TurmaResponse)
def obter_turma(
    turma_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtém detalhes de uma turma específica."""
    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return turma


@router.get("/{turma_id}/grade", status_code=status.HTTP_200_OK)
def listar_grade_turma(
    turma_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna a grade horária predefinida (matriz base) para uma turma específica ("§5.1. Grade Horária").
    Isso busca as aulas previstas, horários e disciplinas a partir do horario.csv inserido via ETL.
    """
    turma = db.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    # Import Grade and Disciplina to query the schedules
    from app.models.auxiliares import Grade, Disciplina
    
    # Query grades da turma, incluindo a disciplina
    grades = (
        db.query(Grade)
        .filter(Grade.turma_id == turma_id)
        .order_by(Grade.horario_inicio)
        .all()
    )

    resultado = []
    for g in grades:
        resultado.append({
            "id": str(g.id),
            "dia_semana": g.dia_semana,
            "horario_inicio": g.horario_inicio.strftime("%H:%M") if g.horario_inicio else None,
            "horario_fim": g.horario_fim.strftime("%H:%M") if g.horario_fim else None,
            "turno_aula": g.turno_aula,
            "canal_iptv": g.canal_iptv,
            "disciplina_id": str(g.disciplina_id) if g.disciplina_id else None,
            "disciplina_nome": g.disciplina.nome if g.disciplina else "N/A",
            "professor_id": str(g.professor_id) if getattr(g, "professor_id", None) else None,
            "professor_nome": getattr(g.professor, "nome", "N/A") if getattr(g, "professor_id", None) else "N/A",
            "is_gravacao": (g.horario_inicio.strftime("%H:%M") == "00:00") if g.horario_inicio else False
        })
    
    return resultado


class GradeCreate(BaseModel):
    disciplina_id: UUID
    dia_semana: str
    horario_inicio: str # "HH:MM"
    horario_fim: str    # "HH:MM"
    canal_iptv: Optional[int] = None

@router.post("/{turma_id}/grade", status_code=status.HTTP_201_CREATED)
def adicionar_grade_turma(
    turma_id: UUID,
    grade_in: GradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Adiciona manualmente um horário na grade da turma (§5.2)."""
    from app.models.auxiliares import Grade
    
    try:
        h_ini = datetime.strptime(grade_in.horario_inicio, "%H:%M").time()
        h_fim = datetime.strptime(grade_in.horario_fim, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de hora inválido. Use HH:MM.")

    # Inferência básica de turno (reaproveitando lógica do ETL se necessário, ou simplificando)
    minutos = h_ini.hour * 60 + h_ini.minute
    turno = "MANHÃ" if minutos < 720 else "TARDE" if minutos < 1100 else "NOITE"

    nova_grade = Grade(
        turma_id=turma_id,
        disciplina_id=grade_in.disciplina_id,
        dia_semana=grade_in.dia_semana,
        horario_inicio=h_ini,
        horario_fim=h_fim,
        turno_aula=turno,
        canal_iptv=grade_in.canal_iptv
    )
    db.add(nova_grade)
    db.commit()
    db.refresh(nova_grade)
    return nova_grade


@router.delete("/grade/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_grade_turma(
    grade_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Remove um slot da grade horária."""
    from app.models.auxiliares import Grade
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Slot não encontrado.")
    db.delete(grade)
    db.commit()
    return None