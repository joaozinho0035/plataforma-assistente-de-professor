# Relatório de Arquitetura de Segurança e Acessos

**Nota de Escopo:** Esta análise foi realizada estritamente em modo *Read-Only*, garantindo que nenhuma alteração foi sugerida para substituição direta ou aplicada nos arquivos.

---

## 1. [Perfis Mapeados]

Abaixo estão listados os `Roles` (Perfis) explicitamente definidos e suportados pelo sistema, extraídos principalmente de [app/models/user.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/models/user.py) e [app/api/rotas_auth.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_auth.py):

| Perfil | Descrição Encontrada | Menor Privilégio Ideal |
| :--- | :--- | :--- |
| **admin** | Administrador do sistema. Possui acesso total (criação de outros admins, exclusão de registros, desativação de contas). | Acesso irrestrito a configurações e auditoria. |
| **gestor** | Nível gerencial. Pode convidar novos usuários e listar todos os usuários, mas não pode usar funções de soft-delete ou reatribuição de perfis. | Gestão operacional, visualização de painéis e exportação de dados gerais. |
| **auditor** | Perfil com viés de leitura/fiscalização (citado como válido em `valid_roles`, mas sem rotas exclusivas definidas no momento). | Leitura em logs de auditoria e exportação de relatórios. |
| **assistente** | Perfil padrão concedido aos novos usuários. Operador de chão de fábrica. | Apenas criação e edição dos *seus próprios* relatórios/rascunhos. |

---

## 2. [Matriz de Permissões Atual - AS IS]

Este é o cenário existente mapeado no código. Ele cruza os endpoints (Recursos) com as funções de dependência associadas.

### 2.1. Rotas de Autenticação (`/api/v1/auth`)
| Endpoint | Ação / Funcionalidade | Proteção Adotada | Acesso Permitido |
| :--- | :--- | :--- | :--- |
| `POST /login` | Autenticação por Email e Senha | Nenhuma (Público) | Público |
| `POST /bootstrap` | Criação do 1º Admin | Condicional (Usuários == 0) | Público (se DB vazio) |
| `POST /confirm` | Confirmação de convite via token | Token no corpo da req. | Público (com token válido) |
| `GET /me` | Obter dados do próprio usuário | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |
| `GET /users` | Listar todos os usuários | [require_role("admin", "gestor")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin, gestor |
| `POST /invite` | Convidar novo usuário | [require_role("admin", "gestor")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin, gestor |
| `PATCH /users/{id}/deactivate` | Desativar conta (Soft Delete) | [require_role("admin")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin |
| `PATCH /users/{id}/activate` | Reativar conta | [require_role("admin")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin |
| `PATCH /users/{id}/role` | Alterar perfil de usuário | [require_role("admin")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin |
| `GET /audit-logs` | Visualizar Log de Auditoria | [require_role("admin")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin |

### 2.2. Rotas de Relatórios de Aula (`/api/v1/reports`)
| Endpoint | Ação / Funcionalidade | Proteção Adotada | Acesso Permitido |
| :--- | :--- | :--- | :--- |
| `GET /` e `GET /{id}` | Listar / Visualizar relatórios | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |
| `POST /` | Criar novo rascunho de relatório | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |
| `PATCH /{id}/finalizar` | Finalizar e sincronizar relatório | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |
| `PATCH /{id}/cancelar` | Cancelar relatório com justificativa | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |
| `POST /force-sync-drive` | Forçar sincronização noturna geral | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |
| `GET /export` | Exportar relatórios em CSV | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |
| `PUT /{id}` | Editar qualquer relatório finalizado | [require_role("admin")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin |
| `DELETE /{id}` | Excluír relatório do sistema | [require_role("admin")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) | admin |
| `GET /lookup/*` | Listar domínios (disciplinas, profs) | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |

### 2.3. Rotas de Aulas (`/aulas`) - *Legacy / Conflitantes*
| Endpoint | Ação / Funcionalidade | Proteção Adotada | Acesso Permitido |
| :--- | :--- | :--- | :--- |
| `GET /` | Listar todas as aulas | Nenhuma (`Depends(get_db)`) | **Público (Vulnerabilidade!)** |
| `GET /{id}` | Buscar aula específica | Nenhuma (`Depends(get_db)`) | **Público (Vulnerabilidade!)** |
| `POST /` | Registrar nova aula | [get_current_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#17-41) (Redefinido) | Autenticados (Bug presente)* |
| `PATCH /{id}/cancelar`| Cancelar aula | [get_current_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#17-41) (Redefinido) | Autenticados (Bug presente)* |

### 2.4. Rotas de Live Monitor (`/api/v1/live`)
| Endpoint | Ação / Funcionalidade | Proteção Adotada | Acesso Permitido |
| :--- | :--- | :--- | :--- |
| `GET /matrix` | Cruzamento Grade vs Relatórios | [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53) | admin, gestor, auditor, assistente |

---

## 3. [Análise Crítica de Vulnerabilidades]

A varredura Read-Only revelou furos sensíveis e falhas de design na implementação atual:

1. **Exposição de Informações Sensíveis (Endpoints Órfãos Públicos)**
   - No arquivo [app/api/rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py), os recursos `GET /aulas/` e `GET /aulas/{lesson_id}` **não possuem qualquer tipo de proteção de autenticação** (não injetam o parâmetro `current_user = Depends(...)`). Isso significa que visitantes anônimos e bots da internet podem baixar toda a base histórica de aulas criadas sem precisar de token.

2. **Crítico: Redefinição Bugada de Autenticação ([rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py))**
   - O arquivo [rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py) tenta reescrever manualmente seu próprio [get_current_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#17-41) e `oauth2_scheme`.
   - **O Bug**: Ele faz o decode do JWT localmente buscando o id por `User.username == username` (Linha 35). Contudo, no arquivo [app/models/user.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/models/user.py), **não existe a coluna `username`**, apenas [email](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/arquiv%20email). Qualquer chamada a `POST /aulas` resultará num *AttributeError* ou erro 500 no banco, quebrando a funcionalidade totalmente para qualquer usuário.
   - **Vulnerabilidade de Bypass**: Diferente do [deps.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py), a versão de [rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py) ***NÃO* verifica se a conta está banida (`is_active = False`) nem se o email foi confirmado**. Se um administrador desativar uma conta mal-intencionada, esse usuário ainda teoricamente logaria via endpoints antigos que usam essa redefinição, caso a query não estourasse na falta do `username`.

3. **Ausência de Segregação de Funções (Segregation of Duties) no Core**
   - Nas **Rotas de Relatório ([rotas_report.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_report.py))**, praticamente todas as operações de negócio usam [get_current_active_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#43-53).
   - Isso significa que o perfil "assistente" possui tanto poder quanto um "gestor". Um assistente pode:
     - Cancelar o relatório de qualquer outra pessoa.
     - `POST /force-sync-drive`: Acionar a sincronização pesada massiva com o Google Drive (possível alvo de DDoS interno agendando Celery repetidas vezes).
     - `GET /export`: Exportar em CSV toda a base confidencial de relatórios do sistema sem restrições de departamento ou autoria.

4. **Escopo do Log de Auditoria Bypassável via PATCH**
   - Ainda que os verbos estritos (`PUT /reports/{id}` e `DELETE /reports/{id}`) estejam blindados com [require_role("admin")](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70), qualquer `assistente` pode chamar as rotas de negócio de transição de estado (`PATCH /reports/{id}/cancelar` ou `PATCH /reports/{id}/finalizar`) corrompendo fluxos da escola (pois não há [require_role](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#55-70) nesses endpoints ou lógica verificando a autoria).

---

## 4. [Recomendações de Arquitetura - TO BE]

Para alcançar um selo de conformidade e aderir aos Princípios de Segurança da Informação, os seguintes passos arquiteturais devem ser endereçados:

### 4.1. Unificação do IAM e Dependências D.R.Y (Don't Repeat Yourself)
* **O Que Fazer:** Remover instantaneamente a redefinição isolada de [get_current_user](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/deps.py#17-41), `oauth2_scheme`, e da decodificação de JWT do arquivo [rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py).
* **Justificativa:** Centralizar a autorização em `app.api.deps` assegura que todos os endpoints chequem invariavelmente os booleanos de segurança vitais (`is_active` e `email_confirmed`). Reduz superfície de ataque e elimina o bug crítico da coluna `username` invisível que está quebrando a aplicação.
* **Ação TO-BE:** O arquivo [rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py) deve apenas importar e utilizar `current_user = Depends(get_current_active_user)`.

### 4.2. Blindagem e Princípio do Menor Privilégio na Camada de Relatórios
* **O Que Fazer:** Aplicar Controle de Acesso Baseado em Propriedade (Ownership) e RBAC Restrito.
* **Justificativa TO-BE:**
  1. **Endpoints Destrutivos/Alteradores (`PATCH cancelar/finalizar`)**: Continuar permitindo assistentes, MAS no corpo da rota garantir que: `if report.created_by != current_user.id and current_user.role not in ["admin", "gestor"]: raise HTTP 403`. O assistente só pode interagir com os relatórios que ele mesmo criou.
  2. **Vazamento de Dados (`GET /export`)**: Travar estritamente com `Depends(require_role("admin", "gestor", "auditor"))`. Assistentes de operação não devem extrair os relatórios financeiros de todas as aulas em CSV.
  3. **Rotas de Sistema (`POST /force-sync-drive`)**: Travar estritamente com `Depends(require_role("admin", "gestor"))`. Apenas a gerência deve forçar ações pesadas contra a infraestrutura/APIs Google.

### 4.3. Fechamento Imediato de Rotas Públicas Vazadas (`GET /aulas`)
* **O Que Fazer:** Injetar o decorador ou dependência de verificação ao instanciar os verbos `GET` em [rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py).
* **Justificativa:** O sistema não foi desenhado para ser uma API aberta B2C. Todos os painéis requerem login de rede. Fechá-las imediatamente com `current_user = Depends(get_current_active_user)` previne *data-scraping* anônimo.

### 4.4. Governança e Validação Funcional
* **O Que Fazer:** Remover rotas legadas.
* **Justificativa:** Observa-se que existem dois módulos lidando com Aulas: [rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py) e [rotas_report.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_report.py). Parecem versões distintas (um legado e um novo com mais validações de compliance drive/condicionais). A recomendação arquitetural TO-BE é **depreciar completamente** [rotas_lesson.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_lesson.py) se [rotas_report.py](file:///c:/Users/Paulo/OROS/ce_assistente_professores%20%2812%29/ce_assistente_professores/app/api/rotas_report.py) for seu substituto (v3.0), ou, no mínimo, aplicar as mesmas travas de autenticação supracitadas.  
* Isso evitará *Shadow Endpoints* onde invasores ou usuários encontram portas legadas para burlar o Naming Engine mais rigoroso do `/api/v1/reports`.
