-- Migration: 0001_initial_schema.sql
-- Duque IA — Migração Inicial
-- Aplicada em: 2026-06-30
-- Descrição: Criação do schema completo do banco de dados local SQLite.

-- (Este arquivo é equivalente ao schema_full.sql gerado na data acima)
-- Para reaplicar: python database/scripts/rebuild_db.py

-- HISTÓRICO DE MIGRAÇÕES:
-- 0001 | 2026-06-30 | Criação inicial do banco Duque IA
-- 0002 | 2026-06-30       | Adição de message_id em rag_queries (FK -> chat_messages)
