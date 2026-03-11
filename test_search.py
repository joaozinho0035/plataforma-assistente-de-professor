from app.services.sync_drive import buscar_video_no_drive, get_drive_service, normalize_for_search
import re

test_names = [
    "EM 1 TI GEOGRAFIA 10 03 26 INDUSTRIALIZACAO MUNDIAL II P2.mp4",
    "REGULAR 1ª SERIE MANHA EDUCACAO FISICA 11 03 26.mp4"
]

def debug_search(nome_alvo):
    print(f"\n--- Debugging Search for: {nome_alvo} ---")
    service = get_drive_service()
    
    match_data = re.search(r'(\d{2}\s\d{2}\s\d{2})', nome_alvo)
    query_base = match_data.group(1) if match_data else nome_alvo.replace(".mp4", "").strip()
    query = f"name contains '{query_base}' and trashed = false"
    
    print(f"Query: {query}")
    results = service.files().list(
        q=query, 
        fields="files(id, name)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="allDrives"
    ).execute()
    
    items = results.get('files', [])
    print(f"Found {len(items)} items in Drive for this query.")
    
    alvo_norm = normalize_for_search(nome_alvo.replace(".mp4", ""))
    print(f"Target Normalized: '{alvo_norm}'")
    
    for item in items:
        name = item['name']
        name_norm = normalize_for_search(name.replace(".mp4", ""))
        match = (alvo_norm == name_norm or alvo_norm in name_norm or name_norm in alvo_norm)
        print(f"  - Drive: '{name}'")
        print(f"    Norm : '{name_norm}'")
        print(f"    Match: {match}")

if __name__ == "__main__":
    for name in test_names:
        debug_search(name)
