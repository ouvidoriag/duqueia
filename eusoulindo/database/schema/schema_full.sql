-- Duque IA — Schema Completo (auto-sincronizado)
-- Última sincronização: 2026-07-02 13:03:21

PRAGMA foreign_keys = ON;

-- VIEW: vw_ia_servicos
CREATE VIEW vw_ia_servicos AS
    SELECT 
        s.id AS servico_id,
        sec.name AS secretaria_nome,
        sec.code AS secretaria_codigo,
        s.name AS servico_nome,
        c.name AS categoria,
        s.description AS descricao,
        s.how_to_access AS como_acessar,
        s.who_can_request AS quem_pode_solicitar,
        s.waiting_time AS tempo_espera,
        s.max_deadline AS prazo_maximo,
        s.cost AS custo,
        s.regulation_norm AS norma_reguladora
    FROM services s
    LEFT JOIN secretarias sec ON s.secretaria_id = sec.id
    LEFT JOIN categories c ON s.category_id = c.id
    WHERE s.status = 'published';

-- TABLE: categories
CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        secretaria_id INTEGER DEFAULT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (secretaria_id) REFERENCES secretarias (id) ON DELETE CASCADE
    );

-- TABLE: chat_feedback
CREATE TABLE chat_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    positive INTEGER CHECK(positive IN (0, 1)), -- 1 para positivo, 0 para negativo
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(message_id) REFERENCES chat_messages(id)
);

-- TABLE: chat_messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
);

-- TABLE: chat_sessions
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY, -- Session UUID ou string
    user_id TEXT,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: chunks_metadata
CREATE TABLE chunks_metadata (
        id TEXT PRIMARY KEY,
        document_id TEXT,
        chunk_index INTEGER,
        token_count INTEGER,
        content TEXT NOT NULL,
        relevance_weight INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES core_documents (id) ON DELETE CASCADE
    );

-- TABLE: core_documents
CREATE TABLE core_documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        secretaria TEXT,
        category TEXT,
        sha256_hash TEXT UNIQUE,
        total_chunks INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER
    );

-- TABLE: duque_ia_chunks
CREATE TABLE duque_ia_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        category TEXT,
        content TEXT NOT NULL,
        embedding TEXT, -- Armazenado como JSON string de float list
        metadata TEXT,   -- Armazenado como JSON string
        keywords TEXT,   -- Armazenado como JSON string de lista de palavras-chave
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- TABLE: embedding_metadata
CREATE TABLE embedding_metadata (
            provider TEXT,
            model TEXT,
            dimension INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

-- TABLE: rag_queries
CREATE TABLE rag_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    query TEXT NOT NULL,
    intent_detected TEXT,
    answer TEXT,
    sources_matched TEXT, -- Armazena JSON array com as fontes utilizadas
    latency_ms REAL,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
, message_id INTEGER REFERENCES chat_messages(id) ON DELETE SET NULL);

-- TABLE: secretaria_unidades
CREATE TABLE secretaria_unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secretaria_id INTEGER,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT,
    working_hours TEXT,
    FOREIGN KEY(secretaria_id) REFERENCES secretarias(id)
);

-- TABLE: secretarias
CREATE TABLE secretarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE
    , address TEXT, phone TEXT, email TEXT, working_hours TEXT);

-- TABLE: service_categories
CREATE TABLE service_categories (
        service_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (service_id, category_id),
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    );

-- TABLE: service_documents
CREATE TABLE service_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        document_name TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );

-- TABLE: service_emails
CREATE TABLE service_emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        email TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );

-- TABLE: service_history
CREATE TABLE service_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        field_name TEXT DEFAULT NULL,
        old_value TEXT DEFAULT NULL,
        new_value TEXT DEFAULT NULL,
        ip_address TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

-- TABLE: service_links
CREATE TABLE service_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        link TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );

-- TABLE: service_phones
CREATE TABLE service_phones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        phone TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );

-- TABLE: service_priorities
CREATE TABLE service_priorities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        priority_name TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );

-- TABLE: service_steps
CREATE TABLE service_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        step_number INTEGER NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );

-- TABLE: services
CREATE TABLE services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        secretaria_id INTEGER NOT NULL,
        category_id INTEGER DEFAULT NULL,
        name TEXT NOT NULL,
        description TEXT,
        how_to_access TEXT,
        address TEXT,
        who_can_request TEXT,
        waiting_time TEXT DEFAULT NULL,
        max_deadline TEXT DEFAULT NULL,
        cost TEXT DEFAULT NULL,
        regulation_norm TEXT,
        status TEXT NOT NULL DEFAULT 'published',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (secretaria_id) REFERENCES secretarias (id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
    );

-- TABLE: triage_cache
CREATE TABLE triage_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT NOT NULL,
            intent TEXT NOT NULL,
            confidence REAL NOT NULL,
            needs_clarification INTEGER NOT NULL,
            reason TEXT,
            model_version TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(query_hash, prompt_version)
        );

-- TABLE: users
CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        secretaria_id INTEGER NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin', 'editor', 'viewer')) DEFAULT 'editor',
        FOREIGN KEY (secretaria_id) REFERENCES secretarias (id) ON DELETE CASCADE
    );

-- INDEX: idx_chunks_category
CREATE INDEX idx_chunks_category ON duque_ia_chunks(category);

-- INDEX: idx_chunks_source
CREATE INDEX idx_chunks_source ON duque_ia_chunks(source);
