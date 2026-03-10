import os
import sys

# Define root dir to find app module
sys.path.append('c:/Users/joao.borges/Downloads/ce_assistente_professores')

from app.services.sync_drive import get_drive_service
from app.core.config import get_settings

def test_drive():
    service = get_drive_service()
    settings = get_settings()
    
    # Try basic search
    query = "name contains 'CORRIDA' or name contains 'VERBO THE BE'"
    print(f"Partial Search ({query}):")
    try:
        results = service.files().list(
            q=query, 
            pageSize=10, 
            fields="files(id, name, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        for f in results.get('files', []):
            print(f"- {f['name']} ({f['id']})")
    except Exception as e:
        print("Error:", e)

    # Try shared drive search
    print("\nShared Drive Search:")
    try:
        results = service.files().list(
            q=query, 
            pageSize=5, 
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        for f in results.get('files', []):
            print(f"- {f['name']} ({f['id']})")
    except Exception as e:
        print("Error:", e)

    # Try with Folder ID
    folder_id = settings.GOOGLE_DRIVE_VIDEOS_FOLDER_ID
    print(f"\nFolder Search ({folder_id}):")
    folder_query = f"'{folder_id}' in parents and trashed = false"
    try:
        results = service.files().list(
            q=folder_query, 
            pageSize=5, 
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        for f in results.get('files', []):
            print(f"- {f['name']} ({f['id']})")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_drive()
