# 🔄 Ciclo de Vida Completo do DUQUE IA: Da Pergunta à Resposta Final

![Arquitetura Ponta a Ponta do Pipeline RAG do DUQUE IA](C:\Users\501379.PMDC\.gemini\antigravity-ide\brain\b15cdb31-0ed2-4454-aadc-3b290c401135\duqueia_rag_pipeline_1790165235556.jpg)

---

## As 9 Etapas do Fluxo Cognitivo

O **DUQUE IA** opera sob uma arquitetura de múltiplos níveis de triagem, recuperação híbrida e blindagem de segurança para garantir respostas estritamente factuais, protegidas pela LGPD e aderentes aos Procedimentos Operacionais Padrão (POP) da Prefeitura de Duque de Caxias / RJ.

---

### 1. Entrada do Munícipe (Canais Digitais)
* **Origem**: Mensagem de texto enviada pelo munícipe via **Web Chat** (`/chat.html`), **WhatsApp** ou integração de voz.
* **Exemplo de Pergunta**: *"Onde tem posto de saúde para vacinar meu filho no Pilar?"* ou *"Como reclamo de som alto do vizinho?"*

---

### 2. Gateway HTTP & Gestão de Sessões (`server.js`)
* **Sanitização e Segurança**:
  * Aplicação de **Rate Limiting** por IP (máximo de 30 requisições por minuto).
  * Proteção contra **Path Traversal** e validação de payloads.
* **Correlacionamento de Sessão**:
  * Associa a mensagem a um `conversation_id` e atribui um `request_id` único para rastreabilidade atômica.
* **Encaminhamento**: Transmite o JSON para o processo Python em background via stream contínuo **UTF-8 Pipe (`stdin`/`stdout`)**, sem custo de reinicialização de interpretador.

---

### 3. FastGate & Input Guardrails (`agent/guardrails.py` — 0 ms)
Antes de qualquer chamada a bancos ou inteligência artificial, filtros determinísticos avaliam a query:
* 🛡 **Anti-SQL Injection**: Intercepta comandos como `DROP TABLE`, `UNION SELECT` e `DELETE`.
* 🛡 **Anti-Prompt Injection**: Detecta tentativas de desvio de persona (*"esqueça suas instruções"*, *"aja como Dan"*).
* 🛡 **Proteção LGPD / Privacidade**: Bloqueia imediatamente consultas por CPFs, nomes ou protocolos de terceiros (*"quero saber o andamento do processo do meu vizinho"*).
* 🛡 **Competência Municipal**: Filtra perguntas de âmbito Estadual ou Federal (Metrô, Linha Amarela, INSS, Rodovias Federais), emitindo recusa formal de competência da Prefeitura de Duque de Caxias.

> ⚡ **Desvio Imediato**: Se alguma regra de segurança for disparada, o fluxo encerra instantaneamente com a mensagem protocolar de recusa, poupando CPU e chamadas de rede.

---

### 4. Triagem Cognitiva em 3 Níveis & Agente Coletor (`agent/triage.py`)
Caso passe pelo FastGate, a intenção da mensagem é classificada:
1. **Nível 1 (Determinístico / Regex)**: Identifica saudações pontuais, agradecimentos ou emergências vitais (Defesa Civil **199**, SAMU **192**, PM **190**).
2. **Nível 2 (Cache SQLite - `cache.db`)**: Responde em menos de 5 ms se for uma consulta frequente já memorizada.
3. **Nível 3 (Classificador Semântico LLM)**: Classifica o intento (`RAG_GERAL`, `COLETOR_INFO`, `AMBIGUIDADE`, `OUVIDORIA_MANIFESTACAO`).

> 🧩 **Comportamento do Agente Coletor**: Se faltar contexto na pergunta (ex: munícipe diz apenas *"minha rua está esburacada"*), o sistema entra em modo de coleta **estritamente incremental (1 pergunta por vez)** para saber o bairro e o ponto de referência antes de acionar a busca.

---

### 5. Motor de Recuperação Híbrida (`agent/retrieval.py`)
A busca é disparada simultaneamente em três frentes complementares:
1. **Busca Relacional Estruturada ([main.db](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/data/db/main.db))**:
   * Consulta à tabela `services` e `vw_ia_servicos` com índices FTS5 (Full-Text Search) sobre a Carta de Serviços oficial (644 serviços catalogados).
2. **Resolução de Entidades Geográficas ([agent/entity_resolver.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/entity_resolver.py))**:
   * Mapeamento de 443 unidades físicas (CRAS, CREAS, Postos de Saúde, UPAs, Escolas) e 152 bairros para resolver a unidade mais próxima ao endereço informado.
3. **Busca Vetorial Semântica ([vector.db](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/data/db/vector.db))**:
   * Geração do vetor de embedding de 768 dimensões via Google Gemini e cálculo de similaridade por cosseno contra 1.575 chunks de leis, decretos, resoluções e normas.

---

### 6. RRF Fusion & Cross-Encoder Reranker (`agent/reranker.py`)
* **RRF (Reciprocal Rank Fusion)**: Une os rankings da busca FTS5 (palavras-chave exatas) e da busca vetorial (sentido semântico) em um score combinado equilibrado.
* **Cross-Encoder Reranking**: Um modelo avaliador profundo reordena os top 8 candidatos mais promissores com a fórmula ponderada:
  $$\text{Score Final} = 0.60 \times \text{CrossEncoderScore} + 0.40 \times \text{HybridScore}$$
* Candidatos que não atingem a nota de corte mínima de relevância são descartados.

---

### 7. Síntese e Geração Contextualizada (`agent/handlers.py`)
* O orquestrador monta um prompt restrito contendo **apenas** os fatos comprovados nos chunks recuperados e as regras institucionais do POP:
  * Tom profissional e afirmativo (sem saudações redundantes a cada turno).
  * Dados essenciais formatados em **negrito** (endereços, telefones, prazos e documentos).
  * Instrução de registro na plataforma oficial **Colab** (`duquedecaxias.colab.re`).
* A LLM (Google Gemini) gera o texto da resposta.

---

### 8. Output Guardrail & Fallback Oficial (`agent/guardrails.py`)
* **Verificação Anti-Alucinação**: Compara semanticamente a resposta gerada com os dados originais resgatados do banco.
* **Controle de Vazamento**: Garante que nenhum dado pessoal ou telefone não-oficial foi inventado.
* 🚨 **Fallback Oficial da Ouvidoria Geral**: Se a informação for omissa ou inconclusiva, o sistema substitui respostas vagas pelo encaminhamento oficial com contatos reais:
  * **Telefone**: `(21) 2652-3835`
  * **WhatsApp**: `(21) 99824-5903`
  * **E-mail**: `ouvidoria@duquedecaxias.rj.gov.br`

---

### 9. Resposta Estruturada Final & Telemetria (`agent/telemetry.py`)
* **Formatação Final**: A resposta é encapsulada em um payload JSON estruturado:
  ```json
  {
    "answer": "Para matricular seu filho na creche municipal...",
    "sources": ["carta_servicos_educacao.xlsx", "vw_ia_servicos"],
    "confidence": 0.94,
    "intent_detected": "RAG_GERAL",
    "conversation_id": "sess_1784209...",
    "metrics": {
      "retrieval_time_ms": 118.4,
      "llm_time_ms": 612.0,
      "total_time_ms": 745.2
    }
  }
  ```
* **Gravação de Métricas**: Latências individuais de cada nó do grafo, tokens consumidos e custos são persistidos em [telemetry.db](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/data/db/telemetry.db) e `metrics/retrieval_performance.csv`.
* **Exibição ao Cidadão**: O Node.js recebe o JSON e entrega na interface do munícipe instantaneamente.
