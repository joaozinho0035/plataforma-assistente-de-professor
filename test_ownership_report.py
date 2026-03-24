import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from fastapi import HTTPException

from app.api.rotas_report import cancelar_relatorio
from app.models.class_report import ClassReport
from app.models.user import User
from app.schemas.class_report import ClassReportCancel

def test_rbac_ownership_cancelamento_relatorio():
    user_a_id = uuid4()
    user_b_id = uuid4()
    user_admin_id = uuid4()
    report_id = uuid4()

    # Usuário A: O Criador do Relatório (Assistente)
    user_a = User(id=user_a_id, role="assistente", full_name="Assistente A")
    
    # Usuário B: Outro Assistente ("Atacante")
    user_b = User(id=user_b_id, role="assistente", full_name="Assistente B")
    
    # Usuário C: Administrador/Gestor (Privilegiado)
    user_admin = User(id=user_admin_id, role="admin", full_name="Admin C")

    # Mock do Banco populando o relatório do Usuário A
    report_mock = ClassReport(
        id=report_id,
        created_by=user_a_id,
        status="RASCUNHO"
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = report_mock

    payload_cancel = ClassReportCancel(justificativa="Teste de Titularidade QA")

    # CENÁRIO 1: Usuário B (Assistente) tenta cancelar o relatório do Usuário A -> DEVE FALHAR (403)
    with pytest.raises(HTTPException) as exc_info:
        cancelar_relatorio(report_id=report_id, cancel_data=payload_cancel, db=mock_db, current_user=user_b)
    
    assert exc_info.value.status_code == 403
    assert "Assistentes só podem cancelar relatórios criados por eles mesmos" in exc_info.value.detail

    # CENÁRIO 2: Usuário C (Admin) tenta cancelar o mesmo relatório do Usuário A -> DEVE PASSAR OK (200)
    res_admin = cancelar_relatorio(report_id=report_id, cancel_data=payload_cancel, db=mock_db, current_user=user_admin)
    assert res_admin.status == "CANCELADO"

    # Reset do mock para o próximo teste
    report_mock.status = "RASCUNHO"

    # CENÁRIO EXTRA: Usuário A (Assistente e Dono) tenta cancelar seu PRÓPRIO relatório -> DEVE PASSAR OK (200)
    res_dono = cancelar_relatorio(report_id=report_id, cancel_data=payload_cancel, db=mock_db, current_user=user_a)
    assert res_dono.status == "CANCELADO"
