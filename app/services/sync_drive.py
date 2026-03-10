import os
import json
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

def buscar_video_no_drive(nome_arquivo: str):
    """
    Busca um arquivo por nome no Google Drive e retorna o link e metadados.
    Implementação para o §3.2 (Compliance do Drive).
    """
    service = get_drive_service()
    if not service:
        return None

    # Escape single quotes in the filename to prevent query syntax errors
    nome_seguro = nome_arquivo.replace("'", "\\'")
    folder_id = settings.GOOGLE_DRIVE_VIDEOS_FOLDER_ID
    
    # Query improved to search inside the specific folder and for the exact sanitized name
    # Usando strict match "=" em vez de "contains" e adicionando a extensão .mp4
    query = f"'{folder_id}' in parents and name = '{nome_seguro}.mp4' and trashed = false"
    
    try:
        results = service.files().list(
            q=query, 
            fields="files(id, name, webViewLink, size, createdTime, mimeType)",
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives"
        ).execute()
        
        items = results.get('files', [])
        if not items:
            return None
            
        return items[0]
    except Exception as e:
        print(f"❌ ERRO na busca do Drive: {str(e)}")
        return None
