# Relatório de Auditoria de Arquivos — DUQUE IA

Este documento apresenta uma análise profunda de cada arquivo pertencente ao workspace do **DUQUE IA**, cobrindo importações, uso, redundâncias, integridade e conformidade de código.

---

## 📂 1. Arquivos da Raiz (Root)

| Arquivo | Quem usa? | Quando é usado? | Importado? | Status / Qualidade / Observações |
| :--- | :--- | :--- | :--- | :--- |
| `setup_and_run.py` | Desenvolvedor / DevOps | No bootstrap do sistema para preparar bancos e dependências. | Não | **Necessário.** Centraliza a inicialização e validação das bases. |
| `server.js` | Node.js Runtime | Servidor web HTTP e WebSockets que gerencia a interface de chat. | Não | **Necessário.** Inicia processos filhos Python. |
| `requirements.txt` | pip / DevOps | Instalação de dependências do Python. | Não | **Necessário.** Contém pacotes como `fastapi`, `google-genai`. |
| `package.json` | npm | Configura dependências do Node.js (`express`, `ws`). | Não | **Necessário.** |
| `package-lock.json`| npm | Lockfile de pacotes Node.js. | Não | **Necessário.** |
| `skills-lock.json` | IDE / Agente | Lockfile de skills do Gemini IDE. | Não | **Necessário.** |
| `Dockerfile` | Docker | Geração da imagem de deploy do RAG. | Não | **Necessário para produção.** |
| `docker-compose.yml`| Docker | Orquestração local do container e PostgreSQL. | Não | **Necessário para produção.** |
| `Makefile` | Desenvolvedor | Atalhos de comando (`make test`, `make run`). | Não | **Necessário.** Contém scripts úteis de automação. |
| `README.md` | Desenvolvedores | Manual de configuração e inicialização. | Não | **Necessário.** |
| `Documentacao_Completa.html`| Desenvolvedores | Arquivo de documentação estático gerado anteriormente. | Não | **Legado / Preservado.** Documentação offline. |
| `.gitignore` | Git | Ignorar arquivos compilados, locais e envs. | Não | **Necessário.** |
| `.env` / `.env.example`| Todo o sistema | Carregar chaves de API e caminhos de banco. | Não | **Necessário.** |

---

## 🤖 2. Pacote `agent/` (Core do Sistema)

| Arquivo | Quem usa? | Quando é usado? | Importado? | Status / Qualidade / Observações |
| :--- | :--- | :--- | :--- | :--- |
| `agent.py` | `server.js` / CLI | Orquestração do agente DuqueIAAgent. | Sim | **Ativo.** Core do runtime cognitivo. |
| `main.py` | `server.js` | Interface CLI por stdin/stdout com o Node.js. | Não | **Ativo.** Entrada principal por sessão. |
| `graph.py` | `agent.py` | Gerencia o grafo cognitivo (LangGraph Lite). | Sim | **Ativo.** Controla as transições de estados. |
| `triage.py` | `graph.py` | Classifica a intenção usando fallbacks e caches. | Sim | **Ativo.** Primeira barreira de triagem. |
| `retrieval.py` | `handlers.py` | Realiza a busca híbrida (vetores, Levenshtein, regex). | Sim | **Ativo.** Algoritmo central de RAG. |
| `handlers.py` | `graph.py` | Executa fluxos de RAG, triagem contextual e coleta. | Sim | **Ativo.** Contém a inteligência dos nós do grafo. |
| `guardrails.py` | `triage.py` | Valida inputs contra invasão e LGPD (Fase 9). | Sim | **Ativo.** Segurança de entrada e saída. |
| `scoring.py` | `retrieval.py` | Funções matemáticas de score de relevância e similaridade. | Sim | **Ativo.** |
| `models.py` | Todo o pacote | Definição de Pydantic Models e Enums. | Sim | **Ativo.** |
| `planner.py` | `handlers.py` | Cria planos de ação quando necessário. | Sim | **Ativo.** |
| `reranker.py` | `retrieval.py` | Reordena chunks com base em heurísticas finas. | Sim | **Ativo.** |
| `memory.py` | `agent.py` | Persistência em memória de contexto curto. | Sim | **Ativo.** |
| `fallback.py` | `handlers.py` | Cria mensagens de retorno da Ouvidoria Geral. | Sim | **Ativo.** |
| `confidence.py` | `handlers.py` | Calcula score final de confiança. | Sim | **Ativo.** |
| `tool_router.py`| `handlers.py` | Encaminha chamadas de ferramentas. | Sim | **Ativo.** |
| `authorities_catalog.py`| `retrieval.py` | Dicionário estático de órgãos e contatos. | Sim | **Ativo.** Código de dados inline pesado (pode ser migrado para o banco futuramente). |

---

## 🗄️ 3. Pacote `storage/` (Persistência)

| Arquivo | Quem usa? | Quando é usado? | Importado? | Status / Qualidade / Observações |
| :--- | :--- | :--- | :--- | :--- |
| `__init__.py` | Todo o sistema | Exporta a instância Singleton `storage_manager`. | Sim | **Ativo (Novo).** |
| `manager.py` | Todo o sistema | Gerencia conexões e manutenção (VACUUM/ANALYZE). | Sim | **Ativo (Novo).** |
| `main_repository.py` | `agent.py` / Testes | Consultas estruturadas sobre secretarias e CRAS. | Sim | **Ativo (Novo).** |
| `vector_repository.py` | `retrieval.py` / Ingestão | Leitura e inserção de chunks e embeddings. | Sim | **Ativo (Novo).** |
| `cache_repository.py` | `triage.py` | Leitura e escrita de classificações em cache. | Sim | **Ativo (Novo).** |
| `telemetry_repository.py` | `db_stats.py` | Estatísticas de observabilidade. | Sim | **Ativo (Novo).** |

---

## ⚙️ 4. Pacotes `config/` e `utils/`

| Arquivo | Quem usa? | Quando é usado? | Importado? | Status / Qualidade / Observações |
| :--- | :--- | :--- | :--- | :--- |
| `config/settings.py` | Todo o sistema | Variáveis de ambiente e blocklists. | Sim | **Ativo (Novo).** |
| `utils/db_client.py` | `storage/` | Execuções cruas SQL no SQLite. | Sim | **Ativo.** Helper genérico de persistência. |
| `utils/gemini_client.py`| `agent/`, `ingestion/` | Comunicação com a API do Gemini. | Sim | **Ativo.** |
| `utils/groq_client.py` | `utils/llm_router.py` | Comunicação com o Groq (Llama). | Sim | **Ativo.** Fallback de triagem. |
| `utils/llm_router.py` | `agent/` | Roteamento dinâmico de LLMs com fallback. | Sim | **Ativo.** |
| `utils/provider_health.py`| `utils/llm_router.py`| Monitora latência de provedores. | Sim | **Ativo.** |
| `utils/mock_provider.py`| Testes unitários | Simulação de chamadas LLM offline. | Sim | **Código de Teste em Produção.** Helper usado apenas pela suíte de testes. |

---

## 📥 5. Pacote `ingestion/` (Pipeline de Ingestão)

| Arquivo | Quem usa? | Quando é usado? | Importado? | Status / Qualidade / Observações |
| :--- | :--- | :--- | :--- | :--- |
| `ingestion/embed/main.py` | Ingestor | Script principal para gerar e salvar embeddings. | Não | **Ativo.** CLI executado via pipeline. |
| `ingestion/embed/core.py` | `embed/main.py` | Estratégias e heurísticas de Chunking. | Sim | **Ativo.** |
| `ingestion/embed/config.py` | `embed/main.py` | Loader do YAML de configuração. | Sim | **Ativo.** |
| `ingestion/embed/embed_config.yml` | `embed/main.py` | Parâmetros de chunking do ingestor. | Não | **Ativo.** |
| `ingestion/parser/populate_structured_services.py` | Ingestor | Popula o banco relacional a partir do Excel. | Não | **Ativo.** |
| `ingestion/parser/parse_assuntos.py` | Ingestor | Extrai assuntos do Excel municipal. | Não | **Ativo.** |
| `ingestion/parser/parse_carta_servico.py` | Ingestor | Extrai a carta de serviços do Excel. | Não | **Ativo.** |
| `ingestion/parser/parse_csv.py` | Ingestor | Parser auxiliar para planilhas CSV. | Não | **Ativo.** |
| `ingestion/parser/parse_excel.py` | Ingestor | Parser de suporte para planilhas XLSX. | Não | **Ativo.** |
| `ingestion/parser/parse_pdfs.py` | Ingestor | Parser robusto de PDFs (PyPDF). | Não | **Ativo.** |
| `ingestion/parser/parse_web.py` | Ingestor | Extrator de conteúdos de páginas web. | Não | **Ativo.** |
| `ingestion/parser/parse_oficios_ocr.py` | Ingestor | Parser de ofícios com suporte a OCR. | Não | **Ativo.** |
| `ingestion/parser/inject_ouvidoria_chunk.py` | Ingestor | Injeta chunks estáticos de Ouvidoria Geral. | Não | **Ativo.** |

---

## 6. Pacote `scripts/` (Testes e Utilitários)

| Arquivo | Quem usa? | Quando é usado? | Importado? | Status / Qualidade / Observações |
| :--- | :--- | :--- | :--- | :--- |
| `scripts/db_stats.py` | Desenvolvedor / Admin | Monitoramento operacional em CLI. | Não | **Ativo (Novo).** |
| `scripts/run_all_tests.py` | Desenvolvedor / CI | Executa a suíte de testes de regressão. | Não | **Ativo.** |
| `scripts/check_db.py` | Desenvolvedor | Inspeciona schemas de forma rápida. | Não | **Utilitário.** |
| `scripts/fix_embedding_metadata.py`| Desenvolvedor | Ajusta dimensões de embeddings. | Não | **Utilitário.** |
| `scripts/update_authorities.py`| Desenvolvedor | Utilitário para atualizar dados de contatos. | Não | **Utilitário.** |
| `scripts/search_main.py` | Desenvolvedor | Busca interna por strings em `agent/main.py`. | Não | **Obsoleto / Pode ser removido.** Utilizado apenas para debug rápido local. |

*Nota: A pasta `scripts/tests/` contém 17 arquivos de testes integrados ativos e válidos.*

---

## 🔍 Respostas às Perguntas do Usuário (Auditoria Sintética)

1.  **Quem usa / Quando é usado / Importado?**
    *   Verificado individualmente na tabela acima. O runtime é disparado pelo Node (`server.js`) que spawna o CLI (`agent/main.py`), orquestrado por `agent/agent.py` e persistido em `storage/`.
2.  **Está morto / Pode ser removido / Substituído / Versão mais nova?**
    *   **Sim, mortos e removidos:** O monólito `duque_ia.db`, a biblioteca `utils/storage.py`, as configurações `agent/config.py` e a pasta `archive/` foram removidos ou substituídos pelas novas implementações estruturadas de produção.
    *   **Pode ser removido:** O script `scripts/search_main.py` é obsoleto e pode ser deletado de forma segura sem afetar o runtime.
3.  **Existe duplicado?**
    *   Tínhamos duplicidade lógica nos logs (raiz `logs/` e `data/logs/`). O da raiz foi deletado. Os logs agora concentram-se em `data/logs/`.
4.  **Existe código comentado / experimental / legado?**
    *   `Documentacao_Completa.html` é um HTML legado que descreve versões antigas do banco. Pode ser mantido apenas para referência histórica de documentação.
    *   `utils/mock_provider.py` é código puramente para testes (mock) estruturado dentro do pacote de utilitários de produção. O ideal seria movê-lo para `scripts/tests/helpers/` em revisões futuras.
