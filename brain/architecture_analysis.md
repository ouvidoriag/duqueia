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
│   ├── storage/                  # Camada de Persistência Segregada (main, vector, cache, telemetry)
│   ├── utils/                    # Utilitários compartilhados (gemini_client, groq_client)
│   ├── public/                   # Frontend estático do chat (chat.html, style.css)
│   ├── logs/ & metrics/          # Históricos de execução e métricas de RAG
│   └── Makefile                  # Automação do pipeline
```

---

## 2. Fluxo de Execução e Comunicação Node-Python

### A. Fluxo de Comunicação de Processo (stdin/stdout)
1. O servidor Node.js (`server.js`) escuta requisições POST na rota `/api/chat`.
2. Para cada sessão, um processo filho Python (`agent/main.py`) é instanciado em modo de processo persistente (`spawn`).
3. O Node.js escreve a pergunta do munícipe em bytes UTF-8 no stream `stdin` do processo Python.
4. O processo Python processa a pergunta e imprime a resposta estruturada em JSON no `stdout`.
5. O Node.js bufferiza e extrai o JSON, devolvendo-o para o cliente HTTP.

### B. Fluxo de Triagem e Recuperação RAG Híbrida
1. **Triagem de Intenção**: Fast Gate (regex rápidas) → Cache SQLite de Turnos → Gemini LLM Classifier (com base no histórico do diálogo).
2. **Roteamento de Handlers**: Se for bloqueado por segurança (LGPD/Jurisdição), cai no `SecurityHandler`. Se faltar dados, cai no `CollectorHandler` (Agente Coletor).
3. **Recuperação Híbrida Dinâmica (RAG)**: O RAG busca candidatos nas tabelas estruturadas (`services` e `secretarias`) e no banco vetorial (`duque_ia_chunks`). 
4. **Classificação Unificada**: Todos os candidatos são ordenados juntos sob uma pontuação de similaridade híbrida ajustada (85% cosseno vetorial + 15% overlap de palavras-chave) com boosts de categoria e clínico/saúde.
5. **Guardrail de Saída**: O `check_output_guardrail` compara a resposta da LLM diretamente contra as fontes oficiais recuperadas, eliminando alucinações e evitando falsos positivos.

---

## 3. Robustez Multiplataforma (Windows e Linux)

*   **Resolução de Caminhos**: Todos os caminhos de arquivos em Python e Node.js utilizam `os.path.join`, garantindo a compatibilidade de caminhos entre Windows e Linux.
*   **sys.path**: O arquivo `agent/main.py` define programaticamente a raiz do projeto como primeira posição do `sys.path`.
*   **Tratamento de Encoding**: O processo Python configura explicitamente `sys.stdin`, `sys.stdout` e `sys.stderr` para `utf-8`.

---

## 4. Melhorias Recomendadas e Roadmap

1. **Query Rewriting & Sinônimos:** Traduzir termos coloquiais de Duque de Caxias para termos formais.
2. **Cross-Encoder Reranking:** Integrar um modelo reranker leve para melhorar NDCG@3 e MRR.
3. **Grafo de Conhecimento (Knowledge Graph):** Mapear as relações de secretarias, unidades e serviços locais.
