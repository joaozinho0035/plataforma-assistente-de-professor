from datetime import date
from app.services.naming_engine import gerar_nome_padronizado
from app.services.sync_drive import buscar_video_no_drive

casos = [
    {
        "turma": "EJA V QP TÉC AGRIC",
        "disciplina": "PRODUÇÃO DE RUMIN E NÃO RUMINANTES",
        "data": date(2026, 3, 10),
        "conteudo": "ALIMENTAÇÃO DE RUMINANTES",
        "esperado": "EJA V QP TÉC AGRIC PRODUÇÃO DE RUMIN E NÃO RUMINANTES 10 03 26 ALIMENTAÇÃO DE RUMINANTES.mp4"
    },
    {
        "turma": "EM 1 NOITE",
        "disciplina": "BIOLOGIA",
        "data": date(2026, 3, 9),
        "conteudo": "INTRODUÇÃO À EVOLUÇÃO",
        "esperado": "EM 1 NOITE BIOLOGIA 09 03 26 INTRODUÇÃO À EVOLUÇÃO.mp4"
    },
    {
        "turma": "EM 1 TI",
        "disciplina": "OLIMP DO CONHECIMENTO",
        "data": date(2026, 3, 7),
        "conteudo": "DEDUÇÃO LÓGICA P1",
        "esperado": "EM 1 TI OLIMP DO CONHECIMENTO 07 03 26 DEDUÇÃO LÓGICA P1.mp4"
    },
    {
        "turma": "EM 1 TI",
        "disciplina": "LEIT INTERP PRODUÇÃO TEXTO",
        "data": date(2026, 3, 10),
        "conteudo": "EFEITOS DE SENTIDO DUPLO SENTIDO AMBIGUIDADE E POLISSEMIA",
        "esperado": "EM 1 TI LEIT INTERP PRODUÇÃO TEXTO 10 03 26 EFEITOS DE SENTIDO DUPLO SENTIDO AMBIGUIDADE E POLISSEMIA.mp4"
    }
]

print("=== INICIANDO TESTES DO NAMING ENGINE ===")
for c in casos:
    nome_gerado = gerar_nome_padronizado(c["turma"], c["disciplina"], c["data"], c["conteudo"])
    print(f"\n[Naming Engine] Gerou: '{nome_gerado}'")
    if nome_gerado == c["esperado"]:
        print(" -> [OK] Bate exatamente com a nomenclatura proposta pelo usuário!")
    else:
        print(f" -> [ALERTA] Diferente do esperado: {c['esperado']}")
        
print("\n\n=== INICIANDO CONSULTAS NA API DO GOOGLE DRIVE ===")
for c in casos:
    print(f"\nBuscando: '{c['esperado']}'")
    arquivo_drive = buscar_video_no_drive(c["esperado"])
    
    if arquivo_drive:
        print(f" -> [SUCESSO] Localizado no Drive!")
        print(f" -> Nome real no Drive: {arquivo_drive.get('name')}")
        print(f" -> Link (WebView):     {arquivo_drive.get('webViewLink')}")
        print(f" -> ID:                 {arquivo_drive.get('id')}")
    else:
        print(" -> [FALHA] Não encontrado no Google Drive!")
