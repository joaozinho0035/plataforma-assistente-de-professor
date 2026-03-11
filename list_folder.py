import sys
import os
sys.path.append(os.getcwd())
from app.services.sync_drive import get_drive_service
from app.core.config import get_settings

def list_folder_contents():
    settings = get_settings()
    service = get_drive_service()
    folder_id = settings.GOOGLE_DRIVE_VIDEOS_FOLDER_ID
    
    print(f"Checking Folder ID: {folder_id}")
    
    query = f"'{folder_id}' in parents and trashed = false"
    # Also try without parents to see everything available
    query_broad = "trashed = false and mimeType contains 'video'"
    
    try:
        print("\n--- Files in specific folder ---")
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=50,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives"
        ).execute()
        items = results.get('files', [])
        if not items:
            print("No files found in this folder.")
        for item in items:
            print(f"NAME: {item['name']} | ID: {item['id']}")
            
        print("\n--- Broad Search (any video) ---")
        results_broad = service.files().list(
            q=query_broad,
            fields="files(id, name, mimeType)",
            pageSize=10,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives"
        ).execute()
        items_broad = results_broad.get('files', [])
        for item in items_broad:
            print(f"NAME: {item['name']} | ID: {item['id']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_folder_contents()
