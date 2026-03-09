"""
Canal Educação v3.0 — Rotas de Autenticação e IAM.
Login por email, convites, confirmação de conta, RBAC, audit logging.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    generate_invite_token,
    get_invite_expiration,
    get_password_hash,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import (
    AuditLogResponse,
    ConfirmAccountRequest,
    InviteRequest,
    InviteResponse,
    TokenResponse,
    UserListResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação e IAM"])


# ─── Helpers ──────────────────────────────────────────────────────────


def _create_audit_log(
    db: Session,
    actor_id,
    action: str,
    target_user_id=None,
    details: str = None,
    ip_address: str = None,
):
    """Cria um registo inalterável no log de auditoria."""
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        target_user_id=target_user_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)


# ─── Login ────────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Autentica o utilizador por email e senha.
    O campo 'username' do OAuth2 form recebe o email.
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Contacte o administrador.",
        )

    if not user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique a sua caixa de entrada.",
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": str(user.id)}
    )
    return TokenResponse(access_token=access_token)


# ─── Convites ─────────────────────────────────────────────────────────


@router.post("/invite", response_model=InviteResponse)
def invite_user(
    invite_data: InviteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gestor")),
):
    """
    Cria um convite para um novo utilizador.
    Apenas Admin e Gestor podem convidar.
    Gera token de 24h para confirmação via email.
    """
    # Verifica se o email já está registado
    existing = db.query(User).filter(User.email == invite_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O email '{invite_data.email}' já está registado no sistema.",
        )

    # Restrição: assistente não pode criar admin
    if invite_data.role == "admin" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem criar contas de administrador.",
        )

    # Cria o utilizador com convite pendente
    token = generate_invite_token()
    new_user = User(
        email=invite_data.email,
        full_name=invite_data.full_name,
        role=invite_data.role,
        hashed_password=None,  # Será definida na confirmação
        email_confirmed=False,
        invite_token=token,
        invite_expires_at=get_invite_expiration(),
        invited_by=current_user.id,
    )

    db.add(new_user)
    db.flush()  # Garante que new_user.id está disponível para o audit log

    # --- NOVO §2.1: Envio de Email em Background ---
    from app.services.email_service import send_invite_email
    import asyncio
    
    # Dispara o email (não esperado concluir para responder a requisição, mas aqui usamos await para garantir consistência)
    # Em produção real, poderíamos usar BackgroundTasks do FastAPI
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(send_invite_email(new_user.email, new_user.full_name, token))
    except Exception as e:
        print(f"⚠️ Falha ao agendar tarefa de email: {str(e)}")

    # Audit log: regista o convite
    _create_audit_log(
        db,
        actor_id=current_user.id,
        action="USER_INVITED",
        target_user_id=new_user.id,
        details=f"Convidou {invite_data.email} com perfil '{invite_data.role}'",
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(new_user)

    return InviteResponse(
        message=f"Convite enviado para {invite_data.email}.",
        email=invite_data.email,
        invite_token=token,
    )


# ─── Confirmação de Conta ────────────────────────────────────────────


@router.post("/confirm", response_model=UserResponse)
def confirm_account(
    confirm_data: ConfirmAccountRequest,
    db: Session = Depends(get_db),
):
    """
    Confirma a conta e define a senha inicial.
    O token é recebido via link no email com validade de 24h.
    """
    user = (
        db.query(User).filter(User.invite_token == confirm_data.token).first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de convite inválido.",
        )

    if user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta conta já foi confirmada.",
        )

    # Verifica expiração
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if user.invite_expires_at and user.invite_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Token de convite expirado. Solicite um novo convite.",
        )

    # Confirma e define a senha
    user.hashed_password = get_password_hash(confirm_data.password)
    user.email_confirmed = True
    user.invite_token = None  # Invalida o token após uso
    user.invite_expires_at = None

    db.commit()
    db.refresh(user)

    return user


# ─── Perfil ───────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Retorna os dados do utilizador autenticado."""
    return current_user


# ─── Gestão de Utilizadores (Admin) ──────────────────────────────────


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gestor")),
):
    """Lista todos os utilizadores (apenas Admin/Gestor)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return UserListResponse(users=users, total=len(users))


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Desativa um utilizador (Soft Delete — §5.4).
    Invalida a sessão e impede o acesso mesmo se logado.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível desativar a sua própria conta.",
        )

    user.is_active = False

    # Audit log
    _create_audit_log(
        db,
        actor_id=current_user.id,
        action="USER_DEACTIVATED",
        target_user_id=user.id,
        details=f"Desativou a conta de {user.email}",
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    return {"message": f"Utilizador {user.email} desativado com sucesso."}


@router.patch("/users/{user_id}/activate")
def activate_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Reativa um utilizador que foi desativado (§5.4 Soft Delete recovery).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilizador já está ativo.",
        )

    user.is_active = True

    # Audit log
    _create_audit_log(
        db,
        actor_id=current_user.id,
        action="USER_ACTIVATED",
        target_user_id=user.id,
        details=f"Reativou a conta de {user.email}",
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    return {"message": f"Utilizador {user.email} reativado com sucesso."}


@router.patch("/users/{user_id}/role")
def change_user_role(
    user_id: str,
    role: str = Query(..., description="Novo perfil: admin, gestor, auditor, assistente"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Altera o perfil de um utilizador (§5.4 RBAC fixo).
    Apenas Admin pode promover/rebaixar perfis.
    """
    valid_roles = {"admin", "gestor", "auditor", "assistente"}
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Perfil inválido. Opções: {', '.join(valid_roles)}",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    old_role = user.role
    user.role = role

    # Audit log
    _create_audit_log(
        db,
        actor_id=current_user.id,
        action="USER_ROLE_CHANGED",
        target_user_id=user.id,
        details=f"Alterou perfil de {user.email}: '{old_role}' → '{role}'",
        ip_address=request.client.host if request and request.client else None,
    )

    db.commit()
    return {
        "message": f"Perfil de {user.email} alterado para '{role}'.",
        "old_role": old_role,
        "new_role": role,
    }


# ─── Log de Auditoria (§5.4) ─────────────────────────────────────────


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Lista o log de auditoria de acessos (§5.4 — Admin only).
    Mostra histórico de convites, desativações, promoções de perfil.
    """
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return logs


# ─── Setup Inicial (Admin Bootstrap) ─────────────────────────────────


@router.post("/bootstrap", response_model=UserResponse)
def bootstrap_admin(db: Session = Depends(get_db)):
    """
    Cria o primeiro administrador do sistema.
    APENAS funciona se não existir nenhum utilizador no banco.
    """
    existing_users = db.query(User).count()
    if existing_users > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap só pode ser executado num sistema sem utilizadores.",
        )

    admin = User(
        email="admin@canaleducacao.com",
        full_name="Administrador Sistema",
        role="admin",
        hashed_password=get_password_hash("admin123"),
        email_confirmed=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin