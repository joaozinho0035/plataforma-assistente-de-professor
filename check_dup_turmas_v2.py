from app.core.database import SessionLocal
from app.models.turma import Turma
from app.models.auxiliares import Grade
from app.models.class_report import ClassReport

def analyze():
    db = SessionLocal()
    try:
        turmas = db.query(Turma).all()
        print(f"Total Turmas cadastradas: {len(turmas)}")
        
        grupos = {}
        for t in turmas:
            key = (t.serie_modulo, t.turno.upper())
            if key not in grupos:
                grupos[key] = []
            grupos[key].append(t)
            
        for key, lista in grupos.items():
            if len(lista) > 1:
                print(f"\n[CONFLITO] Série: {key[0]} | Turno: {key[1]}")
                for t in lista:
                    grades_count = db.query(Grade).filter(Grade.turma_id == t.id).count()
                    reports_count = db.query(ClassReport).filter(ClassReport.turma_id == t.id).count()
                    print(f"   -> ID: {t.id} | Nome: '{t.nome}' | Nomenclatura: '{t.nomenclatura_padrao}' | Grades: {grades_count} | Reports/Relatórios: {reports_count}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze()
