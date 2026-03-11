import sys
import os
sys.path.append(os.getcwd())
from app.services.sync_drive import get_drive_service

def list_all_videos():
    service = get_drive_service()
    query = "trashed = false and mimeType contains 'video'"
    
    try:
        results = service.files().list(
            q=query,
            fields="files(id, name, parents)",
            pageSize=100,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives"
        ).execute()
        items = results.get('files', [])
        print(f"Total videos found: {len(items)}")
        folders = set()
        for item in items:
            p = item.get('parents', ['NO PARENT'])[0]
            print(f"FILE: {item['name']} | FOLDER: {p} | ID: {item['id']}")
            folders.add(p)
        
        print("\nDistinct Parent Folders Found:")
        for f in folders:
            print(f" - {f}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_videos()
