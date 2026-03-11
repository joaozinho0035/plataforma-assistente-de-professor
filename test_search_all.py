import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.class_report import ClassReport
from app.services.sync_drive import buscar_video_no_drive

def verify_all():
    db = SessionLocal()
    reports = db.query(ClassReport).filter(ClassReport.status == "FINALIZADO").all()
    
    found_count = 0
    not_found = []
    
    print(f"--- Starting Bulk Verification ({len(reports)} reports) ---")
    for r in reports:
        print(f"Checking: {r.nome_ficheiro_gerado}")
        result = buscar_video_no_drive(r.nome_ficheiro_gerado)
        if result:
            print(f"  ✅ FOUND: {result['name']}")
            found_count += 1
        else:
            print(f"  ❌ NOT FOUND")
            not_found.append(r.nome_ficheiro_gerado)
        print("-" * 20)
    
    print(f"\n--- Summary ---")
    print(f"Total: {len(reports)}")
    print(f"Found: {found_count}")
    print(f"Missing: {len(not_found)}")
    if not_found:
        print("Missing filenames:")
        for name in not_found:
            print(f"  - {name}")
    
    db.close()

if __name__ == "__main__":
    verify_all()
