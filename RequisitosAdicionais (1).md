# **Documento de Especificação Técnica: Canal Educação v3.0 (Produção)**

## **1\. Visão Geral da Arquitetura e Escalabilidade**

O sistema deixa de ser um protótipo estático (HTML/JS em memória) e passa a ser uma aplicação de produção orientada a serviços (API-Driven). O objetivo é suportar \+50 utilizadores simultâneos com alta consistência de dados (evitando conflitos de edição de grade).

* **Backend (Sugerido):** FastAPI (Python) \- Excelente para alta concorrência e tipagem forte via Pydantic.  
* **Base de Dados:** PostgreSQL \- Relacional, garantindo a integridade referencial entre Estúdios, Turmas, Relatórios e Utilizadores.  
* **Frontend:** Integração das telas atuais com HTMX (para chamadas API leves mantendo a estrutura atual) ou Next.js/React (caso a equipa prefira uma SPA completa).  
* **Tempo Real (Crucial):** Implementação de WebSockets no ecrã de "Gestão de Turmas" para que, quando um utilizador altera um horário, a grelha dos outros 49 utilizadores se atualize instantaneamente, bloqueando a edição simultânea do mesmo slot.

  ## **2\. Requisitos do Módulo de Autenticação (IAM)**

A porta de entrada do sistema deve ser reescrita para garantir segurança e rastreabilidade (Sessões baseadas em JWT \- JSON Web Tokens).

### **2.1. Login Tradicional (Email e Senha)**

* **Registo/Criação:** A criação de contas Gestor ou Auditor deve ser feita apenas pelo Admin via painel. O Assistente pode ser convidado.  
* **Confirmação de Email:** Ao criar a conta, disparar um email via SendGrid ou Amazon SES contendo um token (link) com validade de 24h para definir a senha inicial e confirmar a titularidade.  
* **Segurança:** Senhas guardadas com hash seguro (bcrypt/Argon2).

  ### **2.2. Login via Google (OAuth 2.0) \- Single Sign-On**

* **Integração:** Implementar o fluxo de Autorização do Google.  
* **Regras de Negócio (SSO):** O sistema apenas deve permitir o login social se o email retornado pelo Google pertencer ao domínio corporativo (ex: `@canaleducacao.gov.br` ou `@seduc.gov.br`). Domínios `@gmail.com` normais devem ser rejeitados com a mensagem: *"Acesso restrito a contas institucionais"*.

  ## **3\. Estrutura de Dados: Relatório de Aulas (Payload Definition)**

Para a API que receberá os dados da "Gaveta Lateral" (Frontend), o desenvolvedor deve criar a seguinte tabela/modelo na base de dados (`class_reports`).

Todos estes campos devem ser preenchidos e validados no backend:

### **A. Metadados do Registo (Automáticos)**

1. **id:** UUID (Identificador único do relatório).  
2. **created\_by:** UUID (ID do utilizador logado que preencheu o formulário).  
3. **created\_at:** Timestamp (Data e hora real em que o utilizador clicou em "Finalizar").  
4. **status:** Enum `['RASCUNHO', 'FINALIZADO', 'CANCELADO']`.

   ### **B. Contexto Operacional (Herdados da Grelha / Sistema)**

5. **data\_aula:** Date (YYYY-MM-DD)  
    $$coletar pelo sistema utilizando o arquivo "horario.csv"$$  
   .  
6. **turno:** Enum `['Manhã', 'Tarde', 'Noite', 'FDS manhã', 'FDS tarde', 'FDS noite', 'Outro']`.  
7. **estudio:** Enum `['Estúdio 01', 'Estúdio 02', 'Estúdio 03', 'Estúdio 04', 'Estúdio 05', 'Estúdio 06', 'Estúdio 07', 'Estúdio 08', 'Estúdio 09', 'Externo']`.  
8. **turma\_id:** Identificador da Turma/Série  
    $$turmas já previstas no arquivo "horario.csv"$$  
   .  
9. **disciplina\_id:** Identificador da Disciplina  
    $$disciplinas já previstas no arquivo "professordisciplina.csv"$$  
   .  
10. **professor\_id:** Identificador do Professor(a)  
     $$Professores já previstos no arquivo "professordisciplina.csv"$$  
    .  
11. **horario\_aula:** Enum `['1º Horário', '2º Horário', '3º Horário', '4º Horário', '5º Horário', '6º Horário', '7º Horário', '8º Horário']`  
     $$já definidos no arquivo "horario.csv"$$  
    , se tiver mais horários adicione.  
12. **regular:** Enum `['Sim', 'Não']`.

    ### **C. Detalhes da Execução (Inputs do Assistente)**

13. **tipo\_aula:** Enum `['Manutenção de estúdio', 'Planejamento Pedagógico', 'Videoconferência', 'Gravação estúdio', 'UAPI', 'Transmissão ao vivo', 'Gravação externa']`, se for gestor ou administrador pode adicionar mais tipo aula.  
14. **canal\_utilizado:** Enum `['Canal SEDUC PI 1', 'Canal SEDUC PI 2', 'Canal SEDUC PI 3', 'Canal SEDUC PI 4', 'Canal SEDUC PI 5', 'Canal SEDUC PI 6', 'Canal SEDUC PI 7', 'Canal SEDUC PI 8', 'Canal SEDUC PI 9']`.  
15. **conteudo\_ministrado:** String (Campo de texto altamente sanitizado, base do Naming Engine. Sem acentos, sem caracteres especiais), limitar em 100 caracteres.  
16. **interacao\_professor\_aluno:** Enum `['Não', 'Chat', 'Videoconferência', 'Chat e vídeo', 'Outras']`.  
17. **interacao\_outras\_desc:** String (Campo de texto extra, exibido/obrigatório se `interacao_professor_aluno` for 'Outras').  
18. **atividade\_pratica:** Enum `['Exercício teórico', 'Exercício pratico', 'Dinâmica', 'Debates']`.  
19. **observacoes:** Text (Campo de texto livre para anotações gerais da execução).

    ### **D. Recursos e Materiais**

20. **tipo\_recursos\_utilizados:** Array de Enums `['vídeo', 'chorma key', 'animação', 'alpha', 'Internet', 'Outro']`.  
21. **recursos\_outro\_desc:** String (Campo de texto extra, exibido/obrigatório se `tipo_recursos_utilizados` contiver 'Outro').  
22. **problema\_material:** Enum `['Não', 'Atraso na entrega', 'Alteração', 'Não entregue', 'Problemas técnicos', 'Outros']`.

    ### **E. Ocorrências Operacionais (Compliance)**

23. **teve\_substituicao:** Boolean (`Sim` / `Não`).  
24. **professor\_substituto\_id:** Identificador (Obrigatório se `teve_substituicao` for True. Deve carregar a lista de professores já definidos no arquivo "professordisciplina.csv").  
25. **teve\_atraso:** Boolean (`Sim` / `Não`).  
26. **minutos\_atraso:** Integer (Obrigatório se `teve_atraso` for True. Dropdown listando de 5 em 5 minutos até 60 minutos: `[5, 10, 15, ..., 60]`).  
27. **observacao\_atraso:** Text (Obrigatório se `teve_atraso` for True. Exibe campo "Observação atraso").

    ### **F. Auditoria e Faturamento**

28. **nomeFicheiroGerado:** String (A string exata gerada pela Naming Engine no momento da finalização, ex: `[MOD] [SERIE] [TURNO] [DISC] [DATA] [CONTEUDO].mp4`). O nome do ficheiro gerado não deve ter hífen ou underline.  
29. **conflitoGeminadaResolvido:** Boolean (Flag interna de auditoria para garantir que a regra de adicionar P1/P2/P3 foi cumprida perante o backend).

    ## **4\. Plano de Ação para a Equipa de Desenvolvimento (Roadmap)**

    ### **Fase 1: Configuração do Backend e Base de Dados**

* Setup do projeto FastAPI \+ PostgreSQL.  
* Migração de dados: Criar script (ETL) para importar e relacionar os ficheiros CSV originais (`Séries.csv`, `Horário.csv`, lista de Professores e Disciplinas) para tabelas relacionais SQL.  
* Criação dos Endpoints REST de Leitura (GET turmas, GET horários por data).

  ### **Fase 2: Autenticação**

* Implementação do JWT e Middleware de segurança no FastAPI.  
* Configuração de chaves API no Google Cloud Console para o OAuth 2.0.  
* Integração do envio de emails via SMTP/Serviço cloud para confirmação.

  ### **Fase 3: Integração do Frontend e Naming Engine Backend**

* Ligar a interface HTML desenvolvida às APIs reais e mapear todos os Enum/Selects do Relatório de Aulas.  
* **Crítico:** Replicar a lógica da "Naming Engine" do JS para o Backend. O frontend sugere o nome, mas o backend garante a sanitização e formatação antes de salvar na base de dados para evitar injeção de caracteres inválidos via API.

  ### **Fase 4: Concorrência e WebSockets**

* Adicionar canal WebSocket na tela de Grade Horária para "Broadcast" de atualizações, prevenindo que 50 utilizadores colidam edições simultâneas do mesmo slot (Estúdio \+ Horário).

  ## **5\. Especificações de Interface (Frontend) \- Disposição das Telas**

  ### **5.1. Grade Horária (Componente Principal)**

**Barra de Contexto Superior (Filtro Principal):**

* Acima da tabela, deve existir um **Dropdown Dinâmico (Seletor de Turmas com Auto-complete)**. Um simples botão não é escalável para a quantidade de turmas.  
* O utilizador deve selecionar a turma com base nas nomenclaturas exatas já definidas no ficheiro `horario.csv`. O sistema deve exibir as opções concatenadas para clareza operacional:  
  * 1ª SÉRIE \- INTEGRAL \- EM 1 TI  
  * 1ª SÉRIE \- NOITE \- EM 1 NOITE  
  * 2ª SÉRIE \- INTEGRAL \- EM 2 TI  
  * 2ª SÉRIE \- NOITE \- EM 2 NOITE  
  * 3ª SÉRIE \- INTEGRAL  
  * 3ª SÉRIE \- MANHÃ  
  * 3ª SÉRIE \- TARDE  
  * 3ª SÉRIE \- NOITE  
  * EJA ETAPA V \- NOITE  
  * EJATEC MOD 01 \- NOITE  
  * EJATEC MOD 03 \- NOITE  
  * EJATEC MOD 05 \- NOITE  
* A grade horária irá mostrar as disciplinas e os seus horários estritamente correspondentes à turma selecionada.  
* **Nota Técnica (Gatilho de Dados):** A alteração do valor neste seletor serve como o "gatilho" principal da tela. Ao trocar a turma, o frontend fará uma chamada API (via HTMX/Fetch) ao backend (FastAPI) para buscar exclusivamente os registos daquela turma, limpando e redesenhando a tabela na hora.

**Estrutura da Tabela:**

Crie uma tabela (Matrix) responsiva com scroll (X e Y) e barras de rolagem personalizadas.

* **Eixo Y (Esquerda \- Fixo/Sticky):** Horários (ex: 07:30 às 08:30). Ao passar o rato num horário, deve aparecer um ícone "Edit" sutil para editar essa linha. No cabeçalho da coluna "HORÁRIO", coloque um botão "+" para adicionar novos horários.  
* **Eixo X (Topo \- Fixo/Sticky):** Dias da semana (Segunda a Domingo). Sábado e Domingo devem ter um fundo ligeiramente mais escuro (slate-50) para se diferenciarem visualmente.  
* **Células Vazias:** Ao passar o rato (hover), mostra um botão circular com um ícone "+" centralizado para "Alocar Disciplina".  
* **Células Preenchidas:** Um "card" com borda lateral esquerda azul, contendo o nome da Disciplina. Ao passar o rato, mostra um ícone "external-link".

  ### **5.2. Sistema de Modais e Slide-overs (Ações)**

Implemente um backdrop escuro e as seguintes janelas ocultas (acionadas por JS e integradas via API no backend):

* **Modal "Adicionar/Editar Horário" (Central):**  
  * Inputs de "Hora Início" e "Hora Fim" (type="time"). Botões Cancelar e Guardar.  
* **Modal "Alocar Disciplina" (Central):**  
  * Abre ao clicar num "+" de um slot vazio.  
  * Mostra o dia e hora selecionados (read-only).  
  * Um dropdown dinâmico para escolher a Disciplina. Botão "Alocar".  
* **Slide-over "Registo de Aula / Execução" (Lateral Direita, largo \- 850px):**  
  * Abre ao clicar num card de disciplina preenchido.  
  * **Header (Read-only):** Mostra Turma, Disciplina, Data/Horário e Estúdio.  
  * **Formulário Esquerdo (Execução):**  
    * Selects para: Tipo de Aula, Turno, Canal Utilizado e Atividade Prática.  
    * Textarea para "Conteúdo Ministrado" (limite 100 caracteres). Alerta abaixo a pedir para usar P1/P2/P3 em aulas geminadas.  
    * Textarea para "Observações Gerais".  
    * **Naming Engine Preview (Crítico):** Um painel escuro (slate-950) com texto monoespaçado verde. Conforme o utilizador digita, gera em tempo real o nome do ficheiro, estritamente no formato `[MODALIDADE] [SERIE] [TURNO] [DISC] [DATA] [CONTEUDO].mp4` (sem hífens ou underlines). Deve incluir lógica de sanitização em tempo real para remover acentos e caracteres especiais do campo "Conteúdo".  
  * **Formulário Direito (Ocorrências / Compliance / Recursos):**  
    * Checkboxes/Selects para: Interação Professor/Aluno, Recursos Utilizados e Problema com Material. Lógica condicional: se "Outro" for selecionado, abrir input de texto.  
    * Checkboxes de Ocorrência: Substituição de Professor e Atraso no Início. Lógica Accordion: expande-se suavemente exigindo o Professor Substituto ou os Minutos/Motivo do Atraso.  
    * Botão Vermelho de "Cancelar Aula (RN-05)": ao ser clicado, expande justificativa.  
  * **Rodapé:** Botões "Cancelar(Vermelho)", "Salvar Rascunho" (Amarelo) e "Finalizar" (Verde).

  ### **5.3. Tela de Relatórios e Auditoria (Nova)**

Painel dedicado para Gestores e Auditores realizarem buscas, verificações de *compliance* e exportações para faturamento.

* **Listagem Principal (DataGrid):** Tabela de exibição de relatórios.  
  * A especificação deve exigir **Paginação no Servidor (Server-side Pagination)** para evitar gargalos de performance. Padrão de 50 relatórios por página, adicionando um seletor no rodapé para quantidade por página `[20, 50, 100]`.  
  * **Ordenação:** O padrão deve ser ordenação decrescente pela `data_aula` (para ver rapidamente a operação do dia corrente), com a opção de o utilizador alternar para `created_at` caso precise fazer uma auditoria de produtividade da equipa (saber quando o registo foi de facto inserido no sistema).  
  * **Ação Individual:** Clicar numa linha da tabela deve abrir o "Slide-over" do relatório em modo *Read-Only* (apenas leitura).  
* **Barra de Filtros (Pesquisa Específica):**  
  * *Filtros Acadêmicos:* Data/Período, Professor, Disciplina, Modalidade, Turma.  
  * *Filtros de Compliance (Críticos):*  
    * **Status do Relatório:** (Rascunho, Finalizado, Cancelado). Essencial para saber o que falta faturar ou conferir.  
    * **Estúdio:** (Estúdio 01 a 09, Externo). Crítico para descobrir se um estúdio específico está a ter muitas falhas de operação.  
    * **Ocorrências (Filtros Booleanos):** "Mostrar apenas com Atraso", "Mostrar apenas com Substituição", "Mostrar apenas com Problema Técnico". (Considerado o "ouro" para a auditoria rápida).  
* **Exportação de Dados:**  
  * Deve conter um botão de **"Exportar Relatório em Massa (Excel/CSV)"**.  
  * A exportação deve respeitar estritamente os filtros aplicados na tela no momento do clique, entregando um ficheiro planilhado ideal para o fecho de faturamento e relatórios gerenciais.

  ### **5.4. Tela de Gestão de Acessos (Admin Only)**

Painel restrito a utilizadores com perfil de Administrador para a gestão centralizada do sistema e da equipa (IAM \- Identity and Access Management).

* **Adicionar Utilizador (Onboarding Seguro):**  
  * O formulário de "Adicionar Utilizador" deve pedir apenas **Nome**, **E-mail Institucional** e a seleção do **Perfil**.  
  * O sistema encarrega-se de gerar um link único, enviando-o para o e-mail do utilizador convidado, sendo este o responsável por definir a sua própria palavra-passe secreta (alinhado com o tópico 2.1 do documento).  
* **Ativar / Desativar Utilizadores (Soft Delete):**  
  * O sistema usará *Soft Delete* (Desativação lógica) em vez de exclusão permanente para preservar a integridade referencial dos relatórios e da auditoria.  
  * Quando uma conta for desativada, o sistema deve **cortar imediatamente a sessão ativa** (invalidar o JWT), impedindo que o funcionário desligado continue a usar a plataforma, mesmo que já esteja logado na sua máquina.  
* **Associação de Perfis (RBAC Fixo):**  
  * Para garantir segurança e evitar a complexidade do RBAC dinâmico, os perfis de acesso do sistema são fixos no código (Admin, Gestor, Auditor, Assistente).  
  * A tela do Administrador foca apenas em **Associar** a qual (ou quais) destes perfis fixos o utilizador pertence.  
* **O "Vigia" do Sistema (Logs de Auditoria de Acesso):**  
  * A tela deve conter uma aba ou secção dedicada ao "Log de Auditoria de Acessos".  
  * Deve mostrar um histórico claro de eventos (ex: *"Admin X convidou Utilizador Y no dia Z"*, ou *"Admin X desativou a conta de Utilizador W"*).  
  * **Trilha de Auditoria (Security Log):** Deve ser um registo inalterável das ações de promoção de perfil, envio de convites e desativação de contas realizadas pelos administradores, garantindo a rastreabilidade total de quem deu poder a quem.

  ### **5.5. Tela de Live Monitor (Operação em Tempo Real)**

Painel estilo NOC (Network Operations Center), estritamente "Read-Only" (apenas visualização), desenhado para acompanhamento global da operação dos estúdios.

* **Barra Superior (Contexto Live):**  
  * Relógio em tempo real e exibição fixa da data de Hoje (sem navegação temporal).  
  * **Seletor de Turma:** Dropdown para selecionar uma turma. Em vez de apagar os outros dados, a seleção de uma turma deve atuar como um *Highlight* (iluminando apenas o estúdio e horário onde essa turma está e ofuscando o resto).  
* **Estrutura da Matriz Operacional:**  
  * **Eixo X (Topo \- Fixo):** Horários do dia (ex: 07:00, 08:00, ..., 21:00) \[deve estar relacionado ao arquivo "horario.csv" que tem os horários definidos\].  
  * **Eixo Y (Esquerda \- Fixo):** Lista de todos os Estúdios (Estúdio 01 ao Estúdio 09).  
* **Interseção (Cards de Aula):**  
  * Nos cruzamentos de Estúdio vs. Horário, o sistema exibe um card com os dados herdados da grade (Disciplina e Turma e Professor).  
  * Nenhuma ação de edição é permitida ao clicar no card.  
* **Telemetria de Status (Cores):**  
  * O card altera visualmente a sua cor com base no status do relatório de aula no exato momento:  
    * 🔴 **PENDENTE (Alerta):** Horário ativo, mas o assistente ainda não iniciou o registo.  
    * 🟡 **RASCUNHO:** O assistente já abriu o formulário e começou a preencher, mas não validou a nomenclatura.  
    * 🟢 **FINALIZADO:** Aula concluída, nomenclatura gerada e pronta.  
    * ⚪ **CANCELADO:** Aula relatada como cancelada.

Requisitos de Higienização e Conteúdo
Preservar as letras maiúsculas e minúsculas originais digitadas pelo usuário (não forçar uppercase).

Remover todos os acentos utilizando normalização adequada (ex: á vira a, ç vira c).

Remover todos os caracteres especiais, incluindo _ . , : ; ! ? / \ () [] {}, além de emojis e símbolos.

Reduzir espaços múltiplos para apenas um espaço simples.

Regras de Nomenclatura do Arquivo
Estruturar o nome base estritamente no formato: [TIPO] [SERIE] [TURNO] [DISCIPLINA] [DIA] [MES] [ANO] [CONTEUDO].

Separar os termos exclusivamente por espaços (proibido o uso de hífens ou underlines).

Remover automaticamente o prefixo "REGULAR" dos nomes dos arquivos.

Impedir a duplicação de palavras no nome gerado.

Garantir que a extensão final do arquivo seja sempre .mp4 (estritamente em letras minúsculas).

Corrigir automaticamente erros de extensão durante o pipeline (ex: converter .MP4 para .mp4 e reduzir .mp4.mp4 para .mp4).

Parâmetros de Busca no Google Drive
Configurar a query principal para buscar pelo nome base gerado (name contains '{nome_base}').

Restringir a pesquisa para a pasta institucional correta utilizando a variável GOOGLE_DRIVE_VIDEOS_FOLDER_ID ('{FOLDER_ID}' in parents).

Habilitar a busca global nos drives da instituição (supportsAllDrives=True, includeItemsFromAllDrives=True, corpora="allDrives").

Filtrar estritamente por arquivos de vídeo (mimeType contains 'video') e ignorar arquivos na lixeira (trashed=false).

Implementar correspondência flexível (Match Flexível) no backend para ignorar divergências de acentuação, maiúsculas/minúsculas e subpastas entre o nome gerado e o arquivo real no Drive.

Acionar um fallback de busca utilizando os componentes de data (DD MM AA) caso a busca inicial pelo nome completo falhe.

Regras de Negócio e Compliance
Classificar o status do vídeo como VERDE (encontrado), PENDENTE (ainda não localizado no Drive) ou VERMELHO (não encontrado após o limite de tentativas).

Executar um fluxo de retry automático via Celery caso o vídeo não seja encontrado na primeira tentativa (1 tentativa por hora, limite máximo de 15 horas).

Rodar uma rotina de sincronização noturna todos os dias às 03:00 da manhã para varrer e reprocessar todos os relatórios com status pendente.

Disponibilizar um endpoint (POST /api/v1/reports/force-sync-drive) para permitir a sincronização manual e imediata pelo operador.



