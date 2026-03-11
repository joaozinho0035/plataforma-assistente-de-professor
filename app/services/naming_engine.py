"""
Canal Educação v3.0 — Naming Engine (Motor de Nomenclatura).
Gera o nome padronizado do ficheiro MP4 conforme especificação:
  [MODALIDADE] [SERIE] [TURNO] [DISCIPLINA] [DATA] [CONTEUDO]
Sem hifens, sem underscores, sem acentos, sem caracteres especiais.
"""

import re
import unicodedata
from datetime import date


def remover_acentos(texto: str) -> str:
    """Remove toda acentuação do texto (NFD decomposition)."""
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def sanitizar_conteudo(texto: str) -> str:
    """
    Sanitização completa conforme BA008:
    - Remove acentos
    - Remove caracteres inválidos para filesystem: \\ / : * ? " < > |
    - Remove hifens e underscores
    - Remove espaços extras
    - Limita a 100 caracteres
    - Converte para UPPERCASE
    """
    # Remove acentos
    texto = remover_acentos(texto)

    # Remove caracteres proibidos (filesystem + hifens + underscores)
    texto = re.sub(r'[\\/:*?"<>|\-_]', "", texto)

    # Remove espaços extras
    texto = re.sub(r"\s+", " ", texto).strip()

    # Limita a 100 caracteres
    return texto[:100]


def gerar_nome_padronizado(
    nomenclatura_turma: str,
    disciplina: str,
    data_aula: date,
    conteudo: str,
) -> str:
    """
    Gera o nome do ficheiro no formato exato:
    [NOMENCLATURA_TURMA] [DISCIPLINA] [DATA] [CONTEUDO]

    Regras:
    - nomenclatura_turma vem da Coluna C do CSV (ex: EM 1 TI, EM 3 TARDE, EJA ETAPA V)
    - O turno já está embutido na nomenclatura (MANHÃ, TARDE, NOITE, TI)
    - Data no formato DD MM YY
    - Sem hifens ou underscores em nenhum lugar
    - Tudo em UPPERCASE
    """
    data_formatada = data_aula.strftime("%d %m %y")

    partes = [
        remover_acentos(nomenclatura_turma.strip()).upper(),
        remover_acentos(disciplina.strip()).upper(),
        data_formatada,
        sanitizar_conteudo(conteudo),
    ]

    # Junta as partes ignorando vazias, sem hifens/underscores
    nome = " ".join(p for p in partes if p)

    # Sanitização final: remove hifens e underscores em todo o resultado
    nome = re.sub(r"[\-_]", "", nome)
    nome = re.sub(r"\s+", " ", nome).strip()

    # Garante que não duplique a extensão e coloca o .mp4 sempre em minúsculo
    nome = re.sub(r'(?i)\.mp4$', '', nome).strip()

    return f"{nome}.mp4"


def verificar_sufixo_geminada(conteudo: str) -> bool:
    """Verifica se o conteúdo já possui sufixo P1, P2 ou P3."""
    return bool(re.search(r"\bP[1-3]$", conteudo.strip().upper()))