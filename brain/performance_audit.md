# Relatório de Auditoria de Performance e Latência — DUQUE IA

> **Auditoria do Projeto — Etapa 9**  
> **Data:** 2026-07-28 | **Sistema:** DUQUE IA (Prefeitura de Duque de Caxias — RJ)

---

## ⚡ 1. Desempenho e Concorrência

* **Modo WAL no SQLite:** Todas as conexões nos 4 bancos de dados (`duque_ia.db`, `vector.db`, `cache.db`, `telemetry.db`) ativam o modo WAL (`PRAGMA journal_mode = WAL;`) durante a inicialização no `StorageManager`, permitindo leituras paralelas sem travas de arquivo.
* **Cache em 3 Níveis:**
  1. *Fast Gate (0ms)*: Interceptação por expressões regulares em memória.
  2. *Cache de Triagem (<1ms)*: Consulta rápida por Hash MD5 no `cache.db`.
  3. *Gemini LLM*: Chamada apenas quando a consulta for inédita.

---

## ⏱️ 2. Mapeamento de Latência por Etapa (Médias do System Benchmark)

| Etapa | Latência Média | Descrição |
| :--- | :--- | :--- |
| **Fast Gate / Cache** | `< 1 ms` | Resposta instantânea de consultas repetidas ou saudações. |
| **Triagem Semântica (LLM)** | `~ 800 ms` | Classificação de intenção e reescrita de query. |
| **Retrieval Híbrido (SQL + Vector)**| `~ 2.3 s` | Busca aproximada relacional + similaridade de cosseno. |
| **Re-ranker (Cross-Encoder)** | `~ 0.25 s` | Re-classificação dos top 8 candidatos. |
| **Context Builder** | `~ 0.02 s` | Formatação do bloco de contexto. |
| **Geração LLM (Flash-Lite)** | `~ 4.3 s` | Geração da resposta final. |
| **Total Pipeline** | `~ 6.6 s` | Latência total média em primeira execução sem cache. |

---

## 📈 3. Otimizações Recomendadas para Produção

1. **Cache L1 em Memória RAM:** Adicionar `functools.lru_cache` no Python para armazenar os 500 hashes mais recentes em memória RAM antes de consultar o `cache.db`.
2. **Streaming de Resposta:** Ativar respostas via SSE (Server-Sent Events) no gateway Node.js (`server.js`) para exibir o texto da resposta ao munícipe conforme os primeiros tokens são gerados pela LLM.
