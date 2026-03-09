"""
Canal Educação v3.0 — ETL: Importar Professores e Disciplinas do horarioNew CSV.
Cria registos nas tabelas 'professores', 'disciplinas' e 'professor_disciplinas' (M:N).
Fonte: horarioNew - horario.csv.csv (Colunas: PROFESSOR, DISCIPLINA)
"""

import csv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.auxiliares import Disciplina, Professor, ProfessorDisciplina


def executar_etl_professores():
    caminho_csv = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "horarioNew - horario.csv.csv",
    )

    if not os.path.exists(caminho_csv):
        print(f"❌ ERRO: Arquivo não encontrado: {caminho_csv}")
        return

    # Detectar encoding
    encodings = ["utf-8-sig", "cp1252", "iso-8859-1"]
    encoding_correto = None
    for enc in encodings:
        try:
            with open(caminho_csv, mode="r", encoding=enc) as f:
                f.read(2048)
            encoding_correto = enc
            break
        except UnicodeDecodeError:
            continue

    if not encoding_correto:
        print("❌ ERRO: Não foi possível ler o CSV.")
        return

    db = SessionLocal()
    stats = {"professores": 0, "disciplinas": 0, "vinculos": 0, "ignorados": 0}

    print(f"🚀 ETL Professores/Disciplinas (horarioNew) [{encoding_correto}]...")

    try:
        with open(caminho_csv, mode="r", encoding=encoding_correto) as f:
            primeira_linha = f.readline()
            f.seek(0)
            delimitador = ";" if ";" in primeira_linha else ","
            reader = csv.DictReader(f, delimiter=delimitador)

            for idx, row in enumerate(reader, start=2):
                # Colunas do novo CSV: PROFESSOR (col F) e DISCIPLINA (col H - NOMENCLATURA)
                nome_prof = row.get("PROFESSOR", "").strip()
                nome_disc = row.get("NOMENCLATURA", "").strip()

                # Remove prefixos comuns de título (e.g., "Prof. Tércio Câmara")
                if nome_prof.startswith("Prof. "):
                    nome_prof = nome_prof[6:].strip()
                if nome_prof.startswith("Prof "):
                    nome_prof = nome_prof[5:].strip()

                if not nome_prof or not nome_disc:
                    stats["ignorados"] += 1
                    continue

                # Upsert Professor
                professor = (
                    db.query(Professor)
                    .filter(Professor.nome == nome_prof)
                    .first()
                )
                if not professor:
                    professor = Professor(nome=nome_prof)
                    db.add(professor)
                    db.flush()
                    stats["professores"] += 1

                # Upsert Disciplina
                disciplina = (
                    db.query(Disciplina)
                    .filter(Disciplina.nome == nome_disc)
                    .first()
                )
                if not disciplina:
                    # Usar NOMENCLATURA como nomenclatura_padrao se disponível
                    nomenclatura = row.get("NOMENCLATURA", "").strip()
                    disciplina = Disciplina(
                        nome=nome_disc,
                        nomenclatura_padrao=nomenclatura or None,
                    )
                    db.add(disciplina)
                    db.flush()
                    stats["disciplinas"] += 1

                # Upsert Vínculo M:N
                vinculo = (
                    db.query(ProfessorDisciplina)
                    .filter(
                        ProfessorDisciplina.professor_id == professor.id,
                        ProfessorDisciplina.disciplina_id == disciplina.id,
                    )
                    .first()
                )
                if not vinculo:
                    vinculo = ProfessorDisciplina(
                        professor_id=professor.id,
                        disciplina_id=disciplina.id,
                    )
                    db.add(vinculo)
                    stats["vinculos"] += 1

        db.commit()
        print("\n✅ ETL CONCLUÍDA COM SUCESSO!")
        print("-" * 30)
        print(f"👨‍🏫 Novos Professores: {stats['professores']}")
        print(f"📚 Novas Disciplinas: {stats['disciplinas']}")
        print(f"🔗 Novos Vínculos: {stats['vinculos']}")
        print(f"⏩ Linhas ignoradas (sem professor/disciplina): {stats['ignorados']}")
        print("-" * 30)

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO CRÍTICO NA ETL: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    executar_etl_professores()
