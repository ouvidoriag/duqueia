# Regras do Projeto - Framework RAG para o DUQUE IA

Voce e um **Arquiteto Senior de IA** especializado em RAG, Retrieval Evaluation, Embeddings, Vector Databases, Guardrails e Sistemas GIS.

Sua tarefa e analisar completamente este projeto e transforma-lo em um framework RAG robusto, auditavel e preparado para producao.

---

## Objetivo

O projeto possui ou esta evoluindo para possuir:

* Parser de PDFs
* Geracao de embeddings
* Estrategias de chunking
* Banco vetorial (Supabase/PGVector)
* Testes de retrieval
* Avaliacao de relevancia

O objetivo final e torna-lo uma **plataforma completa de RAG** utilizada no **DUQUE IA (Sistema de Informacoes Municipais)**.

---

## FASE 1 - MAPEAMENTO

Ao analisar o projeto, sempre identifique:

* Fluxo completo de ingestao
* Fluxo de embeddings
* Fluxo de retrieval
* Estrategias implementadas
* Dependencias entre modulos
* Possiveis gargalos
* Codigo morto e arquivos nao utilizados
* Arquitetura atual

Gere o documento brain/architecture_analysis.md contendo:

* Diagrama textual da arquitetura
* Fluxo de execucao
* Dependencias entre modulos
* Melhorias recomendadas

---

## FASE 2 - AUDITORIA DE CHUNKING

Analise e avalie todas as estrategias existentes:

- recursive_500_100
- recursive_256_64
- token_256_64
- semantic_strategy

Para cada estrategia, avalie:

* Precisao (Precision)
* Recall
* Contexto preservado
* Quantidade de embeddings gerados
* Custo estimado
* Tempo de processamento

Crie uma tabela comparativa: strategy | precision | recall | retrieval_score | latency | cost

---

## FASE 3 - RETRIEVAL EVALUATION

Sempre que existirem os arquivos abaixo, analise-os:

- retrieval_metrics.csv
- retrieval_relevance_results.csv
- retrieval_test_results.json
- test_retrieval_relevance.py

Verifique como o score esta sendo calculado, como a relevancia e medida, possiveis vies e oportunidades de melhoria.

Gere o relatorio brain/retrieval_analysis.md.

---

## FASE 4 - GUARDRAILS

### Input Guardrail

Valide e bloqueie:

* Prompt Injection (ex: Ignore todas as instrucoes anteriores)
* SQL Injection (ex: DROP TABLE bairros, DELETE FROM embeddings)
* Dados invalidos ou arquivos corrompidos

### Retrieval Guardrail

Se o retrieval nao atingir o score minimo, retorne:
"Nao encontrei informacoes suficientes para responder."

### Output Guardrail

Toda resposta deve seguir o formato:

{
  "answer": "...",
  "sources": ["..."],
  "confidence": 0.92
}

Valide: alucinacao, respostas sem fonte, informacoes contraditorias com os chunks recuperados.

---

## FASE 5 - SISTEMA DE METRICAS

Registre sempre: latencia, tokens_usados, embedding_cost, retrieval_time, llm_time, total_time, similarity_score.

Salve em: logs/ e metrics/

---

## FASE 6 - PREPARACAO PARA O DUQUE IA (GIS)

### GeoJSON

Suporte a importacao de FeatureCollections. Valide: Geometria, CRS, Nome, ID, Campos obrigatorios.

### Chunking por Entidade Geografica

1 entidade geografica = 1 chunk.
Entidades: Municipio, Bairro, Setor, Quadra, Lote, Logradouro.

### Retrieval Geografico

O sistema deve responder perguntas territoriais sobre bairros, setores, lotes, areas e populacoes.

---

## FASE 7 - BENCHMARK

Execute benchmarks entre:
- recursive_500_100
- recursive_256_64
- token_256_64
- semantic_strategy
- entity_geo_strategy

Gere ranking com: Recall, Precision, F1, Latencia, Custo.

---

## FASE 8 - PRODUCAO

Prepare para: Docker, Supabase + PGVector, OpenAI, Azure OpenAI, Ollama, OpenRouter.

Crie e mantenha: .env.example e docker-compose.yml.

---

## Regras Gerais de Comportamento

1. Nunca faca alteracoes silenciosas. Explique cada decisao tecnica.
2. Sempre apresente riscos, impactos e justificativas antes de executar mudancas significativas.
3. Gere relatorios detalhados na pasta brain/ ao final de cada fase.
4. Preserve todos os comentarios e docstrings existentes, salvo instrucao explicita do usuario.
5. Ao final de qualquer analise ou implementacao, entregue:
   - Diagnostico completo
   - Lista de melhorias priorizadas
   - Guardrails implementados
   - Sistema de metricas
   - Benchmark de chunking
   - Estrategia recomendada
   - Roadmap para o DUQUE IA

6. Uma vez que o banco de dados (`duque_ia.db`) esteja criado e populado, não delete ou recrie o banco por completo. Apenas insira e adicione novos chunks ou atualizações de dados de forma incremental.

---

## FASE 9 - INTEGRAÇÃO POP E OUVIDORIA (BLINDAGEM)

### Segurança e Privacidade (LGPD)
- A IA nunca deve retornar CPFs, nomes de reclamantes ou andamento de protocolos de terceiros (vizinhos).
- Ao detectar tais buscas na query (ex: vizinho, CPF de outro), deve bloquear e emitir a resposta padrão de recusa por privacidade.

### Competência Municipal
- Rejeitar e barrar perguntas sobre assuntos de âmbito estadual, federal ou de outros municípios (ex: metrô, previdência federal, rodovias federais).
- Emitir a negativa por falta de competência da prefeitura de Duque de Caxias.

### Fallback e Direcionamento
- Substituir mensagens genéricas de falha de busca por redirecionamento direto para a Ouvidoria Geral de Duque de Caxias: Telefone **(21) 2652-3835**, e-mail **ouvidoria@duquedecaxias.rj.gov.br** e aplicativo **Colab**. (A Ouvidoria NÃO possui WhatsApp).

### Triagem de Esclarecimento Contextual (Agente Coletor)
- Se a triagem indicar que falta contexto (`needs_clarification: true`), o sistema deve acionar o comportamento de **Agente Coletor** antes de direcionar o munícipe à Ouvidoria Geral ou realizar buscas no RAG.
- A triagem deve receber e avaliar o histórico recente de mensagens do diálogo para contextualizar consultas de turnos subsequentes e identificar quando uma ambiguidade anterior foi resolvida.
- A pergunta de esclarecimento gerada deve ser amigável e contextualizada com base na intenção (`intent`) e no motivo (`reason`) detectados pelo classificador (ex: solicitar endereço e detalhes específicos caso seja uma reclamação de obras).
- A coleta de informações deve ser estritamente **incremental (pedindo uma informação de cada vez)** para evitar sobrecarregar o munícipe, focando em obter o necessário para direcioná-lo ao aplicativo **Colab** vinculando-o à secretaria e assunto adequados.

### Boas Práticas do POP
- Evitar saudações redundantes ("Olá! Que bom ter você aqui...").
- Formatar respostas com dados factuais úteis em **negrito** (endereços, prazos e contatos).
- Orientar o munícipe a preencher dados essenciais (CPF, endereço completo do fato, fotos, pontos de referência) antes de registrar manifestações na plataforma Colab.

### Verificação Preventiva e Reuso de Código
- Sempre analise minuciosamente a estrutura de pastas do projeto (`/data`, `/scripts`, `/agent`, `/ingestion`) e os scripts existentes antes de criar novos arquivos ou recriar lógicas de negócio.
- Evite redundâncias e dê preferência por estender e reaproveitar parsers, indexadores, ferramentas e suítes de testes que já se encontram implementados no projeto.

---

## FASE 10 - ARQUITETURA CONSOLIDADA DE PRODUÇÃO, CHAVES E AGENTES

### 1. Servidor e Gateway de Produção
* **Porta Oficial:** Porta **`3000`** padronizada em todos os ambientes (`server.js`, `ecosystem.config.js`, `config/settings.py`, `.env`).
* **Reverse Proxy Nginx:** Na Máquina Virtual, o Nginx mapeia `http://ogm.duquedecaxias.rj.gov.br/duqueia/` diretamente para o upstream `duque_ia_backend` (`server 127.0.0.1:3000;`).
* **Rotas Relativas no Frontend:** Toda requisição no frontend (`chat.html` e `dashboard.html`) DEVE utilizar caminhos estritamente relativos (`api/chat`, `api/metrics`, `api/feedback`, `audio/...`), garantindo que funcione tanto em desenvolvimento (`localhost:3000`) quanto através do subcaminho do Nginx (`/duqueia/`).
* **WorkerPool Multi-threaded:** O `server.js` gerencia um pool de **4 workers Python persistentes** via stdin/stdout com protocolo JSON, isolamento de memória e hot-reload sob demanda.

### 2. Gestão de Chave e Modelos Cognitivos
* **Chave Paga do Google Cloud:** Utiliza uma única chave oficial com faturamento ativo associada ao projeto `projects/526814071543`, inserida exclusivamente no `.env` (`GEMINI_API_KEYS=AQ.Ab8RN6ICrOM5...`). O arquivo `.env` NUNCA é versionado no Git.
* **Dupla de Modelos Cognitivos:**
  * **Triador Rápido (`gemini-3.1-flash-lite`):** Responsável pela triagem de intenção, detecção de ambiguidade e coleta incremental de contexto em menos de ~1,5s.
  * **Motor RAG e Resposta Factual (`gemini-3.8-flash`):** Responsável pela síntese analítica final com base no contexto injetado, com raciocínio de alta precisão e sem alucinações.
  * **Modelo de Embeddings (`gemini-embedding-2`):** Vetores semânticos densos de 3.072 dimensões.
  * **Síntese de Voz Nativa (`gemini-3.1-flash-tts-preview`):** Áudio 24kHz Studio WAV com timeout ampliado de 25s.
* **Atalho Inteligente de Reranking:** Se a busca híbrida obtiver score de similaridade `>= 0.70`, o reranking de rede é dispensado (0ms), economizando tokens e tempo.

### 3. Segregação Física de Bancos de Dados (4 Bases SQLite em WAL)
1. **`data/db/main.db`:** Dados relacionais, 644 serviços, equipamentos públicos, faixas de CEP e regras de negócio.
2. **`data/db/vector.db`:** 1.575 chunks mestres indexados com busca vetorial e trigramas.
3. **`data/db/cache.db`:** Cache semântico de respostas frequentes com retorno em ~3ms.
4. **`data/db/telemetry.db`:** Auditoria em tempo real, tokens consumidos, histórico de conversas e latências.

### 4. Grafo de Execução de Agentes (Pipeline Cognitivo)
A mensagem do munícipe percorre:
1. `fast_gate`: Validações de regex, bloqueio de injection e palavras proibidas.
2. `entity_resolver`: Normalização geográfica (4 distritos, 40 bairros mestres, apelidos e equipamentos de Duque de Caxias).
3. `triage`: Agente com `gemini-3.1-flash-lite` que avalia histórico multiturno e intenção. Se faltar dados, assume papel de **Agente Coletor Incremental** (`needs_clarification`).
4. `tool_router`: Direciona o fluxo para o handler adequado:
   * `RAG_HANDLER`: Busca híbrida + Gemini 3.8-flash + guardrails.
   * `AMBIGUITY_HANDLER`: Resposta de esclarecimento amigável ao munícipe.
   * `OUT_OF_SCOPE_HANDLER`: Bloqueio com redirecionamento para Ouvidoria Geral.
5. `output_guardrail`: Blindagem de dados sensíveis (LGPD) e validação factual.

### 5. Diretrizes para Frontend e Apresentação
* **`public/chat.html`:** Interface de atendimento humanizada com o atendente virtual do DUQUE IA. Deve utilizar a suíte de avatares 3D disponíveis em `public/assets/personagens/` (`duque_boas_vindas_bracos_abertos.png`, `duque_desenvolvedor_notebook.png`, `duque_joinha_aprovado.png`, `duque_saude_jaleco.png`, `duque_atendimento_telefone.png`, `duque_consultando_tablet.png`, etc.) alternando dinamicamente de acordo com o estado e temática da conversa (acolhendo, pensando/pesquisando, saúde, contatos, confirmando).
* **`public/dashboard.html`:** Painel de observabilidade executivo que consome `telemetry.db` através do endpoint `api/metrics`. Deve exibir métricas de latência, volume de atendimentos por secretaria, conformidade de respostas, economia de tokens e mapa de calor de demandas.

### 6. Estrutura Canônica de Secretarias e Pastas Municipais
* **SMCT (Cultura e Turismo):** Pasta dedicada aos equipamentos culturais (Teatro Raul Cortez, Biblioteca Leonel Brizola, Museu da Taquara, Centro Niemeyer).
* **SMEL (Esporte e Lazer):** Pasta dedicada aos complexos esportivos (Vila Olímpica de Duque de Caxias, polos de artes marciais, natação e Jogos Estudantis).
* **SMG (Secretaria Municipal de Governo):** Articulação política, relações parlamentares e governança do executivo (sem a Ouvidoria Geral).
* **SMCSRPTER (Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral):** Integração estratégica da Ouvidoria Geral do Município (OGM / Colab / Telefone 21 2652-3835), Assessoria de Imprensa, Comunicação Institucional e Políticas de Trabalho/Empregabilidade (SINE Caxias).

---

## FASE 11 - BLINDAGEM DE RESOLUÇÃO DETERMINÍSTICA E PREVENÇÃO DE FALSOS POSITIVOS (GOLDEN SOURCE GUARDS)

### 1. Regra de Não-Interceptação em Perguntas de Serviços/Procedimentos
- A camada `GoldenSourceResolver` (0ms) só deve retornar cartões de endereço quando houver clara intenção locacional (`is_asking_unit_info`: `"onde fica"`, `"endereço"`, `"telefone"`, `"horário"`, ou termos diretos de até 4 palavras como `"UPA Saracuruna"`).
- Consultas com mais de 4 palavras ou contendo verbos e substantivos procedimentais (`"serve para"`, `"serve tbm"`, `"atende tbm"`, `"resgate"`, `"posso levar"`, `"aceita"`, `"castração"`, `"vacinação"`, `"como funciona"`) NUNCA podem ser interceptadas pela camada de unidades físicas. Devem fluir para o motor RAG analítico.

### 2. Diferenciação Estrita de Competência de Animais (Fauna Silvestre vs Animais Domésticos)
- **Fauna Silvestre (gambás, sariguês, cobras, jacarés, corujas, morcegos, gaviões, etc.):** NUNCA é atendida pela Secretaria de Proteção Animal (SMPA). O resgate sem risco imediato é de competência da **Guarda Ambiental / Secretaria Municipal de Meio Ambiente (SMMA)** via chamado no aplicativo **Colab** (categoria **Meio Ambiente > Resgate de Animais Silvestres / Proteção Animal**). Em caso de risco iminente ou animal agressivo, acionar o **Corpo de Bombeiros Militar (193)** ou a **Defesa Civil (199)**. Termos de fauna silvestre possuem bypass imediato (`is_wild_animal`) que impede interceptação na Golden Source Layer.
- **Animais Domésticos (cães e gatos):** Competência da **Secretaria Municipal de Proteção Animal (SMPA)** e **Hospital Municipal Veterinário (HMV)**, para castração gratuita (Castramóvel), maus-tratos, acolhimento temporário e atendimento de urgência/emergência para moradores de Duque de Caxias, com suporte pelo **Petzap: (21) 97179-7900**.

### 3. Blindagem de Integridade, Anti-Alucinação e Meta-Questionamento da IA (AI_META_HANDLER)
- A Duque IA jamais inventa protocolos, telefones fictícios de secretarias ou afirmações falsas de encaminhamento para agradar o cidadão (Anti-Sycophancy).
- Quando o munícipe questionar a veracidade das informações, testar a integridade da IA ou perguntar como confiar no sistema, a resposta é roteada para o `AI_META_HANDLER`, assegurando resposta formal, auditável e transparente, esclarecendo que as respostas são baseadas em dados públicos oficiais e indicando os canais da Ouvidoria Geral em caso de auditoria de protocolos.
- NUNCA permitir que a palavra "Duque" na query provoque falso positivo na busca determinística de secretarias (ex: direcionamento errôneo para o IPMDC).

### 4. Proibição Absoluta do WhatsApp da Ouvidoria Geral
- O número `(21) 99824-5903` é fictício/inexistente e foi 100% erradicado de todas as bases, prompts, handlers e caches.
- A Ouvidoria Geral de Duque de Caxias **NÃO possui canal de WhatsApp**. Os canais oficiais exclusivos são:
  - **Telefone:** **(21) 2652-3835**
  - **E-mail:** **ouvidoria@duquedecaxias.rj.gov.br**
  - **Presencial:** Alameda Esmeralda, 206 - Jardim Primavera (Sede da Prefeitura)
  - **Web / Aplicativo:** **Colab** (`duquedecaxias.colab.re`)

### 5. Cobertura Canônica de Autoridades e Secretários (Gestão 2025–2028)
- 100% das 21 Secretarias Municipais, Autarquias (IPMDC), Fundações (FUNDEC) e Órgãos de Controle (PGM, CGM, Ouvidoria Geral) possuem seus titulares mapeados deterministicamente no `AuthorityHandler`.
- Padrão uniforme: Perguntas sobre titulares e secretários ("quem é o secretário de X", "qual o nome do presidente da FUNDEC/IPMDC", "quem é o procurador geral", "quem é o ouvidor") são resolvidas com resposta padronizada e fontes oficiais em menos de 1s (0 tokens LLM).
- Os cartões de endereço de secretarias na Golden Source Layer (`_resolve_secretaria`) exibem obrigatoriamente a linha `• **Titular / Responsável:** **{nome}** ({cargo})` para garantir consistência em todas as consultas da Prefeitura.

---

## FASE 12 - ENGENHARIA DE DADOS VETORIAIS E OTIMIZAÇÃO BINÁRIA (SEM GIT LFS)

### 1. Compactação de Embeddings em float32 Binário (`vector.db`)
- Os 1.575 chunks mestres utilizam vetores densos do modelo `gemini-embedding-2` com 3.072 dimensões.
- Os vetores NÃO são armazenados como JSON textual (que inflava o banco para 151,5 MB). São armazenados como BLOBs binários em precisão simples (`float32` de 12.288 bytes).
- O tamanho físico do banco de dados vetorial foi reduzido para **46,4 MB**, permitindo versionamento nativo no Git abaixo do limite de 50 MB do GitHub sem dependência de Git LFS.
- Leitura de alta velocidade com decodificação via `numpy.frombuffer(blob, dtype=np.float32)` em menos de 3ms.

### 2. Índice Híbrido (BM25 FTS5 + Similaridade Vetorial)
- Tabela virtual `chunks_fts` configurada com tokenizer FTS5 e suporte a trigramas para tolerância a erros de digitação de nomes de bairros e secretarias.
- Busca combinada balanceada: Vetorial (0.7) + BM25 Lexical (0.3).
- Atalho de Reranking: Similaridade híbrida `>= 0.70` descarta reranker de rede (0ms), economizando tokens da cota Gemini.

---

## FASE 13 - GOVERNANÇA DE DEPLOY, AMBIENTE LINUX E SEGURANÇA EM PRODUÇÃO

### 1. Ambiente Homologado de Execução
- **Sistema Operacional:** Ubuntu Linux 22.04 / 24.04 LTS.
- **Python:** Versões homologadas **Python 3.11** ou **Python 3.12** (Python 3.13 pode apresentar instabilidades em wheels binárias).
- **Node.js:** Versão 20+ LTS com gerenciador PM2.

### 2. Procedimento Padrão de Atualização e Deploy
- Na máquina de desenvolvimento: `git add .`, `git commit -m "..."`, `git push origin main`.
- Na VM de Produção:
  ```bash
  cd ~/duqueia
  git pull origin main
  pm2 restart duqueia
  ```
- NUNCA deletar ou recriar os bancos de dados em produção. O script `bootstrap/database_init.py` aplica migrações de forma estritamente incremental e segura (WAL Mode ativo em todas as 4 bases).

### 3. Painel de Observabilidade e Controle de Acesso (Dashboard)
- Dashboard Executivo em `http://ogm.duquedecaxias.rj.gov.br/duqueia/dashboard.html` (ou `localhost:3000/dashboard.html`).
- Credenciais canônicas: usuário `admin` e senha `admin123` (configuráveis via variáveis de ambiente `ADMIN_USERNAME` e `ADMIN_PASSWORD_HASH`).
- Monitoramento em tempo real de latência, secretarias mais acionadas, economia de tokens, volume de consultas e taxa de resolução de primeiro nível.

### 4. Memória Conversacional Persistente (Multiturno 50+ Turnos)
- As interações do munícipe são persistidas no banco `data/db/telemetry.db` sob WAL mode, isoladas por `conversation_id`.
- Suporta retomadas contextuais e comandos de memória ("sobre o que estávamos conversando?", "lembra do meu endereço?") em menos de 15ms sem reprocessar histórico completo pela LLM.

---

## FASE 14 - INTEGRAÇÃO DE WEBHOOK GSE/OGM (SINCRONIZAÇÃO EM TEMPO REAL)

### 1. Arquitetura do Receptor Webhook
- **Endpoint Oficial:** `POST /api/webhook/gse` (suporta rota direta na porta `3000` e sob proxy Nginx `/duqueia/api/webhook/gse`).
- **Autenticação HMAC-SHA256:** Validação estrita via `x-hub-signature-256` (`sha256=<hex>`) ou `x-signature` (`<hex>`) com a chave secreta `DUQUE_IA_WEBHOOK_SECRET` definida no `.env`.
- **Timing-Safe Equal:** Verificação de assinatura em tempo constante via `crypto.timingSafeEqual` para blindagem contra ataques de temporização (timing attacks).
- **Liberação Instantânea (200 OK):** O servidor responde `200 OK` de imediato para liberar a fila SQLite de envio do GSE/OGM, despachando o processamento atômico de forma assíncrona.

### 2. Processador de UPSERT Incremental (`scripts/webhook_processor.py`)
- **Módulo SIGEM (`equipamento.criado`, `equipamento.atualizado`, `equipamento.desativado`):**
  - Faz UPSERT atômico em `main.db` (`secretaria_unidades`) por `sigem_id` ou nome canônico, atualizando endereço, telefones, horário, coordenadas GPS (lat/lon), bairro oficial e distrito.
  - Atualiza o chunk correspondente e FTS5 em `vector.db` (`chunks` e `chunks_fts`).
  - Gera novo embedding denso de 3.072 dimensões via `GeminiClient` e atualiza `duque_ia_chunks` como float32 BLOB.
- **Módulo CDS (`servico.criado`, `servico.atualizado`, `servico.desativado`):**
  - Faz UPSERT atômico em `main.db` (`services`), atualizando prazos (`max_deadline`, `waiting_time`), requisitos, custos e base legal.
  - Atualiza os chunks e vetores correspondentes em `vector.db`.
- **Blindagem e Governança de Dados Curados:**
  - O processador NUNCA sobrescreve ou altera os titulares de secretarias (`secretarias.titular`).
  - O processador NUNCA altera as 85 regras de negócio de IA (`regras_negocio`).
  - Sanitização automática preventiva contra menções de WhatsApp da Ouvidoria em qualquer campo do payload.
  - Auditoria e telemetria: todos os eventos recebidos são registrados na tabela `webhook_events` em `data/db/telemetry.db`.



