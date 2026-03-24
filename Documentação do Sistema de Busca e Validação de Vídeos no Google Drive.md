# Documentação do Sistema de Busca e Validação de Vídeos no Google Drive

Este documento detalha a arquitetura, as regras de negócio e o fluxo de funcionamento do sistema automatizado de higienização, nomenclatura e busca de arquivos de vídeo institucionais no Google Drive.

---

## 1. Requisitos de Higienização e Conteúdo

O pipeline de tratamento de dados (Sanitization) prepara os inputs do usuário garantindo a padronização antes de qualquer busca. As seguintes regras são aplicadas rigorosamente:

* **Preservação de Caixa:** Mantém as letras maiúsculas e minúsculas originais digitadas pelo usuário (não força *uppercase*).
* **Normalização de Acentos:** Remove todos os acentos utilizando normalização adequada (ex: `á` vira `a`, `ç` vira `c`).
* **Limpeza de Caracteres Especiais:** Remove todos os caracteres especiais, incluindo `_`, `.`, `,`, `:`, `;`, `!`, `?`, `/`, `\`, `()`, `[]`, `{}`, além de emojis e símbolos.
* **Redução de Espaços:** Reduz espaços múltiplos para apenas um espaço simples.

---

## 2. Regras de Nomenclatura do Arquivo

Para garantir a conformidade dos relatórios, o sistema gera e espera uma estrutura estrita para os nomes dos arquivos:

* **Estrutura Base Estrita:** O nome deve seguir exatamente o formato: 
  `[TIPO] [SERIE] [TURNO] [DISCIPLINA] [DIA] [MES] [ANO] [CONTEUDO]`
* **Separadores:** Os termos devem ser separados exclusivamente por espaços (é terminantemente proibido o uso de hífens ou underlines).
* **Remoção de Prefixos:** O prefixo `"REGULAR"` é automaticamente removido dos nomes dos arquivos.
* **Prevenção de Duplicidade:** O sistema impede a duplicação de palavras no nome gerado.
* **Extensão Obrigatória:** A extensão final do arquivo deve ser sempre `.mp4` (estritamente em letras minúsculas).
* **Correção Automática de Extensão:** O pipeline corrige erros de extensão automaticamente (ex: converte `.MP4` para `.mp4` e reduz extensões duplas como `.mp4.mp4` para `.mp4`).

---

## 3. Parâmetros de Busca no Google Drive

A integração com a API do Google Drive foi configurada para ser altamente resiliente e abrangente, utilizando os seguintes parâmetros:

* **Query Principal:** A busca inicial é feita pelo nome base gerado: `name contains '{nome_base}'`.
* **Restrição de Diretório:** A pesquisa é restrita à pasta institucional correta através da variável de ambiente: `'{FOLDER_ID}' in parents`.
* **Busca Global e Drives Compartilhados:** Habilitada a busca global nos drives da instituição utilizando os parâmetros: 
  * `supportsAllDrives=True`
  * `includeItemsFromAllDrives=True`
  * `corpora="allDrives"`
* **Filtros de Tipo e Lixeira:** Restringe os resultados estritamente a arquivos de vídeo (`mimeType contains 'video'`) e ignora arquivos deletados (`trashed=false`).
* **Match Flexível no Backend:** Implementação que ignora divergências de acentuação, maiúsculas/minúsculas e subpastas entre o nome gerado pelo sistema e o arquivo real hospedado no Drive.
* **Fallback de Busca:** Caso a busca inicial pelo nome completo falhe, o sistema aciona uma busca secundária utilizando os componentes de data (`DD MM AA`).

---

## 4. Regras de Negócio e Compliance

O ciclo de vida da validação de um vídeo segue fluxos assíncronos e status de monitoramento rigorosos:

* **Classificação de Status:**
  * 🟢 **VERDE:** Vídeo encontrado e validado.
  * 🟡 **PENDENTE:** Vídeo ainda não localizado no Drive.
  * 🔴 **VERMELHO:** Vídeo não encontrado após o limite máximo de tentativas.
* **Fluxo de Retry Automático (Celery):** Caso o vídeo não seja encontrado na primeira tentativa, o relatório entra em uma fila de retentativas (1 tentativa por hora, com limite máximo de 15 horas).
* **Sincronização Noturna:** Uma rotina automática de varredura e reprocessamento roda todos os dias às **03:00 da manhã** para todos os relatórios com status pendente.
* **Sincronização Manual:** O sistema disponibiliza o endpoint `POST /api/v1/reports/force-sync-drive` para permitir a sincronização manual e imediata por um operador.

---

## 5. Capacidades e Limitações do Sistema

A arquitetura garante uma altíssima tolerância a falhas, blindando o sistema contra a grande maioria dos erros humanos, desde que o mínimo da estrutura seja respeitada.

### 🟢 O que o sistema CONSEGUE achar (Superpoderes)
* **Erros de digitação comuns:** O sistema encontra o arquivo independentemente do uso de acentos, variações de maiúsculas/minúsculas ou underlines (ex: `ANÁLISE LINGUÍSTICA`, `Analise Linguistica` ou `ANALISE_LINGUISTICA` darão *match* com a expectativa `ANALISE LINGUISTICA`).
* **Confusão com a extensão:** Arquivos salvos como `video.MP4`, `video.Mp4` ou `video.mp4.mp4` são corrigidos e localizados.
* **Vídeos perdidos em subpastas ou Shared Drives:** Graças às permissões globais, o arquivo é encontrado mesmo oculto em subpastas (ex: pasta "Março") ou Drives Compartilhados da equipe, desde que pertença à árvore da pasta principal.
* **Nomes parcialmente incompletos:** Através do *Fallback de data (DD MM AA)*, se a série, disciplina e data baterem, o sistema consegue contornar divergências no nome do conteúdo específico.

### 🔴 O que o sistema NÃO VAI achar (Limites da Arquitetura)
* **Vídeos salvos fora da pasta oficial:** Por segurança e compliance, a busca é restrita ao `GOOGLE_DRIVE_VIDEOS_FOLDER_ID`. Vídeos esquecidos no "Meu Drive" pessoal do professor não serão encontrados.
* **Nomes completamente fora do padrão:** Arquivos nomeados de forma genérica (ex: `aula_de_hoje_final.mp4` ou `video_whatsapp_123.mp4`) impossibilitam a associação ao relatório. O status ficará VERMELHO.
* **Formatos não suportados:** Arquivos de vídeo que não sejam `.mp4` (como `.mov`, `.avi`, `.mkv`) serão barrados pela regra de conformidade, mesmo sendo vídeos válidos.
* **Arquivos na lixeira:** O filtro `trashed=false` impede a validação de vídeos que foram enviados, mas deletados acidentalmente.

*(Nota: A garantia de 100% de sucesso depende exclusivamente do treinamento operacional básico da equipe para alocar o arquivo na pasta correta e usar a estrutura base de nomenclatura).*

---

## 6. A Lógica de Busca e Tratamento (O Passo a Passo)

1. **Ingestão:** O sistema recebe os dados brutos da aula (Tipo, Série, Turno, Disciplina, Data e Conteúdo).
2. **Higienização (Sanitization):** O algoritmo varre o nome do conteúdo. Mantém o *case* (maiúsculas/minúsculas), remove acentos, pontuações, emojis e o termo "REGULAR". Espaços múltiplos são reduzidos a um.
3. **Montagem do Nome Base:** Os fragmentos são unidos no formato rigoroso: `[TIPO] [SERIE] [TURNO] [DISCIPLINA] [DIA] [MES] [ANO] [CONTEUDO].mp4`.
4. **Busca Primária (Match Flexível):** Consulta à API do Drive buscando `name contains '{nome_base}'` e `mimeType contains 'video'`. A tolerância da API e o tratamento do backend garantem que acentuações não impeçam o *match*.
5. **Busca Secundária (Fallback):** Se a busca exata falhar, o sistema isola as variáveis vitais (Série, Disciplina e Data) e faz uma nova varredura no Drive.
6. **Sincronização/Retries:** Se o arquivo não for encontrado em nenhuma das buscas, o Celery enfileira o relatório para retentativas horárias (até 15h) e submete à rotina da madrugada.

---

## 7. Exemplos Práticos: Do Caos à Conformidade

### Cenário 1: O "Festival de Caracteres Especiais"
* **Situação:** O professor usou pontuações no sistema e salvou o arquivo nativo mantendo acentos e extensão maiúscula.
* **Conteúdo Original (Sistema):** `Análise Linguística! - (Texto & Discurso)`
* **Nome Nativo (Drive):** `EM 3 TARDE Análise Linguística 02 03 26 Texto & Discurso.MP4`
* **Como o Sistema Limpa:** Remove `!`, `-`, `()`, `&` e tira os acentos. Resultado: `Analise Linguistica Texto Discurso`.
* **Nome Base Gerado:** `EM 3 TARDE Analise Linguistica 02 03 26 Texto Discurso.mp4`
* **A Mágica:** O Match Flexível ignora a extensão `.MP4`, acentos e símbolos no Drive.
* **Status:** 🟢 **VERDE** (Encontrado na hora).

### Cenário 2: O "Prefixo Proibido e Extensão Dupla"
* **Situação:** O professor copiou o nome sujo do sistema escolar com o prefixo "REGULAR" e salvou o arquivo com extensão duplicada.
* **Conteúdo Original (Sistema):** `REGULAR Inteligência Artificial: Conceitos`
* **Nome Nativo (Drive):** `REGULAR EM 3 NOITE Inteligência Artificial 10 03 26 Conceitos.mp4.mp4`
* **Como o Sistema Limpa:** Corta a palavra "REGULAR", remove os dois pontos (`:`) e limpa acentos. Resultado: `Inteligencia Artificial Conceitos`.
* **Nome Base Gerado:** `EM 3 NOITE Inteligencia Artificial 10 03 26 Conceitos.mp4`
* **A Mágica:** Reduz a extensão `.mp4.mp4` para `.mp4`, ignora o prefixo e encontra o arquivo nativo.
* **Status:** 🟢 **VERDE** (Encontrado na hora).

### Cenário 3: O "Esquecido" (Ativando o Fallback de Data)
* **Situação:** O professor fez o básico, mas esqueceu de incluir o tema específico no nome do arquivo no Drive.
* **Conteúdo Original (Sistema):** `Geografia Política e Industrialização P2`
* **Nome Base Esperado:** `EM 2 MANHA Geografia 15 03 26 Geografia Politica e Industrializacao P2.mp4`
* **Nome Nativo (Drive):** `EM 2 MANHA Geografia 15 03 26.mp4`
* **A Mágica:** A busca principal falha por ser muito curta. O Fallback é acionado, isola o termo `EM 2 MANHA Geografia 15 03 26`, varre o Drive, verifica o `mimeType` de vídeo e confirma que não está na lixeira.
* **Status:** 🟢 **VERDE** (Encontrado via Fallback).

### Cenário 4: O "Fora da Lei" (Limite da Arquitetura)
* **Situação:** O professor ignorou o treinamento e subiu um arquivo genérico fora do formato `.mp4`.
* **Conteúdo Original (Sistema):** `Matemática Básica Conjuntos`
* **Nome Base Esperado:** `EM 3 MANHA Matematica 20 03 26 Matematica Basica Conjuntos.mp4`
* **Nome Nativo (Drive):** `video_aula_terceirao_final_oficial.mov`
* **A Mágica (e o Limite):** A busca principal falha. O Fallback tenta buscar pela data `20 03 26`, que não existe no nome do arquivo. A regra também barra o formato `.mov`.
* **Fluxo:** O status vai para **PENDENTE**. O Celery inicia os *retries* de hora em hora. A rotina das 03:00 varre a base. Se o arquivo não for corrigido e colocado no padrão nas próximas 15 horas...
* **Status:** 🔴 **VERMELHO** (Não encontrado após limite de tentativas).