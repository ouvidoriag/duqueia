# Relatório de Auditoria — Variáveis de Ambiente e Configurações

Este documento apresenta a análise de variáveis de ambiente e arquivos de configuração do DUQUE IA, cobrindo o `.env`, `.env.example` e a classe centralizadora de configurações `config/settings.py`.

---

## 1. Mapeamento de Variáveis e Uso Real

| Variável | Origem | Destino (Leitura) | Status de Uso |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEYS` | `.env` | `utils/gemini_client.py` | **Ativo e Crítico.** Utilizado para chamadas à API LLM com suporte a rotação dinâmica de chaves. |
| `GROQ_API_KEY` | `.env` | `utils/groq_client.py` | **Ativo.** Utilizado para chamadas de fallback de triagem semântica rápida. |
| `GEMINI_MODEL` | `.env` | `config/settings.py` | **Ativo.** Define o modelo padrão de geração de respostas do RAG (`gemini-2.5-flash`). |
| `GEMINI_FAST_MODEL` | `.env` | `agent/triage.py` / `guardrails.py` | **Ativo (Indireto).** Lido via `os.getenv()` diretamente nos módulos para triagem rápida e guardrails. |
| `GEMINI_FALLBACK_MODEL` | `.env` | `utils/llm_router.py` | **Ativo (Indireto).** Lido sob demanda como modelo reserva caso o principal falhe. |
| `GEMINI_EMBEDDING_MODEL` | `.env` | `config/settings.py` | **Ativo.** Define o modelo de embedding utilizado para geração de vetores de chunks (`gemini-embedding-2`). |
| `ENVIRONMENT` | `.env` | `config/settings.py` | **Ativo.** Controla o nível de verbose e logs locais. |
| `LOG_LEVEL` | `.env` | `config/settings.py` | **Ativo.** Controla o nível do logger do Python. |
| `USE_TRIAGE_LAYER` | `.env` | `config/settings.py` | **Ativo.** Habilita ou desabilita a camada prévia de triagem semântica. |
| `SUPABASE_URL` | `.env` | Opcional | **Inativo Localmente.** Placeholder para infraestrutura futura PGVector (Supabase). |
| `SUPABASE_SERVICE_ROLE_KEY`| `.env` | Opcional | **Inativo Localmente.** Placeholder para infraestrutura futura PGVector (Supabase). |
| `VECTOR_DB_URL` | `.env` | Sem referências | **Sem Uso / Obsoleta.** Herança de protótipos antigos baseados em Qdrant/Milvus. |
| `IA_RATE_LIMIT` | `.env` | Sem referências | **Sem Uso / Obsoleta.** |
| `IA_REQUEST_TIMEOUT_MS` | `.env` | Sem referências | **Sem Uso / Obsoleta.** |
| `IA_ENABLED` | `.env` | Sem referências | **Sem Uso / Obsoleta.** |
| `IA_MAINTENANCE_MODE` | `.env` | Sem referências | **Sem Uso / Obsoleta.** |

---

## 2. Diagnóstico de Problemas Detectados

### A. Variáveis Sem Uso (Código Morto de Configurações)
As variáveis `VECTOR_DB_URL`, `IA_RATE_LIMIT`, `IA_REQUEST_TIMEOUT_MS`, `IA_ENABLED` e `IA_MAINTENANCE_MODE` estão declaradas no arquivo `.env` mas **não são lidas em nenhuma parte do código ativo**. Elas geram ruído visual e podem induzir desenvolvedores a acreditarem que há controle de rate limit ou timeout configurado através do `.env`.

### B. Segredos e Exposição de Chaves
* **`.env` (Local):** Contém chaves de API reais do Gemini (`AQ.Ab8RN...`) e do Groq (`gsk_GUbzG...`). Como o `.env` está devidamente listado no arquivo `.gitignore`, o risco de vazamento público via commits de repositório Git é mitigado.
* **`.env.example` (Template):** Está em conformidade, contendo apenas placeholders fictícios, sem expor chaves válidas.

### C. Assimetria de Leitura (Leituras Diretas vs. Centralizadas)
Modelos auxiliares como `GEMINI_FAST_MODEL` e `GEMINI_FALLBACK_MODEL` são lidos diretamente com `os.getenv` em locais como `triage.py` e `llm_router.py`. O ideal para manter a padronização arquitetural de produção é que **toda leitura de variáveis de ambiente seja centralizada em `config/settings.py`**, e as demais classes importem os valores do módulo de configuração.

---

## 3. Recomendações e Plano de Ação

1. **Limpeza do `.env`:** Remover as variáveis inativas (`VECTOR_DB_URL`, `IA_RATE_LIMIT`, `IA_REQUEST_TIMEOUT_MS`, `IA_ENABLED`, `IA_MAINTENANCE_MODE`) para limpar o arquivo de configurações de produção.
2. **Centralização no `settings.py`:** Mapear e expor `GEMINI_FAST_MODEL` e `GEMINI_FALLBACK_MODEL` dentro do [settings.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/config/settings.py).
3. **Injeção de Variáveis em Produção (Docker / Render):** Garantir que no ambiente cloud (ex: Render/Docker Compose) os segredos sejam fornecidos via variáveis de ambiente da plataforma e não gravados fisicamente em arquivos `.env` dentro da imagem Docker.
