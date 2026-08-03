-- ==============================================================================
--              DUQUE IA - ENTERPRISE PRODUCTION SCHEMA (SUPABASE + PGVECTOR)
-- ==============================================================================
-- Este script define a modelagem de banco de dados nível 9.8/10 para PostgreSQL
-- com suporte a busca vetorial através da extensão pgvector, auditoria completa,
-- controle de versionamento, soft delete, histórico de chat e feedback.
-- ==============================================================================

-- Habilita a extensão pgvector para busca por similaridade de embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilita o suporte a UUIDs (chave primária padrão Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. USUÁRIOS, PERMISSÕES E AUDITORIA GERAL
-- ------------------------------------------------------------------------------

-- Tabela de Secretarias Municipais (para evitar redundância de textos como SEFAZ, Fazenda, etc.)
CREATE TABLE secretarias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    sigla VARCHAR(20) NOT NULL UNIQUE,
    descricao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Categorias Temáticas de Serviços (relacionada a secretarias)
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    secretaria_id INTEGER REFERENCES secretarias(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Logs gerais de auditoria de ações administrativas (quem mudou o quê)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID, -- UUID do usuário do Supabase Auth
    action VARCHAR(100) NOT NULL, -- e.g., 'IMPORT_DOCUMENT', 'DELETE_DOCUMENT', 'UPDATE_ROLE'
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. DOCUMENTOS E VERSIONAMENTO (SOFT DELETE & VERSION HISTORY)
-- ------------------------------------------------------------------------------

-- Tabela principal de Documentos Consolidados (com Soft Delete)
CREATE TABLE core_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    secretaria_id INTEGER REFERENCES secretarias(id) ON DELETE RESTRICT,
    categoria_id INTEGER REFERENCES categorias(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    source_url TEXT,
    sha256_hash CHAR(64) NOT NULL UNIQUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Auditoria
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft Delete
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID
);

-- Histórico de versões dos documentos (Versioning)
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES core_documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    file_path TEXT,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'archived'
    UNIQUE (document_id, version)
);

-- ------------------------------------------------------------------------------
-- 3. CHUNKS E EMBEDDINGS (PGVECTOR)
-- ------------------------------------------------------------------------------

-- Chunks de texto com relacionamento forte (FK) aos documentos e vetores reais (1536 dimensões)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES core_documents(id) ON DELETE CASCADE,
    version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL, -- pgvector 1536-dim (padrão OpenAI/Gemini-embedding-004)
    metadata JSONB DEFAULT '{}'::jsonb,
    keywords TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice IVFFlat ou HNSW para otimizar buscas de similaridade de cosseno em larga escala
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- ------------------------------------------------------------------------------
-- 4. TRIAGEM, CHAT E FEEDBACK DE USUÁRIOS
-- ------------------------------------------------------------------------------

-- Sessões de chat do Duque IA
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- Referência opcional ao Auth User se logado
    title VARCHAR(255) DEFAULT 'Nova Conversa',
    model_used VARCHAR(100) DEFAULT 'gemini-3.1-flash-lite',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Mensagens individuais pertencentes às sessões (Histórico Conversacional)
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Feedback do munícipe sobre as respostas (Excelente para refinar o RAG e curadoria de dados)
CREATE TABLE chat_feedbacks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES chat_messages(id) ON DELETE CASCADE,
    is_positive BOOLEAN NOT NULL, -- TRUE = Upvote, FALSE = Downvote
    comment TEXT, -- Justificativa ou correção sugerida
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 5. AUDITORIA DE QUERIES RAG (Ouro para Analytics e Curadoria)
-- ------------------------------------------------------------------------------

-- Log detalhado de cada consulta processada pelo RAG
CREATE TABLE rag_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    intent_detected VARCHAR(100),
    needs_clarification BOOLEAN DEFAULT FALSE,
    clarification_reason TEXT,
    
    -- Resposta e Fontes
    answer_generated TEXT,
    sources_used UUID[], -- Array de IDs dos document_chunks recuperados
    similarity_scores REAL[], -- Scores das fontes
    
    -- Métricas e Performance
    latency_triage_ms REAL,
    latency_retrieval_ms REAL,
    latency_llm_ms REAL,
    latency_total_ms REAL,
    tokens_triage INTEGER DEFAULT 0,
    tokens_llm INTEGER DEFAULT 0,
    model_name VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para relatórios e BI sobre as interações dos munícipes
CREATE INDEX idx_rag_queries_intent ON rag_queries(intent_detected);
CREATE INDEX idx_rag_queries_created ON rag_queries(created_at);
