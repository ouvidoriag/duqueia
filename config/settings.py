import os
from dotenv import load_dotenv

# Carrega o .env localizado na raiz do projeto
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# Diretório base dos bancos de dados
_DB_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "data", "db"))

# Definição e caminhos de conexões dos bancos separados (Etapa 1)
DATABASE_MAIN = os.path.abspath(os.getenv("DATABASE_MAIN", os.path.join(_DB_DIR, "main.db")))
DATABASE_VECTOR = os.path.abspath(os.getenv("DATABASE_VECTOR", os.path.join(_DB_DIR, "vector.db")))
DATABASE_CACHE = os.path.abspath(os.getenv("DATABASE_CACHE", os.path.join(_DB_DIR, "cache.db")))
DATABASE_TELEMETRY = os.path.abspath(os.getenv("DATABASE_TELEMETRY", os.path.join(_DB_DIR, "telemetry.db")))

# Caminho de compatibilidade legada
DEFAULT_DB_PATH = DATABASE_MAIN

# Configurações de execução e ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
USE_TRIAGE_LAYER = os.getenv("USE_TRIAGE_LAYER", "true").lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "gemini-3.1-flash-lite")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")

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

# Dados de contato centralizados da Ouvidoria Geral
OUVIDORIA_CONTACTS = {
    "telefone": "(21) 2652-3835",
    "whatsapp": None,
    "email": "ouvidoria@duquedecaxias.rj.gov.br",
    "presencial": "Alameda Esmeralda, 206 - Jardim Primavera",
    "colab_url": "https://duquedecaxias.colab.re",
    "colab_url_clean": "duquedecaxias.colab.re"
}

# Mensagens de segurança e fallback padronizadas
PRIVACY_BLOCKED_MESSAGE = (
    "Por motivos de segurança e privacidade (LGPD), não tenho autorização para fornecer dados pessoais, "
    "CPFs ou andamento de solicitações de terceiros. Por favor, consulte o andamento de suas próprias solicitações "
    "nos canais oficiais identificados."
)

COMPETENCY_BLOCKED_MESSAGE = (
    "Esta pergunta não está inserida nos temas que são de responsabilidade da Prefeitura de Duque de Caxias. "
    "O metrô, por exemplo, é um transporte de âmbito estadual, e não compete à prefeitura municipal."
)

LEGAL_BLOCKED_MESSAGE = (
    "Como assistente virtual informativo, não realizo pareceres jurídicos, defesas, recursos ou interpretações de leis, "
    "nem formulo argumentos contra a administração pública. Para suporte legal, favor contatar a Procuradoria Geral do Município ou os órgãos competentes."
)

SECURITY_BLOCKED_MESSAGE = "Requisição bloqueada por motivos de segurança (Input Guardrail)."

HUMAN_ESCALATION_MESSAGE = (
    f"Sua solicitação envolve assuntos sensíveis ou denúncias que requerem atenção direta e sigilosa. "
    "Este canal informativo não processa esse tipo de demanda automaticamente. Por favor, registre formalmente "
    f"sua manifestação na **Ouvidoria Geral de Duque de Caxias**: telefone **{OUVIDORIA_CONTACTS['telefone']}**, "
    f"WhatsApp **{OUVIDORIA_CONTACTS['whatsapp']}**, e-mail **{OUVIDORIA_CONTACTS['email']}** "
    f"ou presencialmente na **{OUVIDORIA_CONTACTS['presencial']}**."
)
