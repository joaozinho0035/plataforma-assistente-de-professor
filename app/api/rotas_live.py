from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.auxiliares import Grade, Disciplina, Professor
from app.models.class_report import ClassReport
from app.models.turma import Turma
from app.models.user import User

router = APIRouter(prefix="/api/v1/live", tags=["Live Monitor Operations"])

@router.get("/matrix")
def get_live_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna os dados consolidados para a matriz operacional do Live Monitor.
    Cruza dados da Grade base com o status dos Relatórios de hoje.
    """
    hoje = date.today()
    dia_semana_map = {
        0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
        4: "Sexta", 5: "Sábado", 6: "Domingo"
    }
    dia_atual = dia_semana_map[hoje.weekday()]

    # 1. Busca a grade base para o dia de hoje
    # No sistema do Canal Educação, a grade define qual turma/disc está em qual estúdio em qual hora.
    # Assumimos que o estúdio está vinculado à grade ou à turma (a spec 5.5 diz Interseção Estúdio vs Horário).
    
    # Busca todos os relatórios de hoje para ver o status real
    relatorios = db.query(ClassReport).filter(ClassReport.data_aula == hoje).all()
    relatorios_map = {
        (str(r.turma_id), str(r.disciplina_id), r.horario_aula): r.status 
        for r in relatorios
    }

    # Busca a grade para o dia da semana atual
    grades = (
        db.query(Grade, Turma, Disciplina, Professor)
        .join(Turma, Grade.turma_id == Turma.id)
        .join(Disciplina, Grade.disciplina_id == Disciplina.id)
        .outerjoin(Professor, Grade.professor_id == Professor.id)
        .filter(Grade.dia_semana == dia_atual)
        .all()
    )

    result = []
    for grade, turma, disc, prof in grades:
        # Formata o horário de início para o frontend (e.g., "07:30 às 08:30" virou "07:30")
        h_inicio = grade.horario_inicio.strftime("%H:%M")
        h_fim = grade.horario_fim.strftime("%H:%M")
        horario_completo = f"{h_inicio} às {h_fim}"
        
        # O estúdio costuma vir de onde? A spec 5.1/5.5 sugere que está na grade ou no relatório.
        # Vamos usar o 'estudio' que o usuário preenche no relatório, ou um default da grade se houver.
        # Se não houver relatório, como sabemos o estúdio? 
        # Baseado na descrição do CSV original, IPTV 1 = Estúdio 01.
        estudio_numero = grade.canal_iptv if grade.canal_iptv else 1
        estudio_nome = f"Estúdio {estudio_numero:02d}"

        # Verifica status no mapa de relatórios (ID Turma + ID Disc + String Horário)
        # Nota: O match de horário_aula no relatório pode ser sensível a strings. 
        # Recomenda-se usar caminhos de ID se possível, mas aqui usamos o que temos.
        status = relatorios_map.get((str(turma.id), str(disc.id), horario_completo), "PENDENTE")

        result.append({
            "estudio": estudio_nome,
            "horario_inicio": h_inicio,
            "turma_id": str(turma.id),
            "turma_nome": turma.nomenclatura_padrao,
            "disciplina_nome": disc.nome,
            "professor_nome": prof.nome if prof else "N/A",
            "status": status
        })

    return result
