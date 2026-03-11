import re
from app.core.database import SessionLocal
from app.models.class_report import ClassReport
db = SessionLocal()
reports = db.query(ClassReport).filter(ClassReport.status == "FINALIZADO").all()
for r in reports:
    if r.nome_ficheiro_gerado:
        novo_nome = re.sub(r'(?i)\.mp4$', '', r.nome_ficheiro_gerado).strip() + ".mp4"
        if novo_nome != r.nome_ficheiro_gerado:
            print(f"Atualizando: {r.nome_ficheiro_gerado}  ->  {novo_nome}")
            r.nome_ficheiro_gerado = novo_nome
db.commit()
db.close()
