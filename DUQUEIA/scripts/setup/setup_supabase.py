import os
import sqlite3

def setup_database():
    """Inicializa as tabelas do banco de dados (SQLite local e PGVector no Supabase)."""
    print("==========================================================")
    print("        INICIALIZAÇÃO DO BANCO DE DADOS (DUQUE IA)        ")
    print("==========================================================")
    
    # 1. Configuração do SQLite Local (Fallback de Desenvolvimento)
    sqlite_path = os.path.join("agent", "duque_ia.db")
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    
    print(f"Criando/Conectando ao banco de dados SQLite local em: {sqlite_path}")
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Cria a tabela de documentos/chunks com suporte a texto, embeddings (armazenados como blobs/json) e metadados
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duque_ia_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        category TEXT,
        content TEXT NOT NULL,
        embedding TEXT, -- Armazenado como JSON string de float list
        metadata TEXT,   -- Armazenado como JSON string
        keywords TEXT,   -- Armazenado como JSON string de lista de palavras-chave
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # --- NOVAS TABELAS ESTRUTURADAS E COGNITIVAS (EVOLUÇÃO) ---
    
    # 1. Tabelas de RAG divididas
    cursor.execute("""
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
    """)
    
    cursor.execute("""
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
    """)

    # 2. Tabelas do escopo relacional de Secretarias e Serviços
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS secretarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        secretaria_id INTEGER NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin', 'editor', 'viewer')) DEFAULT 'editor',
        FOREIGN KEY (secretaria_id) REFERENCES secretarias (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        secretaria_id INTEGER DEFAULT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (secretaria_id) REFERENCES secretarias (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
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
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_phones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        phone TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        email TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        link TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        step_number INTEGER NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        document_name TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_priorities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        priority_name TEXT NOT NULL,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_categories (
        service_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (service_id, category_id),
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_history (
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
    """)

    # 3. View Cognitiva para a IA (vw_ia_servicos)
    cursor.execute("DROP VIEW IF EXISTS vw_ia_servicos;")
    cursor.execute("""
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
    """)
    
    # Cria índices para otimização de buscas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source ON duque_ia_chunks(source);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_category ON duque_ia_chunks(category);")
    
    conn.commit()
    conn.close()
    print("-> Banco de dados SQLite local inicializado com sucesso!")

    # 2. Configuração do Supabase (Se configurado no .env)
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        print(f"\n[Supabase] Detectada configuração do Supabase: {supabase_url}")
        print("Para configurar a tabela de PGVector no Supabase, execute a query abaixo no editor SQL:")
        sql_commands = """
        CREATE EXTENSION IF NOT EXISTS vector;
        
        CREATE TABLE IF NOT EXISTS duque_ia_embeddings (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            content text NOT NULL,
            embedding vector(1536),
            metadata jsonb,
            created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS duque_ia_embeddings_hnsw_idx 
        ON duque_ia_embeddings USING hnsw (embedding vector_cosine_ops);
        """
        print(sql_commands)
    else:
        print("\n[Nota] Para produção no Supabase, configure o arquivo .env com a SUPABASE_URL.")

if __name__ == "__main__":
    setup_database()
