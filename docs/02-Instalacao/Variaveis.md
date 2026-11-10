# Variáveis de Ambiente Detalhadas — Duque IA

| Variável | Tipo | Valor Padrão | Descrição |
|---|---|---|---|
| `GEMINI_API_KEY` / `GEMINI_API_KEYS` | string | `None` | Chave(s) de acesso à API do Google Gemini com suporte a rotação automática. |
| `USE_TRIAGE_LAYER` | boolean | `true` | Se `true`, ativa a triagem de intenções antes do pipeline RAG. |
| `DATABASE_MAIN` | string | `data/db/main.db` | Caminho para o banco relacional de serviços municipais e ontologia. |
| `DATABASE_VECTOR` | string | `data/db/vector.db` | Caminho para o banco vetorial de chunks e FTS5. |
| `DATABASE_CACHE` | string | `data/db/cache.db` | Caminho para o banco de cache semântico de triagem. |
| `DATABASE_TELEMETRY` | string | `data/db/telemetry.db` | Caminho para o banco de telemetria e auditoria de consultas. |
| `PORT` | integer | `3001` | Porta onde o servidor Node.js será executado. |

---
[Avançar: Dependências](Dependencias.md) | [Voltar: Ambiente](Ambiente.md)
