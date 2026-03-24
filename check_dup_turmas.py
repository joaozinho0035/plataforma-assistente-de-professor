from app.core.database import SessionLocal
from app.models.turma import Turma
from app.models.auxiliares import Grade

def check_turmas():
    db = SessionLocal()
    for t in db.query(Turma).all():
        count = db.query(Grade).filter(Grade.turma_id == t.id).count()
        print(f"Turma: {t.nome} (Serie: {t.serie_modulo}, Turno: {t.turno}) - Grades: {count}")
    db.close()

if __name__ == "__main__":
    check_turmas()
