# Análise de Arquitetura — DUQUE IA RAG Framework
> **Atualizado em:** 2026-06-26 | Versão analisada: agent.py 895 linhas · duque_ia.db ~31MB

---

## 1. Diagrama Textual da Arquitetura

```text
DUQUEIA/
│
├── server.js                     # Gateway HTTP Node.js (porta 3000) — gerencia sessões por sessionId
│
├── agent/                        # Camada de Agente Conversacional
│   ├── main.py                   # CLI / modo-pipe — entry point do processo Python
│   ├── agent.py                  # DuqueIAAgent — orquestrador principal (895 linhas)
│   ├── triage.py                 # Triagem 3-camadas: Fast Gate → SQLite Cache → Gemini LLM
│   ├── router.py                 # Intenções de sistema (identidade, saudação, despedida)
│   ├── retrieval.py              # Busca híbrida vetorial + keyword + structured (vw_ia_servicos)
│   ├── guardrails.py             # Input / Privacy / Competency / Legal guardrails
│   ├── scoring.py                # cosine_similarity, keyword_overlap_score
│   ├── fallback.py               # Fallback para Ouvidoria e detecção de queries vagas
│   ├── confidence.py             # Calibração de confiança pós-retrieval
│   ├── reranker.py               # Interface BaseReranker / NoOpReranker (extensível)
│   ├── config.py                 # KEYWORD_POLICY, LIST_INTENT_MAP, EMBEDDING_DIMS
│   ├── models.py                 # QueryIntent enum
│   ├── duque_ia.db               # Banco SQLite (chunks + embeddings + cache de triagem + serviços)
│   └── main_old.py               # ⚠️ CÓDIGO MORTO — versão antiga (103KB), deletar
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
│       ├── main.py               # CLI: lê JSONs → chunking → embedding → SQLite
│       ├── core.py               # ChunkingStrategies (recursive, token, semantic, geo)
│       ├── config.py             # Loader de embed_config.yml
│       └── embed_config.yml      # Configuração da estratégia ativa
│
├── utils/
│   ├── gemini_client.py          # Wrapper Gemini (rotação de chaves, novo SDK e legado)
│   ├── llm_router.py             # Roteador multi-LLM (parcialmente integrado)
│   └── groq_client.py            # Cliente Groq (disponível, não integrado no agente)
│
├── bancoia/                      # Base de conhecimento bruta
│   ├── CARTA_DE_SERVICO_*.xlsx   # Carta de Serviços Municipal
│   ├── OFICIOS/                  # PDFs de ofícios para OCR
│   └── POP/                      # Procedimentos Operacionais Padrão
│
├── logs/
│   └── execution.log             # Log de cada turno de conversa
│
├── metrics/
│   └── retrieval_performance.csv # Métricas: latência, score, tokens, custo
│
├── Makefile                      # Automação do pipeline
├── .env / .env.example           # Configuração de ambiente
└── server.js                     # Servidor HTTP Node.js
```

---

## 2. Fluxo de Execução

### A. Pipeline de Ingestão
```
[Fontes Brutas] → [Parsers] → [JSONs em parsed_pdf_files/]
                                         ↓
[duque_ia.db: duque_ia_chunks] ← [Embedder] ← [Chunking recursive_500_100]
```

### B. Pipeline de Retrieval (por turno)
```
Pergunta do Munícipe
  → Fast Gate (regex, 0ms)
  → Triage Cache SQLite (md5 hash, ~1ms)
  → Gemini Triage LLM (50-200ms) com histórico dos 2 turnos anteriores
  → Intenção Detectada:
      OUVIDORIA_MANIFESTACAO → Agente Coletor (1 dado por vez → Colab)
      AMBIGUO_LUZ/LAMPADA   → Desambiguação contextual
      LGPD/JURIDICO/FORA    → Bloqueio direto
      RAG_GERAL             → Guardrails → Retrieval → LLM → Resposta
  → SystemIntentHandler (saudação, despedida, identidade, ajuda)
  → Input Guardrails (SQL/Prompt/Privacy/Competency/Legal)
  → QueryAnalyzer (intent: LIST / GIS / GENERAL)
  → retrieve_context():
      ├── retrieve_full_category() para LIST queries
      ├── retrieve_structured_service() para queries de serviço
      └── Busca vetorial: 0.70×cosine + 0.30×keyword_overlap
  → Retrieval Guardrail (threshold 0.50)
  → Gemini LLM generate_interaction()
  → calibrate_confidence()
  → log_execution_metrics() → logs/ + metrics/
  → JSON: {answer, sources, confidence, retrieved_chunks, metrics}
```

---

## 3. Dependências entre Módulos

```
gemini_client.py ─┬─► agent.py (geração de resposta + triage)
                  ├─► triage.py (call_triage_llm)
                  └─► ingestion/embed/main.py (geração de embeddings)

agent.py ─────────┬─► triage.py (perform_triage)
                  ├─► retrieval.py (retrieve_context)
                  ├─► router.py (QueryAnalyzer, SystemIntentHandler)
                  ├─► guardrails.py (4 funções de checagem)
                  ├─► fallback.py (build_fallback_guidance, is_query_too_vague)
                  ├─► confidence.py (calibrate_confidence)
                  ├─► scoring.py (extract_query_keywords)
                  └─► models.py (QueryIntent)
```

---

## 4. Melhorias Recomendadas (Priorizadas)

### 🔴 Crítico — Ação Imediata
1. **Deletar `agent/main_old.py`** — 103KB de código morto, risco de confusão
2. **Consolidar `duque_ia.db` duplicado** — existe em `/DUQUEIA/` (raiz) e em `/DUQUEIA/agent/`
3. **Remover `sql_query` da resposta JSON pública** — expõe lógica interna ao frontend

### 🟡 Médio — Sprint 2
4. **Persistir histórico de sessão no SQLite** — `_history` e `_interaction_map` são perdidos no restart
5. **Expandir `COMPETENCY_TRIGGERS`** — INSS, rodovias BR, Detran estadual não são cobertos
6. **Adicionar `USE_TRIAGE_LAYER=true` ao `.env.example`**

### 🟢 Melhoria — Sprint 3
7. **Criar `docker-compose.yml`** para deploy de produção
8. **Implementar reranker real** (Cross-Encoder via sentence-transformers)
9. **Benchmark automatizado** das estratégias de chunking

---

## 5. Diagnóstico de Maturidade

| Fase | Status |
|---|---|
| Fase 1 — Mapeamento e Arquitetura | ✅ Completo |
| Fase 2 — Chunking (recursive_500_100) | ✅ Funcional |
| Fase 3 — Retrieval Evaluation (métricas CSV) | ✅ Funcional |
| Fase 4 — Guardrails (4 tipos + triage + retrieval + output) | ✅ Completo |
| Fase 5 — Sistema de Métricas | ✅ Completo |
| Fase 6 — GIS / Bairros | 🟡 Parcial |
| Fase 7 — Benchmark entre estratégias | 🔴 Pendente |
| Fase 8 — Produção (Docker) | 🟡 Parcial |
| Fase 9 — POP / Ouvidoria / Agente Coletor | ✅ Completo |
