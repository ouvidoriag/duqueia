# Análise Detalhada da Arquitetura e Mapeamento do Pipeline RAG — DUQUE IA

> **Auditoria de Arquitetura — FASE 1 / ETAPA 1**  
> **Data:** 2026-07-23 | **Sistema:** DUQUE IA (Sistema de Informações Municipais — Duque de Caxias / RJ)

---

## 1. Mapeamento Geral da Arquitetura

O sistema **DUQUE IA** é um framework RAG (Retrieval-Augmented Generation) multicamadas de atendimento público municipal. Ele combina triagem de intenções em 3 níveis, reescrita de queries conversacionais, planejamento semântico multi-query (LORS), busca híbrida (banco estruturado + banco vetorial + unidades físicas), reranking com Cross-Encoder e guardrails estritos de entrada e saída.

```text
                               ┌─────────────────────────┐
                               │  Cliente Web / Frontend │
                               └────────────┬────────────┘
                                            │ HTTP POST /api/chat
                                            ▼
                               ┌─────────────────────────┐
                               │   server.js (Node.js)   │  Gateway HTTP & Gestão de Sessões
                               └────────────┬────────────┘
                                            │ UTF-8 Pipe (stdin/stdout)
                                            ▼
                               ┌─────────────────────────┐
                               │   agent/main.py (CLI)   │  Entry Point Python
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │   agent/agent.py        │  Orquestrador DuqueIAAgent
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │   agent/graph.py        │  LangGraph Lite (Grafo de Estados)
                               └────────────┬────────────┘
                                            │
         ┌──────────────────────────────────┼──────────────────────────────────┐
         │                                  │                                  │
         ▼                                  ▼                                  ▼
┌─────────────────┐                ┌─────────────────┐                ┌─────────────────┐
│ Input Guardrails│                │     Triagem     │                │   Query Rewriter│
│(guardrails.py)  │                │   (triage.py)   │                │  (handlers.py)  │
│• Prompt Inject  │                │• Fast Gate (0ms)│                │• Histórico      │
│• LGPD / Privacy │                │• Cache SQLite   │                │• Resolução de   │
│• Competência    │                │• Gemini LLM     │                │  referências    │
└────────┬────────┘                └────────┬────────┘                └────────┬────────┘
         │                                  │                                  │
         └──────────────────────────────────┼──────────────────────────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │   agent/planner.py      │  Planner Semântico (LORS)
                               │  Multi-query Expansion  │  (Sugere até 3 sub-queries)
                               └────────────┬────────────┘
                                            │ Sub-queries + Filtros
                                            ▼
                               ┌─────────────────────────┐
                               │   agent/retrieval.py    │  Retriever Híbrido Multiconta
                               └────────────┬────────────┘
                                            │
         ┌──────────────────────────────────┼──────────────────────────────────┐
         ▼                                  ▼                                  ▼
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────┐
│  Secretarias /   │               │   vw_ia_servicos │               │   duque_ia_chunks│
│  Carta Serviços  │               │   e Unidades CRAS│               │   (Banco Vetorial│
│  (SQLite Main)   │               │   (SQLite Main)  │               │   sqlite-vec/emb)│
└────────┬─────────┘               └────────┬─────────┘               └────────┬─────────┘
         │                                  │                                  │
         └──────────────────────────────────┼──────────────────────────────────┘
                                            │ Chunks & Registros Candidatos
                                            ▼
                               ┌─────────────────────────┐
                               │   agent/reranker.py     │  Re-ranker Cross-Encoder
                               │ (GeminiCrossEncoder)    │  (60% Cross + 40% Hybrid)
                               └────────────┬────────────┘
                                            │ Top Chunks Ordenados
                                            ▼
                               ┌─────────────────────────┐
                               │   agent/handlers.py     │  Prompt Builder & LLM Response
                               │  (RagHandler + Prompt)  │  (gemini-3.1-flash-lite)
                               └────────────┬────────────┘
                                            │ Resposta Candidata
                                            ▼
                               ┌─────────────────────────┐
                               │   Output Guardrail      │  Auditoria Anti-alucinação
                               │   (guardrails.py)       │  & Proteção LGPD de Saída
                               └────────────┬────────────┘
                                            │ Resposta Final JSON
                                            ▼
                               ┌─────────────────────────┐
                               │  Logs / Telemetria      │  metrics/ & logs/
                               └─────────────────────────┘
```

---

## 2. Componentes e Responsabilidades por Arquivo

| Componente | Arquivo(s) Responsável(eis) | Função Principal | Serviços / APIs Utilizados |
| :--- | :--- | :--- | :--- |
| **Gateway & I/O** | `server.js`, `agent/main.py` | Gerencia conexões HTTP, sessões por `sessionId` e faz interface via pipe UTF-8 stdin/stdout com Python. | Node.js child_process spawn |
| **Orquestrador de Grafo** | `agent/graph.py`, `agent/agent.py` | Executa o estado (`AgentState`) entre nós atômicos de decisão com capacidade de desvio e retentativa em caso de erro. | LangGraph Lite (Python puro) |
| **Input Guardrails** | `agent/guardrails.py`, `agent/fallback.py` | Filtra injeções de SQL, Prompt Injection, violações de privacidade LGPD, incompetência municipal e solicitações jurídicas antes da LLM. | Regras Regex locais |
| **Triagem & Classificador** | `agent/triage.py` | Classifica a intenção em 16 categorias em 3 níveis (Fast Gate 0ms → Cache SQLite → Gemini LLM 3.1 Flash-Lite). | SQLite Cache, Gemini API |
| **Query Rewriter** | `agent/handlers.py` (`rewrite_query_with_history`) | Reestrutura perguntas de continuação ("e o telefone?", "onde fica?") incorporando o histórico para tornar a query autossuficiente. | Gemini API / Regras Heurísticas |
| **Roteador de Ferramentas** | `agent/tool_router.py` | Seleciona dinamicamente quais fontes de dados acionar com base na intenção (`structured_db`, `geo_units`, `faq_chunks`). | Regras estáticas |
| **Planner Semântico** | `agent/planner.py` | Decompõe a query original em até 3 sub-queries complementares (LORS: Lógica de Recuperação Semântica). | Gemini API / Rule Engine offline |
| **Retriever Híbrido** | `agent/retrieval.py`, `agent/scoring.py` | Executa busca vetorial (cosseno 85% + overlap 15%) + busca SQL estruturada em `secretarias` e `vw_ia_servicos` com fuzzy Levenshtein. | Gemini Embeddings (768d), SQLite |
| **Re-ranker** | `agent/reranker.py` | Avalia o par (Query, Chunk) usando Gemini Cross-Encoder para refinar o ranking dos 8 melhores candidatos. | Gemini API (3.1 Flash-Lite) |
| **Prompt Builder & Synthesis**| `agent/handlers.py` (`RagHandler`) | Monta o prompt final organizando a hierarquia estrita de fontes (Estruturado > Complementar) e gera a resposta humanizada. | Gemini API (3.1 Flash-Lite) |
| **Calibrador & Output Guardrail** | `agent/confidence.py`, `agent/guardrails.py` | Calibra o score de confiança e audita a resposta final comparando-a diretamente com as fontes recuperadas para travar alucinações. | Gemini API (3.1 Flash-Lite) |
| **Persistência & Métricas** | `storage/storage_manager.py`, `metrics/collector.py` | Mantém os bancos SQLite segregados (`duque_ia.db`, `vector.db`, `cache.db`, `telemetry.db`) e grava logs de execução em CSV/log. | SQLite, File System |

---

## 3. Pipeline RAG Passo a Passo (Cadeia de Execução)

1. **Recepção da Pergunta:** O munícipe envia a mensagem pelo frontend HTTP. O `server.js` redireciona via `stdin` para o processo `agent/main.py`.
2. **Entrada no Grafo de Estados:** O `run_graph` inicia o nó `fast_gate` (0ms). Se a query casar com regras de segurança ou ambiguidade óbvia, desvia imediatamente.
3. **Triagem de Intenção (3 Níveis):**
   - *Nível 0:* Fast Gate Regex.
   - *Nível 1:* Consulta ao `triage_cache` no SQLite por hash MD5.
   - *Nível 2:* Chamada ao Gemini `gemini-3.1-flash-lite` com histórico conversacional. Retorna JSON com `intent`, `needs_clarification` e `rewritten_query`.
4. **Reescrita Conversacional da Consulta:** Se a triagem não forneceu a reescrita e há histórico, o `rewrite_query_with_history` expande pronomes e elipses.
5. **Planejamento Semântico (LORS Planner):** O `SemanticRecoveryPlanner` gera até 3 sub-queries de busca direcionadas (ex: buscando serviço + secretaria + unidade física CRAS simultaneamente).
6. **Recuperação Multiconta (Retrieval Híbrido):**
   - **Estruturada:** Consulta tabelas `secretarias`, `vw_ia_servicos` e `secretaria_unidades` no `duque_ia.db` usando busca aproximada de Levenshtein e aliasing.
   - **Vetorial:** Gera vetor de embedding 768d da sub-query via Gemini Embeddings e calcula similaridade de cosseno contra a tabela `duque_ia_chunks` no `vector.db`.
   - **Boosts & Filtros:** Aplica boosts de contexto (governança, liderança, impostos, saúde, localidade de bairros como Xerém ou Imbariê).
7. **Reranking de Segundo Estágio:** O `GeminiCrossEncoder` avalia os top 8 candidatos para verificar se o trecho efetivamente responde à pergunta. Combina os scores (60% Cross + 40% Híbrido).
8. **Validação do Guardrail de Retrieval:** Se o melhor candidato tiver pontuação inferior ao limiar mínimo (`similarity_threshold` = 0.50 em prod / 0.25 em dev), o sistema dispara o fallback de baixa confiança.
9. **Construção do Prompt & Síntese:** O `RagHandler` formata os blocos de contexto priorizando fontes oficiais estruturadas e instrui a LLM a gerar resposta direta, sem saudações redundantes.
10. **Guardrail de Saída & Auditoria:** O `check_output_guardrail` faz uma verificação final contra o contexto original para garantir ausência de contradições, alucinações ou vazamento de CPFs/protocolos de terceiros.
11. **Entrega da Resposta & Métricas:** A resposta final formatada em JSON é emitida no `stdout` para o `server.js` e enviada ao usuário, registrando a telemetria em `metrics/retrieval_performance.csv` e `logs/execution.log`.

---

## 4. Dependências entre Módulos e Tecnologias Utilizadas

```text
[server.js] ──(spawn)──► [agent/main.py]
                             │
                             ▼
                    [agent/agent.py]
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
[agent/graph.py]                          [utils/gemini_client.py]
        │                                         │ (Google Gemini API / 3.1 Flash-Lite)
        ├──► [agent/triage.py] ───────────────────┤
        ├──► [agent/guardrails.py] ───────────────┤
        ├──► [agent/planner.py] ──────────────────┤
        ├──► [agent/retrieval.py] ────────────────┼──► [agent/scoring.py]
        ├──► [agent/reranker.py] ─────────────────┤
        └──► [agent/handlers.py] ─────────────────┘
                     │
                     ▼
        [storage/storage_manager.py]
                     │
    ┌────────────────┼────────────────┬────────────────┐
    ▼                ▼                ▼                ▼
duque_ia.db      vector.db        cache.db       telemetry.db
(Estruturado)    (Vetorial)       (Triagem)      (Métricas)
```

---

## 5. Pontos Críticos Mapeados para Diagnóstico de Perda de Informação

Com o mapeamento da arquitetura completo, os seguintes pontos foram identificados como potenciais causas raiz de falhas no RAG:

1. **Classificação Errônea de Intenção na Triagem:** Se a triagem classificar incorretamente uma dúvida sobre serviço como `OUVIDORIA_MANIFESTACAO` ou `CONVERSA`, o fluxo é desviado para o `CollectorHandler` ou `ConversationHandler`, pulando totalmente a busca no banco vetorial.
2. **Reescrita Excessiva ou Distorcida (Query Rewriter):** A reescrita de query pode alterar termos-chave da pergunta original ao tentar incorporar o histórico, prejudicando o batimento na busca estruturada/vetorial.
3. **Sub-queries Inadequadas no LORS Planner:** Se o motor de regras offline do Planner não cobrir determinados sinônimos ou termos populares da cidade, as sub-queries geradas podem trazer contexto irrelevante.
4. **Desconexão entre Tabela Estruturada e Banco Vetorial:** Dados existentes em `services`/`secretarias` podem estar ausentes ou desatualizados em `duque_ia_chunks`, ou vice-versa, gerando lacunas de contexto.
5. **Corte Rígido do Guardrail de Retrieval:** Um limiar de similaridade muito estrito (ex: 0.50) pode descartar chunks corretos que receberam score ligeiramente menor devido a divergência de termos.
6. **Sensibilidade Excessiva do Output Guardrail:** O guardrail de saída pode barrar respostas legítimas por classificar falsamente ausência de termos como contradição.
