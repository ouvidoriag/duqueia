# 🏛 Arquitetura Técnica Auditável do DUQUE IA

![Arquitetura Técnica Auditável do DUQUE IA](C:\Users\501379.PMDC\.gemini\antigravity-ide\brain\b15cdb31-0ed2-4454-aadc-3b290c401135\duque_ia_arquitetura_auditavel_1790165979406.jpg)

---

## 🎯 Princípio Arquitetural Fundamental

> **"Nenhuma resposta oficial deve ser entregue sem passar por validação prévia de contexto, segurança e aderência estrita às fontes institucionais."**

---

## As 5 Camadas de Responsabilidade

A arquitetura do **DUQUE IA** foi desenhada para atender aos mais altos padrões de conformidade pública, transparência e auditabilidade da **Prefeitura de Duque de Caxias / RJ**:

```mermaid
graph TD
    subgraph C1["<b>Camada 1: Interface do Munícipe</b>"]
        E1["1. Entrada do Munícipe<br/>• Web Chat (/chat.html)<br/>• WhatsApp Municipal"]
    end

    subgraph C2["<b>Camada 2: Acesso, Sessão e Segurança</b>"]
        E2["2. Gateway e Sessão (server.js)<br/>• Rate Limit (30 req/min/IP)<br/>• Gestão de Sessões e Pipe UTF-8"]
        E3["3. FastGate Local (&lt;1ms)<br/>• Filtro Determinístico sem Custo de Rede<br/>• Proteção SQLi, Prompt Injection e LGPD"]
    end

    subgraph C3["<b>Camada 3: Conhecimento e Inteligência</b>"]
        E4["4. Triagem e Agente Coletor (agent/triage.py)<br/>• Classificação de Intenção<br/>• Coleta Incremental (1 Dado por Vez)"]
        E5["5. Busca Híbrida e Reranker (agent/retrieval.py)<br/>• FTS5 Relacional (Carta de Serviços em main.db)<br/>• 443 Unidades Físicas e 152 Bairros (GIS)<br/>• 1.575 Chunks Vetoriais de 768d (vector.db)<br/>• Re-ranqueamento Cross-Encoder (Score 60/40)"]
    end

    subgraph C4["<b>Camada 4: Geração e Blindagem de Saída</b>"]
        E6["6. Redação IA e Regras do POP (agent/handlers.py)<br/>• Síntese Factual com Google Gemini<br/>• Fatos em Negrito e Direcionamento Colab"]
        E7["7. Output Guardrail (agent/guardrails.py)<br/>• Verificação Anti-Alucinação contra Chunks<br/>• Fallback Oficial da Ouvidoria (2652-3835)"]
    end

    subgraph C5["<b>Camada 5: Saída, Entrega e Auditoria</b>"]
        E8["8. Entrega e Auditoria (agent/telemetry.py)<br/>• Resposta JSON Estruturada na Tela<br/>• Persistência em telemetry.db e Métricas de Execução"]
    end

    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> E5
    E5 --> E6
    E6 --> E7
    E7 --> E8
```

---

## 🔍 Respostas aos Pontos Críticos de Auditoria

### 1. Numeração e Sequência Estrita
* **Correção Efetuada:** Eliminada qualquer duplicação ou nó fantasma. A sequência é perfeitamente linear e monotônica de **1 a 8**.

### 2. O conceito de "FastGate Local (< 1 ms)"
* **Esclarecimento Técnico de Engenharia:**  
  Não existe processamento de 0 ms absoluto no mundo físico. A designação **"FastGate Local (< 1 ms)"** refere-se ao fato de ser uma avaliação **estritamente in-memory**, realizada por expressões regulares compiladas em Python, com **zero chamadas de rede externa** (zero chamadas a APIs ou LLMs). Se houver tentativa de ataque SQLi, Prompt Injection ou invasão da LGPD, a requisição é interceptada em menos de 1 milissegundo.

### 3. As Verificações do Output Guardrail
O nó 7 (Output Guardrail) valida formalmente 5 critérios antes de liberar a resposta:
1. **Aderência Factual:** A resposta só afirma o que consta explicitamente nos chunks recuperados?
2. **Sanitização de Contatos:** Algum telefone ou e-mail falso foi inferido?
3. **Encaminhamento Adequado:** Se a solicitação for de zeladoria urbana, o cidadão foi devidamente instruído a usar a plataforma oficial **Colab**?
4. **Fallback Seguro:** Caso a base de dados não tenha a informação solicitada, o sistema emite imediatamente o direcionamento oficial para a **Ouvidoria Geral de Duque de Caxias**:
   * Telefone: **(21) 2652-3835**
   * WhatsApp: **(21) 99824-5903**
   * E-mail: `ouvidoria@duquedecaxias.rj.gov.br`
5. **Score Mínimo:** A confiança ponderada atingiu o limiar de corte mínimo ($Score \ge 0.50$)?

---

### 4. Métricas e Rastreabilidade (Auditoria em telemetry.db)
A cada requisição concluída, os seguintes metadados são gravados de forma indelével:
* `request_id` e `conversation_id`;
* `retrieval_time_ms`, `llm_time_ms`, `total_time_ms`;
* `similarity_score` e `confidence`;
* Lista exata de fontes consultadas (`sources`);
* Timestamp UTC e hash da versão do banco.
