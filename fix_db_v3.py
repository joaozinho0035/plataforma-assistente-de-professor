import sys
import os

# Adiciona o diretório atual ao sys.path para importar app
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.class_report import ClassReport
from app.models.turma import Turma
from app.models.auxiliares import Disciplina
from app.services.naming_engine import gerar_nome_padronizado

def fix_filenames():
    db = SessionLocal()
    try:
        reports = db.query(ClassReport).filter(ClassReport.status == "FINALIZADO").all()
        print(f"Found {len(reports)} reports to check.")
        
        updates = 0
        for r in reports:
            turma = db.query(Turma).filter(Turma.id == r.turma_id).first()
            disciplina = db.query(Disciplina).filter(Disciplina.id == r.disciplina_id).first()
            
            if not turma:
                print(f"Skipping report {r.id}: Turma not found.")
                continue
            
            nome_antigo = r.nome_ficheiro_gerado
            nome_novo = gerar_nome_padronizado(
                nomenclatura_turma=turma.nomenclatura_padrao or turma.nome,
                disciplina=disciplina.nome if disciplina else "",
                data_aula=r.data_aula,
                conteudo=r.conteudo_ministrado
            )
            
            if nome_antigo != nome_novo:
                print(f"Updating {r.id}:")
                print(f"  OLD: {nome_antigo}")
                print(f"  NEW: {nome_novo}")
                r.nome_ficheiro_gerado = nome_novo
                updates += 1
        
        db.commit()
        print(f"Migration complete. {updates} records updated.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_filenames()
