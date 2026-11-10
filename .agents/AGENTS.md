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
- Substituir mensagens genéricas de falha de busca por redirecionamento direto para a Ouvidoria Geral de Duque de Caxias: Telefone **(21) 2652-3835** ou WhatsApp **(21) 99824-5903**.

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
* **`public/chat.html`:** Interface de atendimento humanizada com o atendente virtual do DUQUE IA. Deve utilizar os avatares disponíveis em `public/assets/` (`atendente_caxias_headset_acolhe.png`, `atendente_notebook_pensando.png`, `atendente_caxias_joinha.png`, etc.) alternando dinamicamente de acordo com o estado da conversa (acolhendo, pensando/pesquisando, respondendo).
* **`public/dashboard.html`:** Painel de observabilidade executivo que consome `telemetry.db` através do endpoint `api/metrics`. Deve exibir métricas de latência, volume de atendimentos por secretaria, conformidade de respostas, economia de tokens e mapa de calor de demandas.
