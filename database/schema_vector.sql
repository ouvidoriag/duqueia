-- Tabela 'duque_ia_chunks': Armazena os chunks de texto extraídos das fontes do RAG e suas representações vetoriais de embeddings (para busca semântica).
CREATE TABLE IF NOT EXISTS duque_ia_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    category TEXT,
    content TEXT NOT NULL,
    embedding TEXT,
    metadata TEXT,
    keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela 'core_documents': Armazena metadados de arquivos inteiros processados pelo pipeline (como hashes SHA256 para controle de modificações).
CREATE TABLE IF NOT EXISTS core_documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    secretaria TEXT,
    category TEXT,
    sha256_hash TEXT UNIQUE,
    total_chunks INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER
);

-- Tabela 'chunks_metadata': Mantém informações adicionais de rastreabilidade associando cada fragmento (chunk) ao seu documento mestre.
CREATE TABLE IF NOT EXISTS chunks_metadata (
    id TEXT PRIMARY KEY,
    document_id TEXT,
    chunk_index INTEGER,
    token_count INTEGER,
    content TEXT NOT NULL,
    relevance_weight INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES core_documents (id) ON DELETE CASCADE
);

-- Tabela 'embedding_metadata': Armazena os metadados técnicos do provedor, modelo e dimensões dos vetores utilizados no banco para fins de compatibilidade no runtime.
CREATE TABLE IF NOT EXISTS embedding_metadata (
    provider TEXT,
    model TEXT,
    dimension INTEGER
);
