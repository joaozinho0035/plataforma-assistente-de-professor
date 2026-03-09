"""
Canal Educação v3.0 — Test Configuration (conftest.py)
Fixtures for test database, client, and authentication.
Uses SQLite with proper UUID handling for cross-dialect compatibility.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, String, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Override environment BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.auxiliares import Professor, Disciplina, ProfessorDisciplina
from app.models.turma import Turma
from app.models.audit_log import AuditLog

# ── SQLite Test Engine ───────────────────────────────────────────────
# Use in-memory SQLite with UUID columns treated as VARCHAR(32)

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Patch UUID for SQLite compatibility ──────────────────────────────
# SQLAlchemy's PG UUID type can't render on SQLite. We intercept it.

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

@event.listens_for(engine, "connect")
def _set_sqlite_uuid(dbapi_connection, connection_record):
    pass  # No-op, SQLite handles UUID as TEXT/VARCHAR


# Override column type rendering for SQLite
from sqlalchemy import types

class _SQLiteUUID(types.TypeDecorator):
    impl = types.String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(36))


# Monkey-patch PG_UUID to work in SQLite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(PG_UUID, "sqlite")
def _compile_pg_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"



# Now safely import the app (which triggers Base.metadata.create_all on PostgreSQL engine, 
# but we'll recreate using our SQLite engine in fixtures)
from app.main import app

app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop ALL tables for each test (clean slate)."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Direct database session for seeding test data."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db_session):
    """Confirmed admin user."""
    user = User(
        email="admin@test.com",
        full_name="Admin Test",
        role="admin",
        hashed_password=get_password_hash("admin123"),
        email_confirmed=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(
        data={
            "sub": admin_user.email,
            "role": admin_user.role,
            "user_id": str(admin_user.id),
        }
    )


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def assistant_user(db_session):
    """Confirmed assistant user."""
    user = User(
        email="assistant@test.com",
        full_name="Assistant Test",
        role="assistente",
        hashed_password=get_password_hash("assist123"),
        email_confirmed=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def assistant_token(assistant_user):
    return create_access_token(
        data={
            "sub": assistant_user.email,
            "role": assistant_user.role,
            "user_id": str(assistant_user.id),
        }
    )


@pytest.fixture
def assistant_headers(assistant_token):
    return {"Authorization": f"Bearer {assistant_token}"}


@pytest.fixture
def sample_turma(db_session):
    """Sample turma for report tests."""
    turma = Turma(
        nome="EM 1 TIM - MANHÃ",
        modalidade="REGULAR",
        serie_modulo="1ª Série",
        turno="MANHÃ",
        nomenclatura_padrao="EM 1 TIM",
    )
    db_session.add(turma)
    db_session.commit()
    db_session.refresh(turma)
    return turma


@pytest.fixture
def sample_professor_disciplina(db_session):
    """Professor + Disciplina + M:N link."""
    prof = Professor(nome="João Silva")
    disc = Disciplina(nome="MATEMÁTICA", nomenclatura_padrao="MAT")
    db_session.add(prof)
    db_session.add(disc)
    db_session.flush()

    link = ProfessorDisciplina(professor_id=prof.id, disciplina_id=disc.id)
    db_session.add(link)
    db_session.commit()
    db_session.refresh(prof)
    db_session.refresh(disc)

    return {"professor": prof, "disciplina": disc}
