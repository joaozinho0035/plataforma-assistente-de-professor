import os
import sys

# Setup Python Path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.database import SessionLocal
from app.models.turma import Turma
from app.models.auxiliares import Grade

def sanear_turmas():
    db = SessionLocal()
    try:
        # Coleta todas as turmas legadas que contêm o padrão " - " no nome
        # Exemplo: "1ª SÉRIE - INTEGRAL", "EJATEC MOD 01 - Noite"
        turmas_legadas = db.query(Turma).filter(Turma.nome.like("% - %")).all()
        
        grades_removidas = 0
        turmas_removidas = 0
        
        print(f"Encontradas {len(turmas_legadas)} turmas para deletar.")
        
        for t in turmas_legadas:
            # Remover horários (Grades) vinculados primeiro para não ferir chaves estrangeiras
            grades = db.query(Grade).filter(Grade.turma_id == t.id).all()
            for g in grades:
                db.delete(g)
                grades_removidas += 1
            
            # Remover a Turma
            db.delete(t)
            turmas_removidas += 1
            
        db.commit()
        print(f"SUCESSO: Foram removidas {turmas_removidas} turmas duplicadas e {grades_removidas} horários (Grades) vinculados a elas.")
        
        # Pós-verificação: quantas turmas oficiais sobraram?
        restantes = db.query(Turma).count()
        print(f"Total de turmas restantes oficiais no sistema: {restantes}")
        
    except Exception as e:
        db.rollback()
        print(f"ERRO: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    sanear_turmas()
