"""
Canal Educação v3.0 — Schemas de Autenticação (DTOs Pydantic).
Login, Tokens, Convites, Confirmação, Audit Log.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InviteRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "assistente"  # admin, gestor, auditor, assistente


class InviteResponse(BaseModel):
    message: str
    email: str
    invite_token: str


class ConfirmAccountRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    email_confirmed: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class AuditLogResponse(BaseModel):
    """Response para log de auditoria (§5.4)."""
    id: UUID
    actor_id: UUID
    action: str
    target_user_id: Optional[UUID] = None
    details: Optional[str] = None
    created_at: datetime
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True
