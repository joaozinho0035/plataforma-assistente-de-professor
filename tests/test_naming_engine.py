"""
Canal Educação v3.0 — Tests: Naming Engine
Unit tests for sanitization, naming format, P1/P2/P3 detection.
"""

from datetime import date

from app.services.naming_engine import (
    gerar_nome_padronizado,
    remover_acentos,
    sanitizar_conteudo,
    verificar_sufixo_geminada,
)


class TestRemoverAcentos:

    def test_remove_acentos_basicos(self):
        assert remover_acentos("Matemática") == "Matematica"

    def test_remove_acentos_multiplos(self):
        assert remover_acentos("Educação Física") == "Educacao Fisica"

    def test_sem_acentos_nao_muda(self):
        assert remover_acentos("BIOLOGIA") == "BIOLOGIA"

    def test_string_vazia(self):
        assert remover_acentos("") == ""

    def test_cedilha(self):
        assert remover_acentos("Ação") == "Acao"


class TestSanitizarConteudo:

    def test_remove_hifens(self):
        result = sanitizar_conteudo("Intro-dução")
        assert "-" not in result

    def test_remove_underscores(self):
        result = sanitizar_conteudo("Intro_dução")
        assert "_" not in result

    def test_remove_caracteres_especiais(self):
        result = sanitizar_conteudo('Teste: <script>"alert"</script>')
        assert "<" not in result
        assert ">" not in result
        assert '"' not in result

    def test_limita_100_caracteres(self):
        texto = "A" * 150
        result = sanitizar_conteudo(texto)
        assert len(result) <= 100

    def test_uppercase(self):
        result = sanitizar_conteudo("funcoes do primeiro grau")
        assert result == "FUNCOES DO PRIMEIRO GRAU"

    def test_remove_espacos_extras(self):
        result = sanitizar_conteudo("  teste   com   espacos  ")
        assert "  " not in result
        assert result == "TESTE COM ESPACOS"


class TestGerarNomePadronizado:

    def test_formato_basico(self):
        nome = gerar_nome_padronizado(
            nomenclatura_turma="EM 1 TI",
            disciplina="Matemática",
            data_aula=date(2026, 3, 15),
            conteudo="Funções do primeiro grau",
        )
        assert "EM 1 TI" in nome
        assert "15 03 26" in nome
        assert "MATEMATICA" in nome
        assert "FUNCOES DO PRIMEIRO GRAU" in nome
        assert "-" not in nome
        assert "_" not in nome

    def test_eja_sem_turno(self):
        nome = gerar_nome_padronizado(
            nomenclatura_turma="EJA ETAPA V",
            disciplina="Português",
            data_aula=date(2026, 5, 10),
            conteudo="Análise Sintática",
        )
        assert "EJA ETAPA V" in nome
        assert "PORTUGUES" in nome

    def test_ejatec(self):
        nome = gerar_nome_padronizado(
            nomenclatura_turma="EJATEC TEC ADM MOD1",
            disciplina="Física",
            data_aula=date(2026, 6, 1),
            conteudo="Mecânica",
        )
        assert "EJATEC TEC ADM MOD1" in nome
        assert "FISICA" in nome

    def test_sem_acentos_no_resultado(self):
        nome = gerar_nome_padronizado(
            nomenclatura_turma="EM 2 TI",
            disciplina="Educação Física",
            data_aula=date(2026, 1, 20),
            conteudo="Práticas esportivas",
        )
        assert "ã" not in nome
        assert "ç" not in nome
        assert "á" not in nome

    def test_sem_hifens_underscores(self):
        nome = gerar_nome_padronizado(
            nomenclatura_turma="EM 3 MANHÃ",
            disciplina="Artes",
            data_aula=date(2026, 6, 1),
            conteudo="Técnicas de pintura a óleo",
        )
        assert "-" not in nome
        assert "_" not in nome

    def test_nomenclatura_noite(self):
        nome = gerar_nome_padronizado(
            nomenclatura_turma="EM 1 NOITE",
            disciplina="Biologia",
            data_aula=date(2026, 3, 9),
            conteudo="Célula animal",
        )
        assert "EM 1 NOITE" in nome
        assert "BIOLOGIA" in nome

    def test_turno_nao_duplica(self):
        """Regressão: 'EM 3 TARDE' NÃO deve gerar 'EM 3 TARDE TARDE'."""
        nome = gerar_nome_padronizado(
            nomenclatura_turma="EM 3 TARDE",
            disciplina="Educação Física",
            data_aula=date(2026, 2, 25),
            conteudo="Jogos Populares Regionais",
        )
        # Deve ser: EM 3 TARDE EDUCACAO FISICA 25 02 26 JOGOS POPULARES REGIONAIS
        assert nome.count("TARDE") == 1
        assert "EM 3 TARDE EDUCACAO FISICA" in nome


class TestVerificarSufixoGeminada:

    def test_com_p1(self):
        assert verificar_sufixo_geminada("Conteúdo P1") is True

    def test_com_p2(self):
        assert verificar_sufixo_geminada("Conteúdo P2") is True

    def test_com_p3(self):
        assert verificar_sufixo_geminada("Conteúdo P3") is True

    def test_sem_sufixo(self):
        assert verificar_sufixo_geminada("Conteúdo normal") is False

    def test_p4_invalido(self):
        assert verificar_sufixo_geminada("Conteúdo P4") is False

    def test_p1_no_meio(self):
        # P1 deve estar no final
        assert verificar_sufixo_geminada("P1 Conteúdo") is False


