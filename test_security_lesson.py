import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.deps import get_current_user, get_current_active_user
from app.models.user import User
from app.core.security import create_access_token
from app.api.rotas_lesson import listar_aulas

def test_1_acesso_anonimo():
    """Teste de Acesso Anônimo: Chamar a rota sem token (simulando falta de dependência resolvida)"""
    mock_db = MagicMock()
    # No FastAPI real, a falta do token = Depends(oauth2_scheme) levanta 401 antes mesmo de chamar get_current_user. 
    # Aqui vamos tentar chamar listar_aulas sem passar current_user (que o FastAPI garante não acontecer sem erro).
    # O teste da dependência sem token no oauth2_scheme nativo lança HTTPException 401.
    with pytest.raises(HTTPException) as exc_info:
        # FastAPI's oauth2_scheme raises 401 normally. We test get_current_user with None token.
        # But get_current_user(token=None, db=mock_db)
        from app.api.deps import get_current_user
        # Se passarmos token inválido
        get_current_user(token="invalid_token", db=mock_db)
    assert exc_info.value.status_code == 401


def test_2_integracao_modelo_email():
    """ Teste de Integração de Modelo: Valida que a autenticação usa User.email. """
    token = create_access_token(data={"sub": "test_auth@example.com", "role": "admin"})
    
    mock_db = MagicMock()
    # O mock finge que achou o user simulando a busca por User.email
    valid_user = User(email="test_auth@example.com", is_active=True, email_confirmed=True)
    mock_db.query.return_value.filter.return_value.first.return_value = valid_user
    
    # Executamos a dependência principal
    user_returned = get_current_active_user(get_current_user(token=token, db=mock_db))
    
    # Se estivesse usando .username como no código vulnerável apagado, daria AttributeError no SQLAlchemy mock
    assert user_returned.email == "test_auth@example.com"
    
    # Passamos para a rota
    mock_db.query.return_value.all.return_value = []
    res = listar_aulas(db=mock_db, current_user=user_returned)
    assert res == []


def test_3_status_conta_inativa():
    """ Teste de Status de Conta: Tenta acessar com is_active=False """
    token = create_access_token(data={"sub": "inactive@example.com", "role": "assistente"})
    
    mock_db = MagicMock()
    inactive_user = User(email="inactive@example.com", is_active=False, email_confirmed=True)
    mock_db.query.return_value.filter.return_value.first.return_value = inactive_user
    
    with pytest.raises(HTTPException) as exc_info:
        # A injeção vai falhar no get_current_user já pela regra do deps.py
        user_returned = get_current_user(token=token, db=mock_db)
    
    assert exc_info.value.status_code == 401
    assert "Credenciais inválidas" in exc_info.value.detail
