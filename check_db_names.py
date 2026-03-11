import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.class_report import ClassReport

def check_names():
    db = SessionLocal()
    reports = db.query(ClassReport).filter(ClassReport.status == "FINALIZADO").all()
    for r in reports:
        print(f"ID: {r.id} | Name: {r.nome_ficheiro_gerado}")
    db.close()

if __name__ == "__main__":
    check_names()
