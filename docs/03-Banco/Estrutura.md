# Estrutura Física do Banco de Dados — Duque IA

O banco de dados SQLite (`agent/duque_ia.db`) utiliza uma estrutura de índices e restrições para garantir a performance e integridade dos dados.

## Índices Físicos Criados
- `idx_chunks_category`: Indexa a coluna `category` na tabela `duque_ia_chunks` para permitir filtros rápidos de escopo de busca RAG.
- `idx_chunks_source`: Indexa a coluna `source` para auditoria rápida de documentos indexados.
- `idx_chat_messages_session`: Indexa `session_id` em `chat_messages` para recuperar rapidamente o histórico de chat da sessão do usuário.
- `idx_triage_cache_hash`: Indexa `query_hash` em `triage_cache` para acelerar respostas repetidas em consultas de triagem semântica.

## Restrições (Constraints)
- Chaves primárias com auto-incremento garantidas na maioria das tabelas de histórico e mensagens.
- Integridade referencial ativada (`PRAGMA foreign_keys = ON`) para cascatear exclusão de mensagens se uma sessão for removida.

---
[Avançar: Migrations](Migrations.md) | [Voltar: Dicionário](Dicionario.md)
