# Relatório de Arquitetura — Fluxo da Aplicação (DUQUE IA)

Este documento detalha o fluxo de dados de ponta a ponta no sistema **DUQUE IA**, mostrando exatamente por onde cada informação passa desde o envio da pergunta pelo munícipe no navegador até o retorno da resposta estruturada.

---

## 1. Diagrama Geral do Fluxo de Informação

```text
Munícipe (Navegador)
  │
  ▼ [HTTP POST /api/chat] (sessionId, message)
Frontend (HTML/JS)
  │
  ▼ [WS/HTTP Stream]
API Gateway (Node.js - server.js)
  │
  ▼ [Spawn / Pipes: stdin (UTF-8)]
Orquestrador (Python - agent/main.py -> agent/agent.py)
  │
  ▼ [LangGraph Lite Graph]
Grafo Cognitivo (agent/graph.py)
  │
  ├─► Triagem de Intenção (agent/triage.py) ──► Cache SQLite (cache.db)
  │
  ├─► Guardrails de Segurança (agent/guardrails.py)
  │
  ▼ [RAG Handler]
Recuperação Híbrida (agent/retrieval.py)
  │
  ├─► Busca Estruturada (storage/main_repository.py ──► main.db)
  │
  ├─► Busca Semântica/Cosseno (storage/vector_repository.py ──► vector.db)
  │
  ▼ [Fusão de Scores & Re-ranking]
Contexto Consolidado (agent/reranker.py)
  │
  ▼ [LLM Router Client]
Roteamento LLM (utils/llm_router.py) ──► Gemini (Principal) / Groq (Fallback)
  │
  ▼ [Output Guardrail Check]
Validação de Alucinação (agent/guardrails.py)
  │
  ▼ [Stdout Pipe (JSON UTF-8)]
Retorno da API Node.js (server.js)
  │
  ▼ [HTTP Response JSON]
Munícipe (Visualização no Frontend)
```

---

## 2. Detalhamento de cada Etapa do Fluxo

### 1. Frontend (Interface de Chat)
* **O que acontece:** O munícipe digita uma pergunta no chat (ex: *"Qual o horário de funcionamento do CRAS Jardim Primavera?"*).
* **Dados trafegados:** Um payload contendo:
  ```json
  {
    "message": "Qual o horário de funcionamento do CRAS Jardim Primavera?",
    "sessionId": "sess_123456789"
  }
  ```

### 2. API Gateway (Node.js - `server.js`)
* **O que acontece:** O servidor Express recebe a requisição. Ele gerencia as sessões ativas do usuário.
* **Comunicação Node-Python:** Se for uma sessão nova, ele spawna um processo filho Python executando `agent/main.py`. Ele então escreve a string JSON com a pergunta diretamente no fluxo `stdin` do processo Python correspondente a essa sessão em UTF-8.

### 3. Orquestrador e Grafo Cognitivo (Python - `agent/main.py` ➔ `agent/graph.py`)
* **O que acontece:** O entry-point Python recebe a mensagem via `sys.stdin` e a direciona para o `DuqueIAAgent`. O agente roda o ciclo cognitivo através do motor de grafos:
  1. **Triagem de Intenção (`agent/triage.py`):**
     * **Fast Gate:** Verifica por padrões óbvios e bloqueios via regex locais (como CPFs, dados sensíveis).
     * **Cache de Triagem:** Busca no banco SQLite local (`cache.db`) se essa exata intenção já foi classificada para poupar chamadas de rede.
     * **LLM Classifier (Gemini Lite):** Classifica a intenção real caso passe pelas etapas anteriores, baseando-se no histórico recente da conversa (Turnos).
  2. **Guardrails de Segurança (`agent/guardrails.py`):**
     * Valida contra SQL Injection, Prompt Injection e violações da LGPD (tentativa de buscar dados de terceiros). Caso detectado, aborta a execução retornando uma mensagem estruturada de bloqueio.

### 4. Recuperação Híbrida / RAG (`agent/retrieval.py` ➔ `storage/`)
* **O que acontece:** Caso a intenção exija busca no RAG (como `RAG_GERAL` ou `GIS`), o orquestrador invoca o motor de retrieval.
* **Acesso ao Banco (`storage/`):**
     * **Busca Estruturada:** Consulta informações de telefones, endereços e serviços no banco relacional `main.db` através do `MainRepository`.
     * **Busca Semântica:** Executa busca aproximada por similaridade de cosseno de embeddings na tabela de chunks vetoriais do banco `vector.db` através do `VectorRepository`.
* **Fusão de Scores:** Os resultados são consolidados. É aplicada uma pontuação híbrida: **85% similaridade vetorial + 15% overlap de palavras-chave** com pesos categorizados (ex: CRAS, IPTU ganham boosts extras).

### 5. Roteamento de LLM e Geração (`utils/llm_router.py`)
* **O que acontece:** O contexto recuperado mais a pergunta e o histórico de mensagens são enviados para a LLM gerar a resposta final formatada.
* **Fallback Inteligente:** O `LLMRouter` gerencia a requisição:
  1. Envia para o **Gemini** (`gemini-2.5-flash`) que é o modelo primário.
  2. Caso o Gemini retorne erro de rede ou estouro de cota (429/503), o roteador automaticamente faz o fallback para o **Groq** (`llama-3.3-70b-versatile` ou `llama-3.1-8b-instant`), gerando a resposta de forma transparente e registrando a telemetria do provedor em `telemetry.db`.

### 6. Guardrail de Saída e Resposta
* **O que acontece:** A resposta gerada pela LLM passa pelo `check_output_guardrail` para verificar se há alucinações (compara fatos da resposta contra as fontes originais) ou dados de terceiros vazados.
* **Escrita do Output:** O agente escreve o JSON formatado no `stdout` do processo Python:
  ```json
  {
    "answer": "O **CRAS Jardim Primavera** funciona de **segunda a sexta-feira, das 9h às 17h**, no endereço **Alameda Esmeralda, 206 - Jardim Primavera**.",
    "sources": ["carta_servicos"],
    "confidence": 0.95
  }
  ```
* **Renderização:** O Node.js captura este JSON no stream `stdout`, fecha a requisição HTTP enviando-o ao navegador, e o frontend renderiza a resposta amigável para o munícipe.
