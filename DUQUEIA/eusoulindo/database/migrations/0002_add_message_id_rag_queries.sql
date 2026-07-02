-- Migration: 0002_add_message_id_rag_queries.sql
-- Duque IA — Rastreabilidade RAG -> Chat
-- Aplicada em: 2026-06-30
-- Descrição: Adiciona coluna message_id em rag_queries apontando para chat_messages(id)
--            para permitir rastrear qual busca RAG originou qual resposta de chat.

ALTER TABLE rag_queries ADD COLUMN message_id INTEGER REFERENCES chat_messages(id) ON DELETE SET NULL;
