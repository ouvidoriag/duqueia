# Relatório de Inventário Completo e Classificação do Projeto — DUQUE IA

> **Auditoria do Projeto — Etapa 1**  
> **Data:** 2026-07-28 | **Sistema:** DUQUE IA (Prefeitura de Duque de Caxias — RJ)

---

## 🏛️ Visão Geral da Classificação de Artefatos

O ecossistema do **DUQUE IA** foi mapeado e categorizado em 5 classificações técnicas principais:
- **`PRODUÇÃO`**: Código, bancos e assets ativos no runtime de atendimento.
- **`DESENVOLVIMENTO`**: Scripts de suporte a carga, geração de relatórios e manutenções operacionais.
- **`TESTE`**: Baterias de testes integrados e validações de regressão semântica.
- **`OBSOLETO`**: Scripts de parsing ou tabelas descontinuadas que podem ser arquivados ou limpos.
- **`EXPERIMENTAL`**: Protótipos pontuais localizados em `/scratch`.

---

## 📂 Inventário por Módulo

### 1. Núcleo do Agente (`/agent`)
| Arquivo | Tamanho | Categoria | Descrição / Função |
| :--- | :--- | :--- | :--- |
| [agent/agent.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/agent.py) | ~28.1 KB | **PRODUÇÃO** | Orquestrador principal da classe `DuqueIAAgent`. |
| [agent/authorities_catalog.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/authorities_catalog.py) | ~121.8 KB | **PRODUÇÃO** | Catálogo estruturado de autoridades municipais de Duque de Caxias. |
| [agent/candidate.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/candidate.py) | ~1.5 KB | **PRODUÇÃO** | Estruturas de dados `CandidateChunk`. |
| [agent/composer.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/composer.py) | ~3.1 KB | **PRODUÇÃO** | Formatador e compositor de respostas finais. |
| [agent/confidence.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/confidence.py) | ~1.2 KB | **PRODUÇÃO** | Calibrador do nível de confiança do retrieval. |
| [agent/context_builder.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/context_builder.py) | ~0.9 KB | **PRODUÇÃO** | Montador do bloco de contexto para o prompt da LLM. |
| [agent/duque_ia.db](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/duque_ia.db) | DB | **PRODUÇÃO** | Banco de dados SQLite relacional principal (Carta de Serviços e Secretarias). |
| [agent/entity_resolver.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/entity_resolver.py) | ~11.3 KB | **PRODUÇÃO** | Resolução semântica de entidades geográficas e serviços. |
| [agent/fallback.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/fallback.py) | ~8.4 KB | **PRODUÇÃO** | Lógicas de fallback para Ouvidoria Geral e aplicativo Colab. |
| [agent/graph.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/graph.py) | ~14.6 KB | **PRODUÇÃO** | Engine do Grafo de Estados Cognitivos (`AgentState`). |
| [agent/guardrails.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/guardrails.py) | ~6.3 KB | **PRODUÇÃO** | Guardrails de entrada/saída, LGPD e competência municipal. |
| [agent/handlers.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/handlers.py) | ~72.3 KB | **PRODUÇÃO** | Handlers de intenção e Prompt Builders do RAG. |
| [agent/main.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/main.py) | ~4.5 KB | **PRODUÇÃO** | CLI Entrypoint para comunicação via pipe UTF-8. |
| [agent/memory.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/memory.py) | ~2.6 KB | **PRODUÇÃO** | Gestão de memória e histórico da sessão. |
| [agent/models.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/models.py) | ~0.8 KB | **PRODUÇÃO** | Modelos de dados e enum de intenções `QueryIntent`. |
| [agent/planner.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/planner.py) | ~10.4 KB | **PRODUÇÃO** | Planner Semântico LORS (Multi-query Expansion). |
| [agent/ranking.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/ranking.py) | ~4.7 KB | **PRODUÇÃO** | Cálculo e ordenação de candidatos. |
| [agent/reranker.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/reranker.py) | ~6.7 KB | **PRODUÇÃO** | Re-ranker Gemini Cross-Encoder. |
| [agent/retrieval.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/retrieval.py) | ~39.1 KB | **PRODUÇÃO** | Motor de Retrieval Híbrido Multiconta. |
| [agent/router.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/router.py) | ~14.7 KB | **PRODUÇÃO** | Roteamento de intenções e fluxos. |
| [agent/rules_config.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/rules_config.py) | ~3.2 KB | **PRODUÇÃO** | Regras estáticas e regras institucionais. |
| [agent/scoring.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/scoring.py) | ~4.0 KB | **PRODUÇÃO** | Algoritmos de pontuação e similaridade vetorial. |
| [agent/telemetry.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/telemetry.py) | ~2.8 KB | **PRODUÇÃO** | Gravador de telemetria por requisição. |
| [agent/tool_router.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/tool_router.py) | ~1.7 KB | **PRODUÇÃO** | Seleção de fontes de dados. |
| [agent/triage.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/triage.py) | ~20.8 KB | **PRODUÇÃO** | Triagem semântica em 3 níveis. |

---

### 2. Camada de Persistência (`/storage` e `/database`)
| Arquivo | Tamanho | Categoria | Descrição / Função |
| :--- | :--- | :--- | :--- |
| [storage/manager.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/storage/manager.py) | ~3.6 KB | **PRODUÇÃO** | Gerenciador central `StorageManager`. |
| [storage/main_repository.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/storage/main_repository.py) | ~1.0 KB | **PRODUÇÃO** | Repositório do banco principal. |
| [storage/vector_repository.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/storage/vector_repository.py) | ~1.5 KB | **PRODUÇÃO** | Repositório do banco vetorial. |
| [storage/cache_repository.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/storage/cache_repository.py) | ~1.5 KB | **PRODUÇÃO** | Repositório de cache de triagem. |
| [storage/telemetry_repository.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/storage/telemetry_repository.py) | ~0.6 KB | **PRODUÇÃO** | Repositório de métricas de telemetria. |
| [database/schema_main.sql](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/database/schema_main.sql) | ~6.3 KB | **PRODUÇÃO** | DDL do banco relacional. |
| [database/schema_vector.sql](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/database/schema_vector.sql) | ~1.6 KB | **PRODUÇÃO** | DDL do banco vetorial. |
| [database/schema_cache.sql](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/database/schema_cache.sql) | ~0.5 KB | **PRODUÇÃO** | DDL do banco de cache. |
| [database/schema_telemetry.sql](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/database/schema_telemetry.sql) | ~1.7 KB | **PRODUÇÃO** | DDL do banco de telemetria. |
| [database/vector.db](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/database/vector.db) | DB | **PRODUÇÃO** | Banco vetorial de embeddings. |

---

### 3. Ingestão e Processamento (`/ingestion`)
| Arquivo | Tamanho | Categoria | Descrição / Função |
| :--- | :--- | :--- | :--- |
| [ingestion/embed/main.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/embed/main.py) | ~6.8 KB | **PRODUÇÃO** | CLI gerador de embeddings. |
| [ingestion/embed/core.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/embed/core.py) | ~4.2 KB | **PRODUÇÃO** | Motor de geração de vetores Gemini. |
| [ingestion/parser/populate_structured_services.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/populate_structured_services.py) | ~10.7 KB | **PRODUÇÃO** | Popula Carta de Serviços no SQLite. |
| [ingestion/parser/parse_pdfs.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/parse_pdfs.py) | ~5.9 KB | **PRODUÇÃO** | Extrator de textos de PDFs. |
| [ingestion/parser/parse_carta_servico.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/parse_carta_servico.py) | ~8.1 KB | **PRODUÇÃO** | Parser da Carta de Serviços. |
| [ingestion/parser/parse_oficios_ocr.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/parse_oficios_ocr.py) | ~11.3 KB | **PRODUÇÃO** | OCR para documentos digitalizados. |
| [ingestion/parser/parse_web.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/parse_web.py) | ~3.5 KB | **PRODUÇÃO** | Parser de dados web municipais. |
| [ingestion/parser/parse_assuntos.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/parse_assuntos.py) | ~3.2 KB | **PRODUÇÃO** | Mapeador de assuntos. |
| [ingestion/parser/inject_ouvidoria_chunk.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/inject_ouvidoria_chunk.py) | ~4.3 KB | **PRODUÇÃO** | Injetor de dados da Ouvidoria. |
| [ingestion/parser/parse_csv.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/parse_csv.py) | ~2.4 KB | **OBSOLETO** | Parser CSV descontinuado. |
| [ingestion/parser/parse_excel.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/ingestion/parser/parse_excel.py) | ~2.5 KB | **OBSOLETO** | Parser Excel legado. |

---

### 4. Utilitários (`/utils`)
| Arquivo | Tamanho | Categoria | Descrição / Função |
| :--- | :--- | :--- | :--- |
| [utils/gemini_client.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/gemini_client.py) | ~46.4 KB | **PRODUÇÃO** | Client nativo da Gemini API. |
| [utils/llm_router.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/llm_router.py) | ~7.8 KB | **PRODUÇÃO** | Multi-provider LLM Router. |
| [utils/db_client.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/db_client.py) | ~1.4 KB | **PRODUÇÃO** | Helper de conexão SQLite. |
| [utils/groq_client.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/groq_client.py) | ~4.3 KB | **PRODUÇÃO** | Client Groq de fallback. |
| [utils/provider_health.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/provider_health.py) | ~3.8 KB | **PRODUÇÃO** | Monitoramento de disponibilidade de APIs. |
| [utils/web_search.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/web_search.py) | ~9.2 KB | **PRODUÇÃO** | Client de busca online. |
| [utils/mock_provider.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/mock_provider.py) | ~13.3 KB | **TESTE** | Provedor de Mock em testes unitários. |

---

### 5. Scripts e Testes (`/scripts` e `/scratch`)
- `scripts/run_all_tests.py`: **TESTE** (Runner principal da suíte).
- `scripts/evaluate_rag.py`: **TESTE / MÉTRICAS** (Avaliação de retrieval).
- `scripts/benchmark_regression.py`: **TESTE** (Benchmark de regressão).
- `scripts/test_30_perguntas.py`: **TESTE** (Teste de 30 perguntas).
- `scratch/*`: **EXPERIMENTAL** (30 scripts de testes pontuais e geradores de relatórios temporários de desenvolvimento).

---

## 📊 Resumo Quantitativo da Classificação

- **Módulos em Produção:** 45 arquivos principais.
- **Scripts de Teste & Métricas:** 24 suítes e helpers ativos.
- **Arquivos Obsoletos Mapeados:** 2 parsers descontinuados (`parse_csv.py`, `parse_excel.py`).
- **Arquivos Temporários Mapeados:** 30 scripts em `/scratch` (preservados em `/archive`).
