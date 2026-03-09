"""
Canal Educação v3.0 — Tests: Text Utils
Unit tests for text sanitization.
"""

from app.utils.text_utils import higienizar_nome_arquivo


class TestHigienizarNomeArquivo:

    def test_remove_barras(self):
        assert "\\" not in higienizar_nome_arquivo("test\\path")
        assert "/" not in higienizar_nome_arquivo("test/path")

    def test_remove_caracteres_proibidos(self):
        result = higienizar_nome_arquivo('test:file?"name<>|.mp4')
        assert ":" not in result
        assert "?" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_remove_espacos_duplos(self):
        result = higienizar_nome_arquivo("teste   com   espacos")
        assert "  " not in result
        assert result == "teste com espacos"

    def test_strip_pontas(self):
        result = higienizar_nome_arquivo("  teste  ")
        assert result == "teste"

    def test_string_limpa_nao_muda(self):
        assert higienizar_nome_arquivo("nome normal") == "nome normal"

    def test_string_vazia(self):
        assert higienizar_nome_arquivo("") == ""
