# Análise de Arquitetura — DUQUE IA RAG Framework
> **Atualizado em:** 2026-07-02 | Versão estável pós-auditoria: agent.py · duque_ia.db ~31MB

---

## 1. Diagrama Textual da Arquitetura

```text
DUQUEIA/
│
├── server.js                     # Gateway HTTP Node.js (porta 3000) — gerencia sessões por sessionId
├── requirements.txt              # Declaração de dependências Python para o Render
├── package.json                  # Scripts npm e build command de dependências
│
├── agent/                        # Camada do Agente Conversacional (Cognitivo)
│   ├── main.py                   # CLI / modo-pipe — entry point do processo Python (UTF-8 stdin/stdout/stderr)
│   ├── agent.py                  # DuqueIAAgent — orquestrador principal (passa contexto para output guardrail)
│   ├── triage.py                 # Triagem de 3 camadas (Fast Gate → SQLite Cache → Gemini LLM)
│   ├── router.py                 # Roteamento semântico (GIS, INSTITUTIONAL, GENERAL)
│   ├── retrieval.py              # Dynamic Hybrid RAG (mistura vetor + estruturado classificados por similaridade)
│   ├── guardrails.py             # Input / Privacy (LGPD) / Competency / Legal / Output guardrails
│   ├── scoring.py                # similaridade de cosseno (cosseno 85% + keyword overlap 15%)
│   ├── fallback.py               # Redirecionamento da Ouvidoria Geral (162 / WhatsApp (21) 99824-5903)
│   ├── confidence.py             # Calibração de confiança pós-retrieval
│   ├── reranker.py               # Interface BaseReranker / NoOpReranker (extensível)
│   ├── config.py                 # KEYWORD_POLICY, LIST_INTENT_MAP, EMBEDDING_DIMS
│   ├── models.py                 # Enums de intenções
│   └── duque_ia.db               # Banco SQLite unificado ( chunks 3072 dim + estruturado + cache de triagem )
│
├── ingestion/                    # Pipeline de Ingestão de Dados
│   ├── parser/
│   │   ├── parse_pdfs.py         # PDFs via pypdf + Markdown de bancoia/
│   │   ├── parse_csv.py          # CSVs com Pandas
│   │   ├── parse_excel.py        # .xlsx/.xls com Pandas + openpyxl
│   │   ├── parse_web.py          # Web scraping (requests + HTMLParser)
│   │   ├── parse_carta_servico.py# Carta de Serviços → tabelas normalizadas no SQLite
│   │   ├── parse_oficios_ocr.py  # OCR de ofícios via Gemini Vision
│   │   ├── parse_assuntos.py     # Mapeamento assunto×secretaria (Colab)
│   │   └── populate_structured_services.py # Popula vw_ia_servicos
│   └── embed/
│       ├── main.py               # lê JSONs → chunking → embedding 3072 dim (resolução absoluta de .env) → SQLite
│       ├── core.py               # ChunkingStrategies (recursive, token, semantic, geo)
│       ├── config.py             # Loader de embed_config.yml
│       └── embed_config.yml      # Configuração da estratégia ativa
│
├── utils/                        # Utilitários compartilhados
│   ├── gemini_client.py          # Wrapper Gemini (rotação de chaves baseada em cota/erro)
│   ├── llm_router.py             # Roteador multi-LLM (parcialmente integrado)
│   └── groq_client.py            # Cliente Groq
│
├── eusoulindo/                   # Repositório de dados, DDL do schema e migrações (Source of Truth)
│   ├── database/                 # DDL, schemas, migrações SQL e scripts de rebuild
│   ├── datasets/                 # Datasets brutos de planilhas, CSVs e Markdowns sincronizados
│   ├── documentation/            # Documentação interativa em HTML e diagramas
│   └── sync.py                   # Sincroniza dados com o restante do projeto
│
├── public/                       # Frontend estático do chat
│   └── chat.html / style.css     # Interface visual do munícipe
│
├── logs/ & metrics/              # Históricos de execução e métricas de RAG
└── Makefile                      # Automação do pipeline
```

---

## 2. Fluxo de Execução e Comunicação Node-Python

### A. Fluxo de Comunicação de Processo (stdin/stdout)
1. O servidor Node.js (`server.js`) escuta requisições POST na rota `/api/chat`.
2. Para cada sessão, um processo filho Python (`agent/main.py`) é instanciado em modo persistente (`spawn`).
3. O Node.js escreve a pergunta do munícipe em bytes UTF-8 no stream `stdin` do processo Python.
4. O processo Python (reconfigurado para UTF-8 em `sys.stdin`, `sys.stdout` e `sys.stderr` para evitar corrupção de acentos no Windows/Linux) processa a pergunta e imprime a resposta estruturada em JSON no `stdout`.
5. O Node.js bufferiza e extrai o JSON, devolvendo-o para o cliente HTTP.

### B. Fluxo de Triagem e Recuperação RAG Híbrida
1. **Triagem de Intenção**: Fast Gate (regex rápidas) → Cache SQLite de Turnos → Gemini LLM Classifier (com base no histórico do diálogo).
2. **Roteamento de Handlers**: Se for bloqueado por segurança (LGPD/Jurisdição), cai no `SecurityHandler`. Se faltar dados, cai no `CollectorHandler` (Agente Coletor).
3. **Recuperação Híbrida Dinâmica (RAG)**: O RAG busca candidatos nas tabelas estruturadas (`services` e `secretarias`) e no banco vetorial (`duque_ia_chunks`). 
4. **Resolução de Bugs**: O bug de listagem total do CRAS foi removido. Agora, unidades físicas só são recuperadas quando os termos da busca realmente casam com seu nome ou endereço.
5. **Classificação Unificada**: Todos os candidatos são ordenados juntos sob uma pontuação de similaridade híbrida ajustada (85% cosseno vetorial + 15% overlap de palavras-chave) com boosts de categoria e clínico/saúde.
6. **Guardrail de Saída**: O `check_output_guardrail` compara a resposta da LLM diretamente contra as fontes oficiais recuperadas, eliminando alucinações e evitando falsos positivos.

---

## 3. Robustez Multiplataforma (Windows e Linux)

*   **Resolução de Caminhos**: Todos os caminhos de arquivos em Python e Node.js utilizam `os.path` e `path.join`, garantindo conversão de separadores de diretório no Windows (`\`) e Linux (`/`).
*   **sys.path**: O arquivo `agent/main.py` define programaticamente a raiz do projeto como primeira posição do `sys.path`, assegurando que `from agent.xxx` e `from utils.xxx` funcionem de forma idêntica tanto localmente quanto no ambiente Render.
*   **Tratamento de Encoding**: O processo Python configura explicitamente `sys.stdin`, `sys.stdout` e `sys.stderr` para `utf-8` com substituição de erros, blindando a troca de mensagens contra qualquer colisão de tabela de páginas de códigos local (como CP1252 no Windows).

---

## 4. Auditoria de Redundâncias e Código Morto (Fase 1)

*   **`agent/main_old.py`**: Confirmado como deletado e limpo.
*   **`duque_ia.db`**: Consolidado unicamente na pasta `/agent/duque_ia.db` com embeddings reais de 3072 dimensões.
*   **`eusoulindo/`**: Identificado como repositório de migrações SQL, datasets e documentação. Deve ser preservado como a fonte de documentação técnica e seeds do banco de dados relacional.
*   **`scripts/`**: Pasta útil que contém testes diretos de comunicação e chaves. Recomenda-se manter para diagnóstico e validação local antes de commits de produção.
