import os
import sys
import csv
from datetime import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.turma import Turma
from app.models.auxiliares import Disciplina, Professor, Grade, ProfessorDisciplina

def parse_horario(h_str):
    if not h_str or h_str.upper() == "GRAVAÇÃO":
        return time(0, 0), time(0, 0)
    parts = h_str.split("às")
    if len(parts) == 2:
        try:
            h1, m1 = map(int, parts[0].strip().split(":"))
            h2, m2 = map(int, parts[1].strip().split(":"))
            return time(h1, m1), time(h2, m2)
        except:
            pass
    return time(0, 0), time(0, 0)

def carregar():
    csv_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "horario.csv")
    
    db = SessionLocal()
    count = 0
    try:
        try:
            f = open(csv_file, mode='r', encoding='utf-8-sig')
            f.read()
            f.seek(0)
        except UnicodeDecodeError:
            f.close()
            f = open(csv_file, mode='r', encoding='ISO-8859-1')
            
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            if not row.get('SÉRIE') or not row.get('SÉRIE').strip():
                continue
                
            # 1. Turma
            t_nome = row['NOMECLATURA TURMA/TURNO'].strip()
            t_serie = row['SÉRIE'].strip()
            t_turno = row['PERIODO'].strip()
            
            turma = db.query(Turma).filter(Turma.nome == t_nome).first()
            if not turma:
                turma = Turma(
                    nome=t_nome,
                    serie_modulo=t_serie,
                    turno=t_turno,
                    modalidade=t_serie,
                    nomenclatura_padrao=t_nome
                )
                db.add(turma)
                db.commit()
                db.refresh(turma)
            
            # 2. Disciplina
            d_nome = row['DISCIPLINA'].strip()
            d_nom_padrao = row['NOMENCLATURA'].strip()
            disciplina = None
            if d_nome:
                disciplina = db.query(Disciplina).filter(Disciplina.nome == d_nome).first()
                if not disciplina:
                    disciplina = Disciplina(nome=d_nome, nomenclatura_padrao=d_nom_padrao)
                    db.add(disciplina)
                    db.commit()
                    db.refresh(disciplina)

            # 3. Professor
            p_nome_raw = row['PROFESSOR'].strip()
            p_nome = p_nome_raw.title() if p_nome_raw else ""
            professor = None
            if p_nome:
                from sqlalchemy import func
                professor = db.query(Professor).filter(func.upper(Professor.nome) == p_nome.upper()).first()
                if not professor:
                    professor = Professor(nome=p_nome)
                    db.add(professor)
                    db.commit()
                    db.refresh(professor)
                    
            # 3.1. Vínculo Professor-Disciplina
            if professor and disciplina:
                vinculo = db.query(ProfessorDisciplina).filter(
                    ProfessorDisciplina.professor_id == professor.id,
                    ProfessorDisciplina.disciplina_id == disciplina.id
                ).first()
                if not vinculo:
                    db.add(ProfessorDisciplina(professor_id=professor.id, disciplina_id=disciplina.id))
                    db.commit()
                    
            # 4. Grade
            horario_str = row['HORÁRIO'].strip()
            h_inicio, h_fim = parse_horario(horario_str)
            iptv = row['IPTV'].strip()
            iptv_val = int(iptv) if iptv.isdigit() else None
            
            dia = row['DIA'].strip()
            
            grade = db.query(Grade).filter(
                Grade.turma_id == turma.id,
                Grade.dia_semana == dia,
                Grade.descricao == horario_str,
                Grade.disciplina_id == (disciplina.id if disciplina else None)
            ).first()
            
            if not grade:
                grade = Grade(
                    turma_id=turma.id,
                    disciplina_id=disciplina.id if disciplina else None,
                    professor_id=professor.id if professor else None,
                    dia_semana=dia,
                    horario_inicio=h_inicio,
                    horario_fim=h_fim,
                    turno_aula=t_turno,
                    descricao=horario_str,
                    canal_iptv=iptv_val
                )
                db.add(grade)
                db.commit()
            
            count += 1
            if count % 50 == 0:
                print(f"Processadas {count} linhas...")
                
        f.close()
        print(f"SUCESSO: Seed concluído! Processou {count} aulas/grades em horario.csv.")
    except Exception as e:
        db.rollback()
        print(f"ERRO: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    carregar()
