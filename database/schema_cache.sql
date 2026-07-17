-- Tabela 'triage_cache': Armazena as decisões semânticas anteriores da triagem de intenções em cache local, evitando chamadas repetidas à API de LLM.
CREATE TABLE IF NOT EXISTS triage_cache (
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
