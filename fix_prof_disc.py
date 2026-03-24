import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.auxiliares import Grade, ProfessorDisciplina

def fix_relationships():
    db = SessionLocal()
    try:
        grades = db.query(Grade).filter(Grade.professor_id != None, Grade.disciplina_id != None).all()
        cadastrados = set()
        novos = 0
        
        for g in grades:
            chave = f"{g.professor_id}-{g.disciplina_id}"
            if chave in cadastrados:
                continue
                
            vinculo = db.query(ProfessorDisciplina).filter(
                ProfessorDisciplina.professor_id == g.professor_id,
                ProfessorDisciplina.disciplina_id == g.disciplina_id
            ).first()
            
            if not vinculo:
                novo_vinculo = ProfessorDisciplina(
                    professor_id=g.professor_id,
                    disciplina_id=g.disciplina_id
                )
                db.add(novo_vinculo)
                novos += 1
            
            cadastrados.add(chave)
            
        db.commit()
        print(f"Sucesso: {novos} vínculos criados entre Professores e Disciplinas!")
        
    except Exception as e:
        db.rollback()
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_relationships()
