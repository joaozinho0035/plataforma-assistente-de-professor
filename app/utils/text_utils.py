import re

def higienizar_nome_arquivo(nome_original: str) -> str:
    """
    BA008: Motor de Sanitização.
    Remove caracteres inválidos para sistemas de arquivos e URLs.
    Regex base: [\/:*?"<>|
]    """
    # Define o padrão de caracteres proibidos
    padrao_proibido = r'[\\/:*?"<>|]'
    
    # Substitui os caracteres proibidos por uma string vazia
    nome_limpo = re.sub(padrao_proibido, '', nome_original)
    
    # Refinamento: Remove espaços duplos criados após a remoção
    nome_limpo = re.sub(r'\s+', ' ', nome_limpo)
    
    return nome_limpo.strip()
