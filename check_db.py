import os
import sys

# Add the project root to sys.path if not there
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.database import SessionLocal
from app.models.auxiliares import Professor, Disciplina, ProfessorDisciplina

def main():
    db = SessionLocal()
    try:
        professors = db.query(Professor).all()
        disciplinas = db.query(Disciplina).all()
        assocs = db.query(ProfessorDisciplina).all()
        
        print(f"Total Professors: {len(professors)}")
        print(f"Total Disciplinas: {len(disciplinas)}")
        print(f"Total Associations: {len(assocs)}")
        
        print("\n--- Sample Professors and their Disciplinas ---")
        for p in professors[:10]:
            disc_names = [d.nome for d in p.disciplinas]
            print(f"Prof: {p.nome} -> Disciplinas: {disc_names}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
