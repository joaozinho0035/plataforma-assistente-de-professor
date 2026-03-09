import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.auxiliares import Disciplina, Grade, ProfessorDisciplina
from app.models.class_report import ClassReport

def cleanup():
    db = SessionLocal()
    try:
        disps = db.query(Disciplina).all()
        print(f"Total Disciplinas before cleanup: {len(disps)}")

        deleted_count = 0
        for d in disps:
            grades = db.query(Grade).filter(Grade.disciplina_id == d.id).count()
            reports = db.query(ClassReport).filter(ClassReport.disciplina_id == d.id).count()
            
            # If the discipline is not used in any Grades or ClassReports, it's safe to delete.
            if grades == 0 and reports == 0:
                print(f"Deleting unused discipline: {d.nome}")
                db.query(ProfessorDisciplina).filter(ProfessorDisciplina.disciplina_id == d.id).delete()
                db.delete(d)
                deleted_count += 1

        db.commit()
        print(f"Cleanup complete. Deleted {deleted_count} unused disciplines.")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
