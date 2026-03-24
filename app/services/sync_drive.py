import re
import os
import unicodedata
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.core.config import get_settings

settings = get_settings()

def get_drive_service():
    """
    Inicializa o serviço do Google Drive usando a conta de serviço configurada.
    """
    credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
    
    # Se o caminho for relativo, tenta encontrar na raiz do projeto
    if not os.path.isabs(credentials_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        credentials_path = os.path.join(base_dir, credentials_path)

    if not os.path.exists(credentials_path):
        print(f"⚠️ AVISO: Arquivo de credenciais não encontrado em {credentials_path}")
        return None

    try:
        creds = Credentials.from_service_account_file(
            credentials_path, 
            scopes=['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"❌ ERRO ao inicializar Google Drive Service: {str(e)}")
        return None

def normalize_for_search(text: str) -> str:
    """
    Remove acentos, converte para minúsculo e limpa caracteres especiais
    para garantir um match robusto.
    """
    if not text:
        return ""
    # Remove acentos
    nfkd_form = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Lowercase + remove caracteres não alfanuméricos (mantendo espaços)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def buscar_video_no_drive(nome_alvo: str):
    """
    Busca flexível no Drive (§3.2 / Regras 6-9).
    """
    service = get_drive_service()
    if not service:
        return None

    # Nome base sem extensão para a query
    nome_base = re.sub(r'(?i)\.mp4$', '', nome_alvo).strip()

    # Nome seguro para query (escape de aspas simples)
    nome_seguro = nome_base.replace("'", "\\'")
    
    # Query recomendada (§6 e §8)
    # Usamos 'contains' no nome, filtro de video e não lixo
    query = f"name contains '{nome_seguro}' and mimeType contains 'video' and trashed = false"
    
    # Removido '{folder_id}' in parents pois os arquivos estão em subpastas (§6/§9)
    # A busca global (allDrives) é suficiente e recomendada.
    pass
    
    try:
        results = service.files().list(
            q=query, 
            fields="files(id, name, webViewLink, size, createdTime, mimeType, md5Checksum)",
            pageSize=20,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives"
        ).execute()
        
        items = results.get('files', [])
        
        # Alvo normalizado para comparação (§9)
        alvo_norm = normalize_for_search(nome_base)
        
        for file in items:
            drive_name = file.get('name', '')
            drive_norm = normalize_for_search(re.sub(r'(?i)\.mp4$', '', drive_name))
            
            # Match flexível: ignorando acentos, case e extensão
            if alvo_norm == drive_norm or alvo_norm in drive_norm or drive_norm in alvo_norm:
                print(f"✅ Match Flexível: '{drive_name}' corresponde a '{nome_alvo}'")
                return file
                
        # Fallback: Se não achou com o nome completo, tenta buscar apenas pela data se disponível
        match_data = re.search(r'(\d{2})\s(\d{2})\s(\d{2})', nome_alvo)
        if match_data:
            dia, mes, ano = match_data.groups()
            query_data = f"name contains '{dia}' and name contains '{mes}' and name contains '{ano}' and mimeType contains 'video' and trashed = false"
            
            results = service.files().list(
                q=query_data, 
                fields="files(id, name, webViewLink, size, createdTime, mimeType, md5Checksum)",
                pageSize=50,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora="allDrives"
            ).execute()
            
            items = results.get('files', [])
            for file in items:
                drive_name = file.get('name', '')
                drive_norm = normalize_for_search(re.sub(r'(?i)\.mp4$', '', drive_name))
                if alvo_norm == drive_norm or alvo_norm in drive_norm or drive_norm in alvo_norm:
                    print(f"✅ Match Flexível (via Data): '{drive_name}' corresponde a '{nome_alvo}'")
                    return file

        print(f"⚠️ Nenhum vídeo encontrado no Drive para: {nome_alvo}")
        return None
        
    except Exception as e:
        print(f"❌ ERRO na busca do Drive: {str(e)}")
        # Tratamento SRE: Rate Limiting e Locks
        from googleapiclient.errors import HttpError
        if isinstance(e, HttpError) and e.resp.status in [423, 429]:
            raise e  # Lança a exceção para que o Celery possa efetuar o retry_backoff
        return None
