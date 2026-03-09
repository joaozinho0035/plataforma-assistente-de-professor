from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from jose import jwt, JWTError
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.lesson import Lesson
from app.models.turma import Turma
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonResponse, LessonCancel

# Configuração da Autenticação via JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Valida o token e retorna o utilizador logado."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

router = APIRouter(prefix="/aulas", tags=["Gestão de Aulas (Relatórios)"])

@router.post("/", response_model=LessonResponse)
def registrar_aula(
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registra uma nova aula com o Naming Engine de Fluxo Contínuo (Sem Hifens).
    Padrão: [TURMA] [DISCIPLINA] [DD MM YY] [CONTEUDO]
    """
    # 1. Valida se a turma existe
    turma = db.query(Turma).filter(Turma.id == lesson.turma_id).first()
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    # 2. MOTOR DE NOMENCLATURA (NAMING ENGINE ATUALIZADO)
    prefixo = turma.nomenclatura_padrao if turma.nomenclatura_padrao else f"{turma.serie_modulo} {turma.turno}"
    disc = lesson.disciplina.upper().strip()
    data_formatada = lesson.data_aula.strftime("%d %m %y")
    conteudo_clean = lesson.conteudo.upper().strip()
    
    nome_gerado = f"{prefixo} {disc} {data_formatada} {conteudo_clean}"
    
    if lesson.bloco:
         nome_gerado += f" {lesson.bloco}"

    # 3. VERIFICAÇÃO DE CONFLITO
    aula_existente = db.query(Lesson).filter(Lesson.nome_padronizado == nome_gerado).first()
    if aula_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflito: A aula '{nome_gerado}' já existe."
        )

    # 4. GRAVAÇÃO
    nova_aula = Lesson(
        turma_id=lesson.turma_id,
        disciplina=disc,
        data_aula=lesson.data_aula,
        conteudo=lesson.conteudo,
        bloco=lesson.bloco,
        canal_iptv=lesson.canal_iptv, 
        status_transmissao=lesson.status_transmissao,
        status_compliance=lesson.status_compliance,
        is_draft=lesson.is_draft,
        is_locked=lesson.is_locked,
        observacoes_gerais=lesson.observacoes_gerais,
        nome_padronizado=nome_gerado,
        criado_por=current_user.id
    )

    db.add(nova_aula)
    try:
        db.commit()
        db.refresh(nova_aula)
        
        # Dispara o robô do Google Drive
        from app.tasks.worker import verificar_compliance_drive
        verificar_compliance_drive.delay(str(nova_aula.id), nome_gerado)
        
        return nova_aula
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro de integridade no banco de dados.")

@router.get("/", response_model=List[LessonResponse])
def listar_aulas(db: Session = Depends(get_db)):
    """Lista todas as aulas registradas no sistema."""
    return db.query(Lesson).all()

@router.get("/{lesson_id}", response_model=LessonResponse)
def obter_aula(lesson_id: UUID, db: Session = Depends(get_db)):
    """
    Busca os detalhes de uma aula específica pelo ID (lesson_id).
    """
    aula = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    return aula

@router.patch("/{lesson_id}/cancelar", response_model=LessonResponse)
def cancelar_aula(
    lesson_id: UUID,
    cancel_data: LessonCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancela uma aula e registra a justificativa com auditoria (RBAC).
    """
    aula = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada para cancelamento.")
    
    if aula.status_transmissao == "cancelada":
        raise HTTPException(status_code=400, detail="Esta aula já se encontra cancelada.")

    # Registro de Auditoria: Quem cancelou e porquê
    justificativa_final = f"Cancelado por {current_user.full_name}: {cancel_data.justificativa}"
    
    aula.status_transmissao = "cancelada"
    aula.status_compliance = "cinza" # Status visual de cancelado
    aula.justificativa_cancelamento = justificativa_final
    
    db.commit()
    db.refresh(aula)
    return aula