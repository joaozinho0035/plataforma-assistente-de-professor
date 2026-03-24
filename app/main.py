"""
Canal Educação v3.0 — Aplicação Principal FastAPI.
Registra todas as rotas, middleware, CORS, WebSockets, e templates.
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base, engine, get_db
from app.domain.exceptions.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolation,
    ConflictException,
    DomainException,
    EntityNotFoundException,
)

# Importa todos os modelos para garantir que as tabelas sejam criadas
from app.models import (  # noqa: F401
    AuditLog,
    ClassReport,
    Disciplina,
    Grade,
    Professor,
    ProfessorDisciplina,
    Turma,
    Unit,
    User,
)

# Rotas
from app.api.rotas_auth import router as auth_router
from app.api.rotas_report import router as report_router
from app.api.rotas_turma import router as turma_router
from app.api.rotas_live import router as live_router
from app.api.websocket.rotas_grade_ws import router as ws_router

settings = get_settings()

# ─── Criação da App ──────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Gestão de Relatórios de Aula — Canal Educação v3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Criação das Tabelas ─────────────────────────────────────────────

Base.metadata.create_all(bind=engine)

# ─── Static Files & Templates ────────────────────────────────────────

import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

# Cria diretórios se não existirem
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# ─── Error Handling Middleware ────────────────────────────────────────


@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(ConflictException)
async def conflict_handler(request: Request, exc: ConflictException):
    return JSONResponse(
        status_code=409,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(BusinessRuleViolation)
async def business_rule_handler(request: Request, exc: BusinessRuleViolation):
    return JSONResponse(
        status_code=422,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(AuthorizationError)
async def authz_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(
        status_code=403,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(DomainException)
async def domain_error_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "detail": exc.message},
    )


# ─── Registro das Rotas ──────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(turma_router)
app.include_router(report_router)
app.include_router(live_router)
app.include_router(ws_router)


# ─── Health Check ─────────────────────────────────────────────────────


@app.get("/ping")
def health_check():
    return {
        "status": "online",
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME,
    }


# ─── Frontend Pages (Jinja2) ─────────────────────────────────────────


@app.get("/")
def index(request: Request):
    """Redireciona para login ou dashboard."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/grade")
def grade_page(request: Request):
    return templates.TemplateResponse("grade.html", {"request": request})


@app.get("/report")
def report_page(request: Request):
    return templates.TemplateResponse("report_form.html", {"request": request})


@app.get("/reports-audit")
def reports_audit_page(request: Request):
    """Tela de Relatórios e Auditoria (§5.3)."""
    return templates.TemplateResponse("reports_audit.html", {"request": request})


@app.get("/admin/users")
def admin_users_page(request: Request):
    return templates.TemplateResponse("admin_users.html", {"request": request})


@app.get("/confirm")
def confirm_page(request: Request):
    return templates.TemplateResponse("confirm.html", {"request": request})


@app.get("/live-monitor")
def live_monitor_page(request: Request, db: Session = Depends(get_db)):
    """Tela de Live Monitor NOC (§5.5)."""
    from app.models.turma import Turma
    from app.models.auxiliares import Grade
    from sqlalchemy import distinct
    import datetime
    
    turmas = db.query(Turma).order_by(Turma.nomenclatura_padrao).all()
    
    # Buscar horários reais da grade (distintos) em vez de range fixo
    horarios_db = (
        db.query(distinct(Grade.horario_inicio))
        .filter(Grade.horario_inicio != None)
        .order_by(Grade.horario_inicio)
        .all()
    )
    
    # Filtrar horários dummy (00:00 = GRAVAÇÃO) e formatar
    horarios = []
    for (h,) in horarios_db:
        formatted = h.strftime("%H:%M")
        if formatted != "00:00":  # Exclui GRAVAÇÃO
            horarios.append(formatted)
    
    # Fallback se não houver horários na base
    if not horarios:
        horarios = [f"{h:02d}:00" for h in range(7, 22)]
    
    estudios = [f"Estúdio {i:02d}" for i in range(1, 10)] + ["Externo"]
    today_formatted = datetime.date.today().strftime("%d de %B, %Y")

    return templates.TemplateResponse("live_monitor.html", {
        "request": request,
        "turmas": turmas,
        "horarios": horarios,
        "estudios": estudios,
        "today_formatted": today_formatted
    })