# Dicionário de Dados do Banco duque_ia.db

Abaixo está listada toda a estrutura física de tabelas e campos do banco de dados SQLite (`agent/duque_ia.db`).

---
## Tabela: `sqlite_sequence`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| name |  | Não | Não | NULL |
| seq |  | Não | Não | NULL |

---

## Tabela: `embedding_metadata`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| provider | TEXT | Não | Não | NULL |
| model | TEXT | Não | Não | NULL |
| dimension | INTEGER | Não | Não | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

---

## Tabela: `duque_ia_chunks`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| source | TEXT | Não | Sim | NULL |
| category | TEXT | Não | Não | NULL |
| content | TEXT | Não | Sim | NULL |
| embedding | TEXT | Não | Não | NULL |
| metadata | TEXT | Não | Não | NULL |
| keywords | TEXT | Não | Não | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Índices

| Nome do Índice | Único |
|---|---|
| idx_chunks_category | Não |
| idx_chunks_source | Não |

---

## Tabela: `triage_cache`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| query_hash | TEXT | Não | Sim | NULL |
| intent | TEXT | Não | Sim | NULL |
| confidence | REAL | Não | Sim | NULL |
| needs_clarification | INTEGER | Não | Sim | NULL |
| reason | TEXT | Não | Não | NULL |
| model_version | TEXT | Não | Sim | NULL |
| prompt_version | TEXT | Não | Sim | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Índices

| Nome do Índice | Único |
|---|---|
| idx_triage_cache_hash | Não |
| sqlite_autoindex_triage_cache_1 | Sim |

---

## Tabela: `core_documents`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | TEXT | Sim | Não | NULL |
| filename | TEXT | Não | Sim | NULL |
| secretaria | TEXT | Não | Não | NULL |
| category | TEXT | Não | Não | NULL |
| sha256_hash | TEXT | Não | Não | NULL |
| total_chunks | INTEGER | Não | Não | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |
| created_by_user_id | INTEGER | Não | Não | NULL |

### Índices

| Nome do Índice | Único |
|---|---|
| sqlite_autoindex_core_documents_2 | Sim |
| sqlite_autoindex_core_documents_1 | Sim |

---

## Tabela: `chunks_metadata`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | TEXT | Sim | Não | NULL |
| document_id | TEXT | Não | Não | NULL |
| chunk_index | INTEGER | Não | Não | NULL |
| token_count | INTEGER | Não | Não | NULL |
| content | TEXT | Não | Sim | NULL |
| relevance_weight | INTEGER | Não | Não | 1 |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| document_id | core_documents | id |

### Índices

| Nome do Índice | Único |
|---|---|
| sqlite_autoindex_chunks_metadata_1 | Sim |

---

## Tabela: `secretarias`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| name | TEXT | Não | Sim | NULL |
| code | TEXT | Não | Sim | NULL |
| address | TEXT | Não | Não | NULL |
| phone | TEXT | Não | Não | NULL |
| email | TEXT | Não | Não | NULL |
| working_hours | TEXT | Não | Não | NULL |

### Índices

| Nome do Índice | Único |
|---|---|
| sqlite_autoindex_secretarias_1 | Sim |

---

## Tabela: `users`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| secretaria_id | INTEGER | Não | Sim | NULL |
| username | TEXT | Não | Sim | NULL |
| password_hash | TEXT | Não | Sim | NULL |
| role | TEXT | Não | Não | 'editor' |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| secretaria_id | secretarias | id |

### Índices

| Nome do Índice | Único |
|---|---|
| sqlite_autoindex_users_1 | Sim |

---

## Tabela: `categories`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| secretaria_id | INTEGER | Não | Não | NULL |
| name | TEXT | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| secretaria_id | secretarias | id |

---

## Tabela: `services`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| secretaria_id | INTEGER | Não | Sim | NULL |
| category_id | INTEGER | Não | Não | NULL |
| name | TEXT | Não | Sim | NULL |
| description | TEXT | Não | Não | NULL |
| how_to_access | TEXT | Não | Não | NULL |
| address | TEXT | Não | Não | NULL |
| who_can_request | TEXT | Não | Não | NULL |
| waiting_time | TEXT | Não | Não | NULL |
| max_deadline | TEXT | Não | Não | NULL |
| cost | TEXT | Não | Não | NULL |
| regulation_norm | TEXT | Não | Não | NULL |
| status | TEXT | Não | Sim | 'published' |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| category_id | categories | id |
| secretaria_id | secretarias | id |

---

## Tabela: `service_phones`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| service_id | INTEGER | Não | Sim | NULL |
| phone | TEXT | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| service_id | services | id |

---

## Tabela: `service_emails`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| service_id | INTEGER | Não | Sim | NULL |
| email | TEXT | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| service_id | services | id |

---

## Tabela: `service_links`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| service_id | INTEGER | Não | Sim | NULL |
| link | TEXT | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| service_id | services | id |

---

## Tabela: `service_steps`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| service_id | INTEGER | Não | Sim | NULL |
| step_number | INTEGER | Não | Sim | NULL |
| description | TEXT | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| service_id | services | id |

---

## Tabela: `service_documents`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| service_id | INTEGER | Não | Sim | NULL |
| document_name | TEXT | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| service_id | services | id |

---

## Tabela: `service_priorities`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| service_id | INTEGER | Não | Sim | NULL |
| priority_name | TEXT | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| service_id | services | id |

---

## Tabela: `service_categories`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| service_id | INTEGER | Sim | Sim | NULL |
| category_id | INTEGER | Não | Sim | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| category_id | categories | id |
| service_id | services | id |

### Índices

| Nome do Índice | Único |
|---|---|
| sqlite_autoindex_service_categories_1 | Sim |

---

## Tabela: `service_history`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| service_id | INTEGER | Não | Sim | NULL |
| user_id | INTEGER | Não | Sim | NULL |
| action | TEXT | Não | Sim | NULL |
| field_name | TEXT | Não | Não | NULL |
| old_value | TEXT | Não | Não | NULL |
| new_value | TEXT | Não | Não | NULL |
| ip_address | TEXT | Não | Não | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| user_id | users | id |
| service_id | services | id |

---

## Tabela: `rag_queries`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| user_id | TEXT | Não | Não | NULL |
| query | TEXT | Não | Sim | NULL |
| intent_detected | TEXT | Não | Não | NULL |
| answer | TEXT | Não | Não | NULL |
| sources_matched | TEXT | Não | Não | NULL |
| latency_ms | REAL | Não | Não | NULL |
| tokens_used | INTEGER | Não | Não | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |
| message_id | INTEGER | Não | Não | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| message_id | chat_messages | id |

---

## Tabela: `chat_sessions`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | TEXT | Sim | Não | NULL |
| user_id | TEXT | Não | Não | NULL |
| title | TEXT | Não | Não | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Índices

| Nome do Índice | Único |
|---|---|
| sqlite_autoindex_chat_sessions_1 | Sim |

---

## Tabela: `chat_messages`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| session_id | TEXT | Não | Sim | NULL |
| role | TEXT | Não | Não | NULL |
| content | TEXT | Não | Sim | NULL |
| tokens | INTEGER | Não | Não | 0 |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| session_id | chat_sessions | id |

### Índices

| Nome do Índice | Único |
|---|---|
| idx_chat_messages_session | Não |

---

## Tabela: `chat_feedback`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| message_id | INTEGER | Não | Sim | NULL |
| positive | INTEGER | Não | Não | NULL |
| comment | TEXT | Não | Não | NULL |
| created_at | TIMESTAMP | Não | Não | CURRENT_TIMESTAMP |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| message_id | chat_messages | id |

---

## Tabela: `secretaria_unidades`

### Campos

| Campo | Tipo | Chave Primária | Não Nulo | Valor Padrão |
|---|---|---|---|---|
| id | INTEGER | Sim | Não | NULL |
| secretaria_id | INTEGER | Não | Não | NULL |
| name | TEXT | Não | Sim | NULL |
| address | TEXT | Não | Sim | NULL |
| phone | TEXT | Não | Não | NULL |
| working_hours | TEXT | Não | Não | NULL |

### Chaves Estrangeiras

| Campo local | Tabela referenciada | Campo referenciado |
|---|---|---|
| secretaria_id | secretarias | id |

---

---
[Avançar: Estrutura](Estrutura.md) | [Voltar: DER](DER.md)
