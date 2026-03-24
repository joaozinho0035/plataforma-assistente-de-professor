import os
import sys
from collections import defaultdict

# Add workspace to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.database import SessionLocal
from app.models.auxiliares import Professor, ProfessorDisciplina, Grade

def merge_professores():
    db = SessionLocal()
    try:
        profs = db.query(Professor).all()
        
        # Agrupar por nome sem espacos e em maíusculo
        grupos = defaultdict(list)
        for p in profs:
            norm_name = p.nome.strip().upper()
            grupos[norm_name].append(p)
            
        merged_count = 0
        deleted_count = 0
        
        for norm_name, lista in grupos.items():
            if len(lista) > 1:
                print(f"Resolvendo duplicatas para o professor: {norm_name}")
                # Ordenar para preferir a versão com mais iniciais maiúsculas ("Title Case") para manter como primário
                lista.sort(key=lambda p: sum(1 for word in p.nome.split() if word and word[0].isupper()), reverse=True)
                
                prof_primario = lista[0]
                prof_secundarios = lista[1:]
                
                print(f"  -> Mantendo oficial: ID {prof_primario.id} | Nome: '{prof_primario.nome}'")
                
                for prof_sec in prof_secundarios:
                    print(f"  -> Transferindo vínculos e removendo: ID {prof_sec.id} | Nome: '{prof_sec.nome}'")
                    
                    # 1. Update Grades
                    grades = db.query(Grade).filter(Grade.professor_id == prof_sec.id).all()
                    for g in grades:
                        g.professor_id = prof_primario.id
                    
                    # 2. Update Associações ProfessorDisciplina
                    links = db.query(ProfessorDisciplina).filter(ProfessorDisciplina.professor_id == prof_sec.id).all()
                    for link in links:
                        # Checa se o professor primário já leciona essa disciplina
                        ja_existe = db.query(ProfessorDisciplina).filter(
                            ProfessorDisciplina.professor_id == prof_primario.id,
                            ProfessorDisciplina.disciplina_id == link.disciplina_id
                        ).first()
                        
                        db.delete(link)
                        
                        if not ja_existe:
                            novo_link = ProfessorDisciplina(professor_id=prof_primario.id, disciplina_id=link.disciplina_id)
                            db.add(novo_link)
                            
                    # 3. Deltar professor secundário
                    db.delete(prof_sec)
                    merged_count += 1
                    deleted_count += 1
                    
        db.commit()
        print(f"\nSUCESSO: {merged_count} professores secundários tiveram os dados migrados e foram removidos.")
        
    except Exception as e:
        db.rollback()
        print(f"ERRO DE FUSÃO: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    merge_professores()
