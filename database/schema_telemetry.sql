-- Tabela 'rag_queries': Armazena dados de telemetria analítica de consultas processadas pelo RAG (latência, tokens utilizados e custos).
CREATE TABLE IF NOT EXISTS rag_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    intent_detected TEXT,
    response_text TEXT,
    confidence_score REAL,
    sources_used TEXT,
    total_time_ms REAL,
    llm_time_ms REAL,
    tokens_used INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela 'chat_sessions': Armazena os identificadores das sessões de chat de conversação ativas dos munícipes.
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela 'chat_messages': Armazena o histórico completo de diálogos (turnos de perguntas do munícipe e respostas da IA) associado à sessão.
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    turn_index INTEGER DEFAULT 1,
    intent TEXT,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- Tabela 'chat_feedback': Armazena avaliações de utilidade (likes/dislikes) enviadas pelos munícipes sobre as respostas da IA.
CREATE TABLE IF NOT EXISTS chat_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    feedback_type TEXT CHECK(feedback_type IN ('upvote', 'downvote')),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    topic TEXT,
    FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_turn ON chat_messages(session_id, turn_index);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_feedback_created ON chat_feedback(created_at);

-- Trigger para garantir que a sessão exista automaticamente em chat_sessions antes de inserir a mensagem
CREATE TRIGGER IF NOT EXISTS trg_chat_messages_auto_session
BEFORE INSERT ON chat_messages
FOR EACH ROW
WHEN new.session_id IS NOT NULL AND new.session_id != ''
BEGIN
    INSERT OR IGNORE INTO chat_sessions (id, created_at)
    VALUES (new.session_id, CURRENT_TIMESTAMP);
END;
