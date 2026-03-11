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
    """Remove toda acentuação do texto (NFKD decomposition)."""
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def sanitizar_conteudo(texto: str) -> str:
    """
    Sanitização conforme novas regras:
    - Remove acentos
    - Remove especificamente: _ . , : ; ! ? / \ () [] {}
    - Remove emojis/símbolos
    - Normaliza espaços múltiplos para um único
    - Preserva o case original (NÃO força uppercase)
    - Limita a 100 caracteres
    """
    # 1. Remove acentos
    texto = remover_acentos(texto)

    # 2. Remove caracteres específicos: _ . , : ; ! ? / \ () [] {}
    # Usamos uma classe de caracteres no regex
    texto = re.sub(r'[_.,:;!?/\\()\[\]{}]', "", texto)

    # 3. Remove emojis e símbolos estranhos (mantém letras, números e espaços)
    # \w inclui letras, números e underscore (mas já removemos underscore acima)
    # Queremos manter espaços, então adicionamos \s
    texto = re.sub(r'[^\w\s]', '', texto)
    # Remove underscores remanescentes se houver (embora re.sub acima cuide disso)
    texto = texto.replace('_', '')

    # 4. Normaliza espaços múltiplos
    texto = re.sub(r"\s+", " ", texto).strip()

    # 5. Limita a 100 caracteres
    return texto[:100]


def gerar_nome_padronizado(
    nomenclatura_turma: str,
    disciplina: str,
    data_aula: date,
    conteudo: str,
) -> str:
    """
    Gera o nome do ficheiro no formato exato:
    [TIPO/SERIE/TURNO] [DISCIPLINA] [DIA] [MES] [ANO] [CONTEUDO].mp4

    Regras:
    - O prefixo "REGULAR" deve ser removido se presente.
    - Separado apenas por espaço.
    - Sem hifens ou underscores.
    - Sem acentos.
    - .mp4 sempre minúsculo e não duplicado.
    """
    # 1. Limpa nomenclatura e remove "REGULAR" no início
    turma_limpo = nomenclatura_turma.strip()
    turma_limpo = re.sub(r'^REGULAR\s*', '', turma_limpo, flags=re.IGNORECASE)
    turma_limpo = remover_acentos(turma_limpo).upper()

    # 2. Disciplina limpa
    disc_limpo = remover_acentos(disciplina.strip()).upper()

    # 3. Data formatada (DD MM YY)
    data_str = data_aula.strftime("%d %m %y")

    # 4. Conteúdo higienizado (preserva case)
    cont_limpo = sanitizar_conteudo(conteudo)

    # 5. Monta o nome base
    partes = [turma_limpo, disc_limpo, data_str, cont_limpo]
    nome_base = " ".join(p for p in partes if p)

    # Limpeza final de hifens/underscores que possam ter sobrado
    nome_base = re.sub(r'[\-_]', ' ', nome_base)
    nome_base = re.sub(r'\s+', ' ', nome_base).strip()

    # 6. Garante extensão .mp4 única e minúscula
    # Remove qualquer .mp4 ou mp4 existente no final (case insensitive)
    nome_final = re.sub(r'(?i)\.mp4$', '', nome_base).strip()
    nome_final = re.sub(r'(?i)mp4$', '', nome_final).strip()
    
    return f"{nome_final}.mp4"


def verificar_sufixo_geminada(conteudo: str) -> bool:
    """Verifica se o conteúdo já possui sufixo P1, P2 ou P3."""
    return bool(re.search(r"\bP[1-3]$", conteudo.strip().upper()))