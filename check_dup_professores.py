from app.core.database import SessionLocal
from app.models.auxiliares import Professor, Disciplina, ProfessorDisciplina

def analyze():
    db = SessionLocal()
    
    # 1. Check duplicate Professor names
    profs = db.query(Professor).all()
    print(f"Total Professores: {len(profs)}")
    
    from collections import Counter
    names = [p.nome.strip().upper() for p in profs]
    dups = [k for k, v in Counter(names).items() if v > 1]
    if dups:
        print(f"\nATENÇÃO: Professores com nomes similares duplicados: {dups}")
        for p in profs:
            if p.nome.strip().upper() in dups:
                print(f" - ID: {p.id} | Nome Original: '{p.nome}'")
    else:
        print("\nNenhum nome de professor duplicado (case/spaces ignored) encontrado na tabela Professores.")

    # 2. Check duplicate ProfessorDisciplina links
    links = db.query(ProfessorDisciplina).all()
    print(f"\nTotal Links Professor-Disciplina: {len(links)}")
    link_counts = Counter([(L.professor_id, L.disciplina_id) for L in links])
    dup_links = {k: v for k, v in link_counts.items() if v > 1}
    
    if dup_links:
        print(f"\nATENÇÃO: Existem {len(dup_links)} links duplicados entre Professor e Disciplina!")
        for (p_id, d_id), count in dup_links.items():
            p = db.query(Professor).get(p_id)
            d = db.query(Disciplina).get(d_id)
            prof_name = p.nome if p else f"Unknown({p_id})"
            disc_name = d.nome if d else f"Unknown({d_id})"
            print(f" - Prof: {prof_name} | Disciplina: {disc_name} -> {count} vínculos")
    else:
        print("\nNenhum link duplicado na tabela ProfessorDisciplina.")
        
    db.close()

if __name__ == "__main__":
    analyze()
