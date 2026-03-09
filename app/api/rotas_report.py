"""
Canal Educação v3.0 — Rotas de Relatórios de Aula (Class Reports).
CRUD completo com auto-preenchimento, validação relacional,
campos condicionais, Naming Engine, paginação server-side e exportação CSV.
"""

import csv
import io
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.auxiliares import Disciplina, Professor, ProfessorDisciplina
from app.models.class_report import ClassReport
from app.models.turma import Turma
from app.models.user import User
from app.schemas.class_report import (
    ClassReportCancel,
    ClassReportCreate,
    ClassReportResponse,
    PaginatedReportsResponse,
)
from app.services.naming_engine import (
    gerar_nome_padronizado,
    verificar_sufixo_geminada,
)

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Relatórios de Aula"],
)


# ─── Validação de Campos Condicionais ────────────────────────────────


def _validar_campos_condicionais(data: ClassReportCreate) -> None:
    """
    Valida campos condicionais conforme spec 3.C/3.D/3.E:
    - Se interação='Outras' → interacao_outras_desc obrigatório
    - Se recurso contém 'Outro' → recursos_outro_desc obrigatório
    - Se problema_material='Outros' → problema_material_outro_desc obrigatório
    - Se teve_substituicao → professor_substituto_id obrigatório
    - Se teve_atraso → minutos_atraso e observacao_atraso obrigatórios
    """
    if data.interacao_professor_aluno == "Outras" and not data.interacao_outras_desc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campo 'interacao_outras_desc' é obrigatório quando interação é 'Outras'.",
        )

    if data.tipo_recursos_utilizados and "Outro" in data.tipo_recursos_utilizados:
        if not data.recursos_outro_desc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campo 'recursos_outro_desc' é obrigatório quando recurso 'Outro' está selecionado.",
            )

    if data.problema_material == "Outros" and not data.problema_material_outro_desc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campo 'problema_material_outro_desc' é obrigatório quando problema é 'Outros'.",
        )

    if data.teve_substituicao and not data.professor_substituto_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campo 'professor_substituto_id' é obrigatório quando há substituição.",
        )

    if data.teve_atraso:
        if not data.minutos_atraso:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campo 'minutos_atraso' é obrigatório quando há atraso.",
            )
        if not data.observacao_atraso:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campo 'observacao_atraso' é obrigatório quando há atraso.",
            )


# ─── Validação Relacional Professor ↔ Disciplina ────────────────────


def _validar_professor_disciplina(
    db: Session, professor_id: UUID, disciplina_id: UUID
) -> None:
    """
    Compliance Crítico: Verifica se o professor está vinculado à disciplina.
    Apenas professores cadastrados para aquela disciplina podem ser selecionados.
    """
    vinculo = (
        db.query(ProfessorDisciplina)
        .filter(
            ProfessorDisciplina.professor_id == professor_id,
            ProfessorDisciplina.disciplina_id == disciplina_id,
        )
        .first()
    )

    if not vinculo:
        professor = db.query(Professor).filter(Professor.id == professor_id).first()
        disciplina = (
            db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
        )
        prof_nome = professor.nome if professor else str(professor_id)
        disc_nome = disciplina.nome if disciplina else str(disciplina_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Validação Relacional: Professor '{prof_nome}' não está "
                f"vinculado à disciplina '{disc_nome}'."
            ),
        )


# ─── Filtro Helper ───────────────────────────────────────────────────


def _apply_report_filters(query, **kwargs):
    """Aplica filtros ao query de relatórios (reutilizado em list e export)."""
    if kwargs.get("data_aula"):
        query = query.filter(ClassReport.data_aula == kwargs["data_aula"])
    if kwargs.get("data_inicio"):
        query = query.filter(ClassReport.data_aula >= kwargs["data_inicio"])
    if kwargs.get("data_fim"):
        query = query.filter(ClassReport.data_aula <= kwargs["data_fim"])
    if kwargs.get("turma_id"):
        query = query.filter(ClassReport.turma_id == kwargs["turma_id"])
    if kwargs.get("professor_id"):
        query = query.filter(ClassReport.professor_id == kwargs["professor_id"])
    if kwargs.get("disciplina_id"):
        query = query.filter(ClassReport.disciplina_id == kwargs["disciplina_id"])
    if kwargs.get("status_filter"):
        query = query.filter(ClassReport.status == kwargs["status_filter"].upper())
    if kwargs.get("estudio"):
        query = query.filter(ClassReport.estudio == kwargs["estudio"])
    if kwargs.get("tipo_aula"):
        query = query.filter(ClassReport.tipo_aula == kwargs["tipo_aula"])
    # Boolean occurrence filters (§5.3 — critical for audit)
    if kwargs.get("com_atraso") is True:
        query = query.filter(ClassReport.teve_atraso == True)  # noqa: E712
    if kwargs.get("com_substituicao") is True:
        query = query.filter(ClassReport.teve_substituicao == True)  # noqa: E712
    if kwargs.get("com_problema"):
        query = query.filter(ClassReport.problema_material != "Não")
    return query


# ─── CRUD ─────────────────────────────────────────────────────────────


@router.post("/", response_model=ClassReportResponse, status_code=status.HTTP_201_CREATED)
def criar_relatorio(
    data: ClassReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Cria um novo relatório de aula (status RASCUNHO).
    Auto-preenche os metadados e valida campos condicionais.
    """
    # 1. Validação das entidades referenciadas
    turma = db.query(Turma).filter(Turma.id == data.turma_id).first()
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    professor = db.query(Professor).filter(Professor.id == data.professor_id).first()
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado.")

    disciplina = (
        db.query(Disciplina).filter(Disciplina.id == data.disciplina_id).first()
    )
    if not disciplina:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada.")

    # 2. Validação relacional Professor ↔ Disciplina
    _validar_professor_disciplina(db, data.professor_id, data.disciplina_id)

    # 3. Validação de campos condicionais
    _validar_campos_condicionais(data)

    # 4. Criação do relatório
    report = ClassReport(
        created_by=current_user.id,
        status="RASCUNHO",
        **data.model_dump(),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


@router.patch("/{report_id}/finalizar", response_model=ClassReportResponse)
def finalizar_relatorio(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Finaliza o relatório: executa o Naming Engine e verifica aulas geminadas (P1/P2/P3).
    """
    report = db.query(ClassReport).filter(ClassReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")

    if report.status != "RASCUNHO":
        raise HTTPException(
            status_code=400,
            detail=f"Relatório com status '{report.status}' não pode ser finalizado.",
        )

    # Buscar turma para dados do naming engine
    turma = db.query(Turma).filter(Turma.id == report.turma_id).first()
    disciplina = (
        db.query(Disciplina).filter(Disciplina.id == report.disciplina_id).first()
    )

    # Gerar nome padronizado via Naming Engine
    nome_gerado = gerar_nome_padronizado(
        nomenclatura_turma=turma.nomenclatura_padrao or turma.nome,
        disciplina=disciplina.nome if disciplina else "",
        data_aula=report.data_aula,
        conteudo=report.conteudo_ministrado,
    )

    # Verificação de aulas geminadas (P1/P2/P3)
    aula_existente = (
        db.query(ClassReport)
        .filter(
            ClassReport.turma_id == report.turma_id,
            ClassReport.disciplina_id == report.disciplina_id,
            ClassReport.data_aula == report.data_aula,
            ClassReport.status == "FINALIZADO",
            ClassReport.id != report.id,
        )
        .first()
    )

    if aula_existente:
        if not verificar_sufixo_geminada(report.conteudo_ministrado):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Aula geminada detectada! Já existe uma aula finalizada para "
                    f"esta turma/disciplina/data. Adicione 'P1', 'P2' ou 'P3' ao "
                    "conteúdo ministrado para distinguir as aulas."
                ),
            )
        report.conflito_geminada_resolvido = True

    # Finaliza
    report.nome_ficheiro_gerado = nome_gerado
    report.status = "FINALIZADO"

    db.commit()
    db.refresh(report)

    # Dispara task assíncrona de compliance no Google Drive (§6)
    try:
        from app.tasks.worker import verificar_compliance_drive
        verificar_compliance_drive.delay(str(report.id), nome_gerado)
    except Exception as e:
        # Não bloqueia a finalização se o Celery/Redis não estiver disponível
        import logging
        logging.getLogger(__name__).warning(
            f"Não foi possível disparar verificação de compliance: {e}"
        )

    return report


@router.post("/force-sync-drive", status_code=status.HTTP_202_ACCEPTED)
def forcar_sincronizacao_drive(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Dispara varredura geral para forçar a sincronização de relatórios Pendentes.
    """
    from app.tasks.worker import sincronizacao_noturna_drive
    try:
        sincronizacao_noturna_drive.delay()
        return {"message": "Sincronização em massa enviada para a fila com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enfileirar task de sync: {str(e)}")


@router.patch("/{report_id}/cancelar", response_model=ClassReportResponse)
def cancelar_relatorio(
    report_id: UUID,
    cancel_data: ClassReportCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancela um relatório com justificativa obrigatória."""
    report = db.query(ClassReport).filter(ClassReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")

    if report.status == "CANCELADO":
        raise HTTPException(status_code=400, detail="Relatório já está cancelado.")

    report.status = "CANCELADO"
    report.observacoes = (
        f"CANCELADO por {current_user.full_name}: {cancel_data.justificativa}"
    )

    db.commit()
    db.refresh(report)

    return report


@router.get("/", response_model=PaginatedReportsResponse)
def listar_relatorios(
    data_aula: Optional[date] = Query(None),
    data_inicio: Optional[date] = Query(None, description="Filtro período início"),
    data_fim: Optional[date] = Query(None, description="Filtro período fim"),
    turma_id: Optional[UUID] = Query(None),
    professor_id: Optional[UUID] = Query(None),
    disciplina_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    estudio: Optional[str] = Query(None),
    tipo_aula: Optional[str] = Query(None),
    com_atraso: Optional[bool] = Query(None, description="Filtrar com atraso"),
    com_substituicao: Optional[bool] = Query(None, description="Filtrar com substituição"),
    com_problema: Optional[bool] = Query(None, description="Filtrar com problema técnico"),
    sort_by: str = Query("data_aula", description="Campo de ordenação: data_aula ou created_at"),
    sort_order: str = Query("desc", description="Ordem: asc ou desc"),
    limit: int = Query(50, ge=1, le=200, description="Itens por página"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lista relatórios com paginação server-side (§5.3).
    Padrão: 50 por página, ordenação decrescente por data_aula.
    """
    query = db.query(ClassReport)

    # Aplicar filtros
    query = _apply_report_filters(
        query,
        data_aula=data_aula,
        data_inicio=data_inicio,
        data_fim=data_fim,
        turma_id=turma_id,
        professor_id=professor_id,
        disciplina_id=disciplina_id,
        status_filter=status_filter,
        estudio=estudio,
        tipo_aula=tipo_aula,
        com_atraso=com_atraso,
        com_substituicao=com_substituicao,
        com_problema=com_problema,
    )

    # Contagem total (antes da paginação)
    total = query.count()

    # Ordenação
    sort_column = ClassReport.created_at if sort_by == "created_at" else ClassReport.data_aula
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Paginação
    items = query.offset(offset).limit(limit).all()

    return PaginatedReportsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/export")
def exportar_relatorios(
    data_aula: Optional[date] = Query(None),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    turma_id: Optional[UUID] = Query(None),
    professor_id: Optional[UUID] = Query(None),
    disciplina_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    estudio: Optional[str] = Query(None),
    tipo_aula: Optional[str] = Query(None),
    com_atraso: Optional[bool] = Query(None),
    com_substituicao: Optional[bool] = Query(None),
    com_problema: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Exporta relatórios em CSV respeitando filtros ativos (§5.3).
    Usado para fecho de faturamento e relatórios gerenciais.
    """
    query = db.query(ClassReport)

    query = _apply_report_filters(
        query,
        data_aula=data_aula,
        data_inicio=data_inicio,
        data_fim=data_fim,
        turma_id=turma_id,
        professor_id=professor_id,
        disciplina_id=disciplina_id,
        status_filter=status_filter,
        estudio=estudio,
        tipo_aula=tipo_aula,
        com_atraso=com_atraso,
        com_substituicao=com_substituicao,
        com_problema=com_problema,
    )

    reports = query.order_by(ClassReport.data_aula.desc()).all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Header
    writer.writerow([
        "ID", "Status", "Data Aula", "Turno", "Estúdio", "Turma ID",
        "Disciplina ID", "Professor ID", "Horário", "Regular",
        "Tipo Aula", "Canal", "Conteúdo Ministrado",
        "Interação", "Atividade Prática",
        "Recursos", "Problema Material",
        "Substituição", "Professor Substituto ID",
        "Atraso", "Minutos Atraso", "Obs. Atraso",
        "Nome Ficheiro", "Geminada Resolvida",
        "Criado Por", "Criado Em", "Observações",
    ])

    for r in reports:
        writer.writerow([
            str(r.id), r.status, str(r.data_aula), r.turno, r.estudio,
            str(r.turma_id), str(r.disciplina_id), str(r.professor_id),
            r.horario_aula, r.regular,
            r.tipo_aula, r.canal_utilizado, r.conteudo_ministrado,
            r.interacao_professor_aluno, r.atividade_pratica or "",
            ",".join(r.tipo_recursos_utilizados) if r.tipo_recursos_utilizados else "",
            r.problema_material,
            "Sim" if r.teve_substituicao else "Não",
            str(r.professor_substituto_id) if r.professor_substituto_id else "",
            "Sim" if r.teve_atraso else "Não",
            str(r.minutos_atraso) if r.minutos_atraso else "",
            r.observacao_atraso or "",
            r.nome_ficheiro_gerado or "",
            "Sim" if r.conflito_geminada_resolvido else "Não",
            str(r.created_by), str(r.created_at),
            r.observacoes or "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=relatorios_{date.today().isoformat()}.csv"
        },
    )


@router.get("/{report_id}", response_model=ClassReportResponse)
def obter_relatorio(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtém detalhes de um relatório específico."""
    report = db.query(ClassReport).filter(ClassReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return report


# ─── Endpoints Auxiliares (Lookup Data) ──────────────────────────────


@router.get("/lookup/professores-por-disciplina/{disciplina_id}")
def listar_professores_por_disciplina(
    disciplina_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna apenas os professores vinculados a uma disciplina específica.
    Usado pelo frontend para preencher o dropdown de professores.
    """
    professores = (
        db.query(Professor)
        .join(ProfessorDisciplina)
        .filter(ProfessorDisciplina.disciplina_id == disciplina_id)
        .all()
    )
    return [{"id": str(p.id), "nome": p.nome} for p in professores]


@router.get("/lookup/disciplinas")
def listar_disciplinas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retorna todas as disciplinas cadastradas."""
    disciplinas = db.query(Disciplina).order_by(Disciplina.nome).all()
    return [{"id": str(d.id), "nome": d.nome} for d in disciplinas]


@router.get("/lookup/professores")
def listar_professores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retorna todos os professores cadastrados."""
    professores = db.query(Professor).order_by(Professor.nome).all()
    return [{"id": str(p.id), "nome": p.nome} for p in professores]
