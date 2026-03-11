import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def list_recent_files():
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print(f"Error: {credentials_path} not found.")
        return

    creds = Credentials.from_service_account_file(
        credentials_path, 
        scopes=['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']
    )
    service = build('drive', 'v3', credentials=creds)
    
    print("Listing latest 50 files in Drive (MP4 only)...")
    try:
        # Search for mp4 files specifically
        results = service.files().list(
            q="mimeType = 'video/mp4' and trashed = false",
            orderBy="createdTime desc",
            pageSize=50,
            fields="files(id, name, createdTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives"
        ).execute()
        
        items = results.get('files', [])
        if not items:
            print("No MP4 files found.")
            # Search all files if no mp4 found
            results = service.files().list(
                q="trashed = false",
                orderBy="createdTime desc",
                pageSize=20,
                fields="files(id, name, mimeType)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora="allDrives"
            ).execute()
            items = results.get('files', [])
            
        for item in items:
            print(f"- {item['name']} | ID: {item['id']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_recent_files()
