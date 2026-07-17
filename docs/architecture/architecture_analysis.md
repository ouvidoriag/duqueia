# Análise de Arquitetura — DUQUE IA RAG Framework
> **Atualizado em:** 2026-07-02 | Versão estável pós-auditoria: agent.py · duque_ia.db ~31MB

---

## 1. Diagrama Textual da Arquitetura

`DUQUEIA/
│
├── server.js                     # Gateway HTTP Node.js (porta 3000) — gerencia sessões por sessionId
├── requirements.txt              # Declaração de dependências Python para o Render
├── package.json                  # Scripts npm e build command de dependências
│
├── data/                         # DIRETÓRIO UNIFICADO DE DADOS
│   ├── raw/                      # Dados brutos (CSVs, Excel, PDFs e URLs de input)
│   │   ├── raw_csv_files/
│   │   ├── raw_excel_files/
│   │   ├── raw_pdf_files/
│   │   └── raw_web_urls/
│   ├── knowledge/                # Base de conhecimento Markdown (anterior bancoia)
│   │   ├── CRIADO/
│   │   ├── IAzeladoria/
│   │   ├── OFICIOS/
│   │   └── POP/
│   └── processed/                # Dados estruturados convertidos em JSON
│
├── agent/                        # Camada do Agente Conversacional (Cognitivo)
│   ├── main.py                   # CLI / modo-pipe — entry point do processo Python (UTF-8 stdin/stdout/stderr)
│   ├── agent.py                  # DuqueIAAgent — orquestrador principal
│   ├── triage.py                 # Triagem de 3 camadas (Fast Gate → SQLite Cache → Gemini LLM)
│   ├── router.py                 # Roteamento semântico (GIS, INSTITUTIONAL, GENERAL)
│   ├── retrieval.py              # Dynamic Hybrid RAG (mistura vetor + estruturado classificados por similaridade)
│   ├── guardrails.py             # Input / Privacy (LGPD) / Competency / Legal / Output guardrails
│   ├── scoring.py                # similaridade de cosseno (cosseno 85% + keyword overlap 15%)
│   ├── fallback.py               # Redirecionamento da Ouvidoria Geral (Telefone/E-mail)
│   ├── confidence.py             # Calibração de confiança pós-retrieval
│   ├── reranker.py               # Interface BaseReranker / NoOpReranker (extensível)
│   ├── config.py                 # KEYWORD_POLICY, LIST_INTENT_MAP, EMBEDDING_DIMS
│   ├── models.py                 # Enums de intenções
│   └── duque_ia.db               # Banco SQLite unificado ( chunks 3072 dim + estruturado + cache de triagem )
│
├── ingestion/                    # Pipeline de Ingestão de Dados
│   ├── parser/                   # Scripts de parsing de dados sob data/raw/ e data/knowledge/
│   └── embed/                    # Lê JSONs sob data/processed/ -> gera chunks -> embeddings -> SQLite
├── utils/                        # Utilitários compartilhados (gemini_client, groq_client)
├── public/                       # Frontend estático do chat (chat.html, style.css)
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

*   **`agent/main_old.py`**: Deletado e limpo.
*   **`duque_ia.db`**: Consolidado unicamente em `/agent/duque_ia.db` com embeddings reais de 3072 dimensões.
*   **`scripts/`**: Mantido para fins de validação local e diagnóstico rápido de APIs.

---

## 5. RAG Roadmap — Fases de Evolução do DUQUE IA (Meta: 90%+)

Com base nas otimizações prioritárias já homologadas (Metadata Filtering + Stopwords Municipais elevando a taxa de acerto de **63.16%** para **78.95%**), as próximas fases arquiteturais mapeadas para atingir o nível industrial de excelência são:

### 🚀 Fase 1 — Query Rewriting & Sinônimos (Meta: 82-85%)
1. **Query Rewriting (Reescrita de Consultas via LLM):** 
   * Traduzir perguntas coloquiais ou abreviadas em termos formais de governança pública antes do retrieval (ex: *"IPTU segunda via"* vira *"segunda via IPTU, imposto predial, Secretaria da Fazenda"*).
2. **Dicionário Municipal de Sinônimos:**
   * Mapeamento de termos equivalentes específicos de Duque de Caxias (ex: Posto de Saúde -> UBS/USF/Clínica da Família, Prefeito -> Chefe do Executivo, etc.) integrado ao processamento de palavras-chave BM25.
3. **Expansão de Metadados na Ingestão:**
   * Enriquecer chunks com marcações finas: `bairro`, `distrito`, `secretaria_vinculada`, `lideranca`, `prazo_limite` e `canal_digital`.

### 🚀 Fase 2 — Reranker & Fusão de Scores (Meta: 85-90%)
1. **Cross-Encoder Reranking:**
   * Integrar o `GeminiCrossEncoder` (ou um modelo local leve como o `MiniLM-L6`) para reordenar os top 15/20 candidatos retornados pelo primeiro estágio híbrido, elevando de forma consistente as métricas de NDCG@3 e MRR.
2. **RRF (Reciprocal Rank Fusion):**
   * Implementar a técnica de fusão RRF para combinar de forma ideal as listas ranqueadas vindas do banco vetorial e do motor de busca híbrida por palavra-chave, aumentando a robustez em queries ambíguas.

### 🚀 Fase 3 — Produção Avançada (Meta: >90%)
1. **Grafo de Conhecimento (Knowledge Graph):**
   * Mapear explicitamente as entidades da prefeitura (Secretaria ⇄ Liderança ⇄ Equipamento Físico ⇄ Serviços ⇄ Regulamentos). O retrieval navegará as conexões estruturais de forma determinística, ao invés de depender apenas de similaridade de cosseno.
2. **Query Cache Inteligente:**
   * Cache de baixa latência (0ms) para consultas repetitivas de alta frequência (IPTU, CRAS, vacinas, horários de atendimento).
3. **Aprendizado Contínuo com Loop de Feedback:**
   * Registro histórico de consultas com feedback dos munícipe (join de perguntas, respostas entregues e likes/cliques do usuário).

