"""
Canal Educação v3.0 — Tests: Reports (Class Reports)
Integration tests for CRUD, validation, conditional fields, naming engine.
"""

from datetime import date


class TestCreateReport:

    def test_create_report_success(
        self, client, admin_headers, sample_turma, sample_professor_disciplina
    ):
        prof = sample_professor_disciplina["professor"]
        disc = sample_professor_disciplina["disciplina"]

        res = client.post(
            "/api/v1/reports/",
            json={
                "data_aula": "2026-03-15",
                "turno": "Manhã",
                "estudio": "Estúdio 01",
                "turma_id": str(sample_turma.id),
                "disciplina_id": str(disc.id),
                "professor_id": str(prof.id),
                "horario_aula": "07:30 - 08:30",
                "regular": "Sim",
                "tipo_aula": "Transmissão ao vivo",
                "canal_utilizado": "1",
                "conteudo_ministrado": "Funções do primeiro grau",
            },
            headers=admin_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "RASCUNHO"
        assert data["conteudo_ministrado"] == "Funções do primeiro grau"

    def test_create_report_unauthenticated(self, client):
        res = client.post("/api/v1/reports/", json={})
        assert res.status_code == 401


class TestConditionalFields:

    def test_interacao_outras_requires_desc(
        self, client, admin_headers, sample_turma, sample_professor_disciplina
    ):
        prof = sample_professor_disciplina["professor"]
        disc = sample_professor_disciplina["disciplina"]

        res = client.post(
            "/api/v1/reports/",
            json={
                "data_aula": "2026-03-15",
                "turno": "Manhã",
                "estudio": "Estúdio 01",
                "turma_id": str(sample_turma.id),
                "disciplina_id": str(disc.id),
                "professor_id": str(prof.id),
                "horario_aula": "07:30 - 08:30",
                "tipo_aula": "Gravação estúdio",
                "canal_utilizado": "1",
                "conteudo_ministrado": "Teste",
                "interacao_professor_aluno": "Outras",
                # Missing interacao_outras_desc!
            },
            headers=admin_headers,
        )
        assert res.status_code == 422

    def test_atraso_requires_minutos_and_obs(
        self, client, admin_headers, sample_turma, sample_professor_disciplina
    ):
        prof = sample_professor_disciplina["professor"]
        disc = sample_professor_disciplina["disciplina"]

        res = client.post(
            "/api/v1/reports/",
            json={
                "data_aula": "2026-03-15",
                "turno": "Manhã",
                "estudio": "Estúdio 01",
                "turma_id": str(sample_turma.id),
                "disciplina_id": str(disc.id),
                "professor_id": str(prof.id),
                "horario_aula": "07:30 - 08:30",
                "tipo_aula": "Gravação estúdio",
                "canal_utilizado": "1",
                "conteudo_ministrado": "Teste",
                "teve_atraso": True,
                # Missing minutos_atraso and observacao_atraso!
            },
            headers=admin_headers,
        )
        assert res.status_code == 422


class TestConteudoValidation:

    def test_conteudo_over_100_chars(
        self, client, admin_headers, sample_turma, sample_professor_disciplina
    ):
        prof = sample_professor_disciplina["professor"]
        disc = sample_professor_disciplina["disciplina"]

        res = client.post(
            "/api/v1/reports/",
            json={
                "data_aula": "2026-03-15",
                "turno": "Manhã",
                "estudio": "Estúdio 01",
                "turma_id": str(sample_turma.id),
                "disciplina_id": str(disc.id),
                "professor_id": str(prof.id),
                "horario_aula": "07:30 - 08:30",
                "tipo_aula": "Gravação estúdio",
                "canal_utilizado": "1",
                "conteudo_ministrado": "A" * 101,
            },
            headers=admin_headers,
        )
        assert res.status_code == 422


class TestListReports:

    def test_list_reports_empty(self, client, admin_headers):
        res = client.get("/api/v1/reports/", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["items"] == []

    def test_list_reports_with_filters(
        self, client, admin_headers, sample_turma, sample_professor_disciplina
    ):
        prof = sample_professor_disciplina["professor"]
        disc = sample_professor_disciplina["disciplina"]

        # Create a report first
        client.post(
            "/api/v1/reports/",
            json={
                "data_aula": "2026-03-15",
                "turno": "Manhã",
                "estudio": "Estúdio 01",
                "turma_id": str(sample_turma.id),
                "disciplina_id": str(disc.id),
                "professor_id": str(prof.id),
                "horario_aula": "07:30 - 08:30",
                "tipo_aula": "Transmissão ao vivo",
                "canal_utilizado": "1",
                "conteudo_ministrado": "Filtro Test",
            },
            headers=admin_headers,
        )

        # Filter by status
        res = client.get(
            "/api/v1/reports/?status=RASCUNHO",
            headers=admin_headers,
        )
        assert res.status_code == 200
        data = res.json()["items"]
        assert len(data) >= 1
        assert all(r["status"] == "RASCUNHO" for r in data)
