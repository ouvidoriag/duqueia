# Estrutura Declarativa de Bancos — DUQUE IA

Este diretório concentra a modelagem de dados do ecossistema do **DUQUE IA**, separada por arquivos DDL e índices correspondentes a cada domínio (Etapa 1 da arquitetura de produção).

---

## Estrutura Física e Arquivos SQL

### 1. Principal Relacional (`main.db`)
*   **Finalidade:** Contém dados de secretarias municipais, Carta de Serviços, prioridades e unidades de atendimento (CRAS).
*   **Arquivos:**
    *   `database/schema_main.sql`: Definição de tabelas, relacionamentos e a View Cognitiva `vw_ia_servicos`.
    *   `database/indexes_main.sql`: Índices para chaves estrangeiras (`service_id`, `secretaria_id`).

### 2. Busca Vetorial Semântica (`vector.db`)
*   **Finalidade:** Chunks de textos longos de documentos oficiais e metadados de embeddings.
*   **Arquivos:**
    *   `database/schema_vector.sql`: Tabelas `duque_ia_chunks` e metadados do modelo.
    *   `database/indexes_vector.sql`: Índices por categoria e fonte.

### 3. Cache de Triagem (`cache.db`)
*   **Finalidade:** Respostas de intenções do LangGraph Lite pré-classificadas para melhorar performance e economia de chamadas LLM.
*   **Arquivos:**
    *   `database/schema_cache.sql`: Tabela `triage_cache` com indexação única.

### 4. Telemetria e Instrumentação (`telemetry.db`)
*   **Finalidade:** Histórico de queries de RAG, chat logs do usuário e feedbacks de interações.
*   **Arquivos:**
    *   `database/schema_telemetry.sql`: Tabelas de chats, feedbacks e observabilidade.
