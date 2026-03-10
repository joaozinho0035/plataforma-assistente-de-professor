import csv
import os
import sys
import re
from datetime import datetime, time

# Adiciona a raiz do projeto ao path para conseguir importar a app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.turma import Turma
from app.models.auxiliares import Disciplina, Grade, Professor

def limpar_texto(texto: str) -> str:
    """Remove espaços extra no início e fim das strings."""
    return texto.strip() if texto else ""

def inferir_turno_aula(hora_inicio: time) -> str:
    minutos_totais = hora_inicio.hour * 60 + hora_inicio.minute
    if minutos_totais < (12 * 60):
        return "MANHÃ"
    elif minutos_totais < (18 * 60 + 20):
        return "TARDE"
    else:
        return "NOITE"

def inferir_modalidade(serie_str: str) -> str:
    serie_upper = serie_str.upper()
    if "EJATEC" in serie_upper:
        return "EJATEC"
    elif "EJA" in serie_upper:
        return "EJA"
    else:
        return "REGULAR"

def executar_migracao():
    # Caminho do novo arquivo na raiz do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_csv = os.path.join(base_dir, 'horarioNew - horario.csv.csv')
    
    if not os.path.exists(caminho_csv):
        print(f"❌ ERRO: Arquivo não encontrado em {caminho_csv}")
        return

    encodings_para_testar = ['utf-8-sig', 'cp1252', 'iso-8859-1']
    encoding_correto = None
    for enc in encodings_para_testar:
        try:
            with open(caminho_csv, mode='r', encoding=enc) as f:
                f.read(2048)
            encoding_correto = enc
            break
        except UnicodeDecodeError:
            continue
            
    if not encoding_correto:
        print("❌ ERRO CRÍTICO: Não foi possível descobrir a codificação do ficheiro Excel.")
        return

    db = SessionLocal()
    print(f"🚀 Iniciando Motor de Migração (ETL) usando codificação [{encoding_correto}]...")
    
    estatisticas = {"turmas": 0, "disciplinas": 0, "grades": 0, "professores": 0}

    try:
        with open(caminho_csv, mode='r', encoding=encoding_correto) as ficheiro:
            primeira_linha = ficheiro.readline()
            ficheiro.seek(0)
            delimitador = ';' if ';' in primeira_linha else ','
            leitor_csv = csv.DictReader(ficheiro, delimiter=delimitador)
            
            for linha_idx, linha in enumerate(leitor_csv, start=2):
                try:
                    serie = limpar_texto(linha.get('SÉRIE', ''))
                    periodo = limpar_texto(linha.get('PERIODO', ''))
                    nomenclatura_turma = limpar_texto(linha.get('NOMECLATURA TURMA/TURNO', ''))
                    horario_str = limpar_texto(linha.get('HORÁRIO', ''))
                    dia_semana = limpar_texto(linha.get('DIA', ''))
                    nome_professor = limpar_texto(linha.get('PROFESSOR', ''))
                    # Mudança: Usar coluna H ('NOMENCLATURA') em vez de G ('DISCIPLINA')
                    nome_disciplina = limpar_texto(linha.get('NOMENCLATURA', ''))
                    nomenclatura_disciplina = limpar_texto(linha.get('NOMENCLATURA', ''))
                    iptv_str = limpar_texto(linha.get('IPTV', ''))
                    url_iptv = limpar_texto(linha.get('URL (IPTV)', ''))
                    
                    if not serie or not horario_str:
                        continue 
                    
                    # --- NOVO: Lidar com o caso "GRAVAÇÃO" no horário ---
                    if horario_str.upper() == "GRAVAÇÃO":
                        hora_inicio = time(0, 0) # 00:00:00 (Tempo Dummy)
                        hora_fim = time(23, 59)  # 23:59:59 (Tempo Dummy)
                        turno_aula = periodo.upper() if periodo else "GRAVAÇÃO"
                    else:
                        # Processo normal de horas
                        partes_horario = re.split(r'\s*(?:às|as|-|a)\s*', horario_str.lower())
                        if len(partes_horario) != 2:
                            # Tenta outro padrão se falhar
                            partes_horario = re.split(r'\s*-\s*', horario_str)
                            if len(partes_horario) != 2:
                                print(f"⚠️ Aviso: Formato de horário ignorado na linha {linha_idx}: '{horario_str}'")
                                continue
                            
                        str_inicio, str_fim = partes_horario[0].strip(), partes_horario[1].strip()
                        # Normaliza horários sem :
                        if ':' not in str_inicio and len(str_inicio) == 4:
                            str_inicio = f"{str_inicio[:2]}:{str_inicio[2:]}"
                        if ':' not in str_fim and len(str_fim) == 4:
                            str_fim = f"{str_fim[:2]}:{str_fim[2:]}"
                            
                        hora_inicio = datetime.strptime(str_inicio, "%H:%M").time()
                        hora_fim = datetime.strptime(str_fim, "%H:%M").time()
                        turno_aula = inferir_turno_aula(hora_inicio)
                    
                    modalidade_inferida = inferir_modalidade(serie)
                    iptv = int(iptv_str) if iptv_str.isdigit() else None
                    
                    # Gestão de Professores atual
                    professor_db = None
                    if nome_professor:
                        professor_db = db.query(Professor).filter(Professor.nome == nome_professor).first()
                        if not professor_db:
                            professor_db = Professor(nome=nome_professor)
                            db.add(professor_db)
                            db.flush()
                            estatisticas["professores"] += 1

                    # Gestão de Disciplinas
                    disciplina_db = db.query(Disciplina).filter(Disciplina.nome == nome_disciplina).first()
                    if not disciplina_db:
                        disciplina_db = Disciplina(nome=nome_disciplina, nomenclatura_padrao=nomenclatura_disciplina)
                        db.add(disciplina_db)
                        db.flush()
                        estatisticas["disciplinas"] += 1

                    # Gestão de Turmas
                    nome_turma_ui = f"{serie} - {periodo}"
                    turno_turma = "INTEGRAL" if "INTEGRAL" in periodo.upper() else periodo.upper()
                    
                    turma_db = db.query(Turma).filter(Turma.nomenclatura_padrao == nomenclatura_turma).first()
                    if not turma_db:
                        turma_db = Turma(
                            nome=nome_turma_ui,
                            modalidade=modalidade_inferida,
                            serie_modulo=serie,
                            turno=turno_turma,
                            nomenclatura_padrao=nomenclatura_turma
                        )
                        db.add(turma_db)
                        db.flush()
                        estatisticas["turmas"] += 1
                        
                    # Gestão da Grade
                    grade_existente = db.query(Grade).filter(
                        Grade.turma_id == turma_db.id,
                        Grade.dia_semana == dia_semana,
                        Grade.horario_inicio == hora_inicio,
                        Grade.disciplina_id == disciplina_db.id
                    ).first()
                    
                    if not grade_existente:
                        nova_grade = Grade(
                            turma_id=turma_db.id,
                            disciplina_id=disciplina_db.id,
                            professor_id=professor_db.id if professor_db else None,
                            dia_semana=dia_semana,
                            horario_inicio=hora_inicio,
                            horario_fim=hora_fim,
                            turno_aula=turno_aula,
                            canal_iptv=iptv,
                            descricao=url_iptv
                        )
                        db.add(nova_grade)
                        estatisticas["grades"] += 1
                    else:
                        # Atualiza professor se mudou
                        if professor_db and grade_existente.professor_id != professor_db.id:
                            grade_existente.professor_id = professor_db.id
                        if url_iptv and grade_existente.descricao != url_iptv:
                            grade_existente.descricao = url_iptv

                except Exception as e:
                    print(f"⚠️ Erro ao processar linha {linha_idx} ({serie} - {nome_disciplina}): {str(e)}")
                    db.rollback()
                    continue 

        db.commit()
        print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("-" * 30)
        print(f"📚 Novas Disciplinas: {estatisticas['disciplinas']}")
        print(f"🏫 Novas Turmas: {estatisticas['turmas']}")
        print(f"👨‍🏫 Novos Professores: {estatisticas['professores']}")
        print(f"⏱️ Aulas Inseridas na Grade: {estatisticas['grades']}")
        print("-" * 30)

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO CRÍTICO NA MIGRAÇÃO: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    executar_migracao()