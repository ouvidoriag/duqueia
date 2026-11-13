# Plano de Correção e Melhoria — Prompts e Respostas (DUQUE IA)

Este documento registra todas as falhas identificadas na auditoria de prompts e respostas dos agentes do **DUQUE IA**, as soluções técnicas aplicadas e o checklist de validação passo a passo.

---

## Checklist de Execução e Validação

### 1. Risco de Truncamento por `max_output_tokens` Baixo
- **Problema:** Limites muito baixos de saída cortavam respostas no meio da frase ou quebravam o JSON de triagem:
  - `agent/triage.py` (linha 598): `max_output_tokens=150`
  - `agent/handlers.py` (`CollectorHandler`, linha 286): `max_output_tokens=250`
  - `agent/handlers.py` (`ClarificationHandler`, linha 1782): `max_output_tokens=300`
  - `agent/handlers.py` (`AIMetaHandler`, linha 1845): `max_output_tokens=350`
- **Solução:** `max_output_tokens` elevado para `350` em `triage.py` e `800` nos handlers (`CollectorHandler`, `ClarificationHandler`, `AIMetaHandler`), eliminando cortes abruptos sem impactar a latência normal (parada natural no `EOS`).
- **Status:**
  - [x] `agent/triage.py`: `max_output_tokens` ajustado para `350`
  - [x] `agent/handlers.py` (`CollectorHandler`): `max_output_tokens` ajustado para `800`
  - [x] `agent/handlers.py` (`ClarificationHandler`): `max_output_tokens` ajustado para `800`
  - [x] `agent/handlers.py` (`AIMetaHandler`): `max_output_tokens` ajustado para `800`

### 2. Modularização do `system_instruction` Monolítico do `RagHandler`
- **Problema:** O `RagHandler` enviava 15.722 caracteres (~3.930 tokens) com 29 regras fixas em **toda** requisição, independentemente do assunto, aumentando latência, custo de tokens e risco de diluição de atenção (*lost in the middle*).
- **Solução:** Extraído o helper `_build_rag_system_instruction(effective_query: str, context_str: str, history: list) -> str` em `agent/handlers.py`, mantendo **100% das 29 regras preservadas**:
  - **Core Rules (sempre ativas):** `3.307` caracteres (~826 tokens) cobrindo identidade, anti-fluff, formatação, demandas múltiplas, contagem exata, anti-placeholder, foco estrito, anti-vazamento de metadados/OCR e proibição de WhatsApp da Ouvidoria Geral.
  - **Domain Rules (injeção dinâmica por palavras-chave em `effective_query + context_str`):**
    - `IPTU segunda via`: `3.719` chars (~929 tokens) — **redução de 76,3%**
    - `quebrei o pe` (trauma/emergência): `3.852` chars (~963 tokens) — **redução de 75,5%**
    - `gamba no quintal` (animais silvestres): `4.344` chars (~1.086 tokens) — **redução de 72,4%**
    - `poda de arvore em fio` (alta tensão/SMMA): `4.899` chars (~1.224 tokens) — **redução de 68,8%**
    - `falta de medicamento idoso` (USF/ACS/SISREG): `4.977` chars (~1.244 tokens) — **redução de 68,3%**
    - `som alto barulho` (190/SMMA/SUOP): `5.034` chars (~1.258 tokens) — **redução de 68,0%**
- **Status:**
  - [x] Helper `_build_rag_system_instruction` implementado em `agent/handlers.py`
  - [x] 100% das 29 regras originais preservadas e testadas quanto à cobertura por domínio
  - [x] Redução de tamanho médio do `system_instruction` medida e registrada (~68% a 76% de economia por requisição)

### 3. Resolução de Instruções Contraditórias de Tamanho e Tom (`RagHandler`)
- **Problema:** A Regra 2 pedia respostas curtas ("1 a 3 frases"), enquanto o rodapé do prompt (linha 1105) exigia "resposta completa, detalhada, empática e prestativa", gerando verbosidade em perguntas pontuais.
- **Solução:**
  - Rodapé do prompt do `RagHandler` atualizado para: *"Gere uma resposta clara, objetiva e adaptada ao tipo de pergunta, sem preâmbulos desnecessários:"*.
  - Regra **1. Anti-Fluff (Direto ao Ponto)** adicionada às Core Rules, proibindo saudações genéricas e rodeios na abertura das respostas.
- **Status:**
  - [x] Rodapé do prompt do `RagHandler` atualizado
  - [x] Regra Anti-Fluff aplicada nas Core Rules

### 4. Coleta Estritamente Incremental no `CollectorHandler` (1 Pergunta por Vez)
- **Problema:** O fallback `"geral"` e a regra 3 em `gerar_esclarecimento_contextual` (`agent/agent.py`, linhas 562 e 578) podiam acumular duas perguntas no mesmo turno (pedindo tipo + assunto simultaneamente).
- **Solução:** Ajustado o fallback `"geral"` e a diretriz para exigir **estritamente 1 pergunta por vez** (primeiro o tipo da manifestação, sem acumular perguntas no mesmo turno).
- **Status:**
  - [x] Prompts e fallback do `gerar_esclarecimento_contextual` (`agent/agent.py`) revisados e padronizados para 1 pergunta por turno

### 5. Validação Técnica, Testes e Registro Final
- **Validação executada:**
  - [x] Checagem de sintaxe Python (`py_compile`) em `agent/triage.py`, `agent/handlers.py` e `agent/agent.py` — **0 erros**
  - [x] Teste automatizado de cobertura e redução de tokens de `_build_rag_system_instruction` — **aprovado (redução de 68% a 76,3%)**
  - [x] `python tests/test_authorities.py` — **aprovado (exit code 0)**
  - [x] `python tests/test_vice_prefeita.py` — **aprovado (4/4 APROVADO, exit code 0)**
  - [x] `python tests/test_webhook_gse.py` — **aprovado (5/5 testes, 100% sucesso, exit code 0)**
  - [x] Commit limpo no Git
