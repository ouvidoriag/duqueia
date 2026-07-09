import os

# Caminho padrão do banco de dados
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "duque_ia.db")

# Política categorizada de pesos de keywords
KEYWORD_POLICY = {
    "noise": {
        "prefeitura": 0.2,
        "secretaria": 0.2,
        "municipal": 0.2,
        "duque": 0.2,
        "caxias": 0.2,
        "como": 0.1,
        "onde": 0.1,
        "quero": 0.1,
        "saber": 0.1,
        "favor": 0.1,
        "solicitar": 0.2,
        "departamento": 0.1,
        "coordenadoria": 0.1,
        "diretoria": 0.1,
        "subsecretaria": 0.1
    },
    "service": {
        "cras": 2.0,
        "iptu": 2.0,
        "alvara": 2.0,
        "alvará": 2.0,
        "previdencia": 2.0,
        "previdência": 2.0,
        "fundec": 2.0,
        "saude": 2.0,
        "saúde": 2.0,
        "vacina": 2.0,
        "consulta": 2.0,
        "exame": 2.0,
        "transporte": 2.0,
        "ônibus": 2.0,
        "ouvidoria": 2.0,
        "limpeza": 2.0,
        "capina": 2.0,
        "buraco": 2.0,
        "iluminacao": 2.0,
        "iluminação": 2.0,
        "lixo": 2.0
    },
    "entity": {
        "rua": 3.0,
        "avenida": 3.0,
        "bairro": 3.0,
        "distrito": 3.0,
        "lote": 3.0,
        "quadra": 3.0,
        "prefeito": 3.0,
        "ipmdc": 3.0
    }
}

# Mapa de intenções de listagem: padrão de query → categoria do banco
LIST_INTENT_MAP = {
    "secretarias": {
        "triggers": ["quais secretarias", "todas secretarias", "secretarias existem",
                     "secretarias da prefeitura", "estrutura da prefeitura", "órgãos municipais",
                     "listar secretarias", "lista de secretarias", "quantas secretarias",
                     "quais são as secretarias", "orgaos municipais"],
        "db_category": "secretarias",
        "db_filter_field": "category"
    },
    "servicos": {
        "triggers": ["quais serviços", "todos os serviços", "serviços disponíveis",
                     "carta de serviços", "lista de serviços", "o que a prefeitura oferece"],
        "db_category": "carta_servicos",
        "db_filter_field": "category"
    },
    "cursos": {
        "triggers": ["quais os cursos", "quais cursos", "cursos oferecidos", "cursos da fundec", 
                     "lista de cursos", "cursos que a fundec", "cursos da fundec oferecidos"],
        "db_category": "cursos",
        "db_filter_field": "special"
    }
}

# Dimensões esperadas por modelo de embedding
EMBEDDING_DIMS = {
    "gemini-embedding-2": 3072,
    "gemini-embedding-2-preview": 3072,
    "gemini-embedding-001": 3072,
    "text-embedding-004": 768,
    "text-embedding-3-small": 1536,
    "deterministic_hash_768": 768,
}
