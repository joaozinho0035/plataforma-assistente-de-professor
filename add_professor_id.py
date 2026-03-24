import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import engine
from sqlalchemy import text

def add_col():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE grades ADD COLUMN professor_id UUID REFERENCES professores(id);"))
            conn.commit()
            print("Sucesso: Coluna professor_id adicionada à tabela grades.")
    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}")

if __name__ == "__main__":
    add_col()
