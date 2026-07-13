# Variáveis de Ambiente Detalhadas — Duque IA

| Variável | Tipo | Valor Padrão | Descrição |
|---|---|---|---|
| `GEMINI_API_KEY` | string | `None` | Chave de acesso à API do Google Gemini (obrigatória em produção). |
| `USE_TRIAGE_LAYER` | boolean | `true` | Se `true`, ativa o roteador de intenções baseado em LLM antes da busca RAG. |
| `SQLITE_DB_PATH` | string | `agent/duque_ia.db` | Caminho físico para o arquivo de banco de dados do SQLite. |
| `PORT` | integer | `3000` | Porta onde o servidor Node.js será executado. |

---
[Avançar: Dependências](Dependencias.md) | [Voltar: Ambiente](Ambiente.md)
