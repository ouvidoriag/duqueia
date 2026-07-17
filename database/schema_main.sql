-- Tabela 'secretarias': Armazena os dados cadastrais das secretarias municipais de Duque de Caxias.
CREATE TABLE IF NOT EXISTS secretarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    address TEXT,
    phone TEXT,
    email TEXT,
    working_hours TEXT
);

-- Tabela 'secretaria_unidades': Armazena as unidades físicas descentralizadas associadas às secretarias (como postos de CRAS).
CREATE TABLE IF NOT EXISTS secretaria_unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secretaria_id INTEGER,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT,
    working_hours TEXT,
    FOREIGN KEY(secretaria_id) REFERENCES secretarias(id) ON DELETE CASCADE
);

-- Tabela 'categories': Armazena as categorias de taxonomia dos serviços da prefeitura.
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secretaria_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (secretaria_id) REFERENCES secretarias(id) ON DELETE CASCADE
);

-- Tabela 'services': Armazena a Carta de Serviços oficial da Prefeitura de Duque de Caxias, contendo prazos, custos e canais de acesso.
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
    FOREIGN KEY (secretaria_id) REFERENCES secretarias(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
);

-- Tabela 'service_phones': Armazena os telefones específicos para suporte de cada serviço público municipal.
CREATE TABLE IF NOT EXISTS service_phones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

-- Tabela 'service_emails': Armazena os e-mails institucionais específicos de suporte de cada serviço.
CREATE TABLE IF NOT EXISTS service_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

-- Tabela 'service_links': Armazena os links ou URLs de acesso a formulários e canais digitais de cada serviço.
CREATE TABLE IF NOT EXISTS service_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    link TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

-- Tabela 'service_steps': Armazena o passo a passo ou fluxo sequencial de execução de cada serviço municipal.
CREATE TABLE IF NOT EXISTS service_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

-- Tabela 'service_documents': Armazena a lista de documentos obrigatórios exigidos do munícipe para iniciar cada serviço.
CREATE TABLE IF NOT EXISTS service_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    document_name TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

-- Tabela 'service_priorities': Armazena regras de atendimento prioritário ou legislações específicas de prioridades aplicáveis ao serviço.
CREATE TABLE IF NOT EXISTS service_priorities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    priority_name TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

-- Tabela 'service_categories': Tabela de relacionamento muitos-para-muitos associando serviços a múltiplas categorias de taxonomia.
CREATE TABLE IF NOT EXISTS service_categories (
    service_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (service_id, category_id),
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
);

-- Tabela 'users': Armazena dados cadastrais de usuários do painel administrativo para controle de login e permissões.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secretaria_id INTEGER NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'editor', 'viewer')) DEFAULT 'editor',
    FOREIGN KEY (secretaria_id) REFERENCES secretarias(id) ON DELETE CASCADE
);

-- Tabela 'service_history': Armazena o registro de auditoria e log de modificações cadastrais realizadas nos serviços por usuários do painel.
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

DROP VIEW IF EXISTS vw_ia_servicos;

-- View 'vw_ia_servicos': Consolida dados estruturados combinados de secretarias e serviços ativos para indexação e consultas rápidas do RAG.
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
