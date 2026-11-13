import sys
import re
import sqlite3
from typing import Optional, Set
from config.settings import GEMINI_FAST_MODEL, OUVIDORIA_CONTACTS, DATABASE_MAIN

# Telefones de emergência e serviços essenciais padronizados nacionalmente
OFFICIAL_SHORT_PHONES = {"190", "192", "193", "199", "100", "180", "181", "153", "141"}

# Telefones oficiais centrais da Prefeitura de Duque de Caxias e concessionárias de utilidade pública
OFFICIAL_CANONICAL_PHONES = {
    "26523835",     # Ouvidoria Geral (Telefone Fixo Oficial - Ouvidoria NÃO tem WhatsApp)
    "26764444",     # Defesa Civil Caxias
    "26732203",     # Defesa Civil Caxias
    "27734550",     # IPMDC Caxias
    "22531177",     # Disque Denúncia RJ
    "36566697",     # Obras / Serviços
    # Concessionárias essenciais atuantes no território municipal de Duque de Caxias
    "08000210196",  # Light (Emergência e Alta Tensão)
    "08001950195",  # Águas do Rio (Saneamento e Esgoto)
    "972118064",    # WhatsApp Oficial Águas do Rio
    "21972118064",  # WhatsApp Oficial Águas do Rio (com DDD)
    "08000249040",  # AGENERSA (Agência Reguladora de Energia e Saneamento do RJ)
    "08000240197",  # Naturgy (Gás Canalizado)
    "08000000755",  # Iluminação Pública
    "08007787272",  # Iluminação Pública
    # Órgãos municipais de atendimento e defesa do consumidor
    "971797900",    # WhatsApp Petzap (Proteção Animal - SMPA)
    "21971797900",  # WhatsApp Petzap (Proteção Animal - SMPA com DDD)
    "27736200",     # Central Geral da Prefeitura de Duque de Caxias
    "26726668",     # PROCON Duque de Caxias
    "26728800",     # Secretaria Municipal de Saúde (SMS)
}

_CACHED_DB_PHONES: Optional[Set[str]] = None
_CACHED_DB_EMAILS: Optional[Set[str]] = None

def _get_db_phones() -> Set[str]:
    """Carrega sob demanda e armazena em cache todos os telefones oficiais cadastrados no main.db."""
    global _CACHED_DB_PHONES
    if _CACHED_DB_PHONES is not None:
        return _CACHED_DB_PHONES
    phones: Set[str] = set()
    try:
        with sqlite3.connect(DATABASE_MAIN, timeout=5.0) as conn:
            cur = conn.cursor()
            for row in cur.execute("SELECT phone FROM secretarias WHERE phone IS NOT NULL AND phone != ''").fetchall():
                clean = re.sub(r'\D', '', row[0])
                if clean:
                    phones.add(clean)
                    if len(clean) in (10, 11) and clean.startswith("21"):
                        phones.add(clean[2:])
            for row in cur.execute("SELECT phone FROM service_phones WHERE phone IS NOT NULL AND phone != ''").fetchall():
                clean = re.sub(r'\D', '', row[0])
                if clean:
                    phones.add(clean)
                    if len(clean) in (10, 11) and clean.startswith("21"):
                        phones.add(clean[2:])
            try:
                for row in cur.execute("SELECT phone FROM secretaria_unidades WHERE phone IS NOT NULL AND phone != ''").fetchall():
                    clean = re.sub(r'\D', '', row[0])
                    if clean:
                        phones.add(clean)
                        if len(clean) in (10, 11) and clean.startswith("21"):
                            phones.add(clean[2:])
            except Exception:
                pass
            try:
                for row in cur.execute("SELECT telefone FROM escolas_municipais WHERE telefone IS NOT NULL AND telefone != ''").fetchall():
                    clean = re.sub(r'\D', '', row[0])
                    if clean:
                        phones.add(clean)
                        if len(clean) in (10, 11) and clean.startswith("21"):
                            phones.add(clean[2:])
            except Exception:
                pass
    except Exception:
        pass
    _CACHED_DB_PHONES = phones
    return _CACHED_DB_PHONES

def _get_db_emails() -> Set[str]:
    """Carrega sob demanda e armazena em cache todos os e-mails oficiais cadastrados no main.db."""
    global _CACHED_DB_EMAILS
    if _CACHED_DB_EMAILS is not None:
        return _CACHED_DB_EMAILS
    emails: Set[str] = set()
    try:
        with sqlite3.connect(DATABASE_MAIN, timeout=5.0) as conn:
            cur = conn.cursor()
            for row in cur.execute("SELECT email FROM secretarias WHERE email IS NOT NULL AND email != ''").fetchall():
                e = row[0].strip().lower()
                if "@" in e:
                    emails.add(e)
            for row in cur.execute("SELECT email FROM service_emails WHERE email IS NOT NULL AND email != ''").fetchall():
                e = row[0].strip().lower()
                if "@" in e:
                    emails.add(e)
            try:
                for row in cur.execute("SELECT email FROM escolas_municipais WHERE email IS NOT NULL AND email != ''").fetchall():
                    e = row[0].strip().lower()
                    if "@" in e:
                        emails.add(e)
            except Exception:
                pass
    except Exception:
        pass
    _CACHED_DB_EMAILS = emails
    return _CACHED_DB_EMAILS

def extract_candidate_phones(text: str) -> list[str]:
    """
    Extrai números de telefone (fixos, celulares, 0800 e códigos de emergência),
    filtrando intervalos de anos e mandatos (ex: 2025-2028 ou 1990-1994).
    """
    phone_pattern = r'(?:\b0800[-.\s]?\d{3}[-.\s]?\d{4}\b)|(?:(?:\(?\d{2}\)?\s*)?(?:[23]\d{3}|9\d{4})[-.\s]?\d{4})'
    raw_matches = re.findall(phone_pattern, text)
    valid_phones = []
    for m in raw_matches:
        clean = re.sub(r'\D', '', m)
        # Exclui intervalos de anos (ex: 2025-2028, 1990-1994)
        if len(clean) == 8 and (clean.startswith('19') or clean.startswith('20')) and (clean[4:6] in ('19', '20')):
            continue
        valid_phones.append(m)
    return valid_phones

def is_phone_grounded(phone: str, context: Optional[str]) -> bool:
    """Verifica se um telefone é fundamentado no contexto ou no catálogo oficial municipal."""
    clean = re.sub(r'\D', '', phone)
    if not clean:
        return True

    # 1. Códigos de emergência de 3 dígitos
    if clean in OFFICIAL_SHORT_PHONES:
        return True

    # 2. Telefones canônicos centrais (Ouvidoria, Defesa Civil, etc.)
    local_digits = clean[2:] if len(clean) in (10, 11) and clean.startswith("21") else clean
    if clean in OFFICIAL_CANONICAL_PHONES or local_digits in OFFICIAL_CANONICAL_PHONES:
        return True

    # 3. Presente no contexto recuperado
    if context:
        if phone in context or local_digits in context:
            return True
        clean_ctx = re.sub(r'\D', '', context)
        if clean in clean_ctx or local_digits in clean_ctx:
            return True

    # 4. Presente no catálogo de secretarias e serviços do main.db
    db_phones = _get_db_phones()
    if clean in db_phones or local_digits in db_phones:
        return True

    return False

DANGEROUS_PATTERNS = [
    # SQL Injection explícito
    "drop table", "delete from", "insert into", "update set", "truncate table",
    "select * from", "union select", "; drop", "; delete", "; insert", "; update",
    "; select", "-- drop", "-- delete", "or 1=1", "' or '1'='1",
    # Prompt Injection
    "ignore as instruções", "ignore todas", "ignore previous",
    "esqueça tudo", "esqueça o que", "forget everything", "forget all",
    "act as", "now you are", "pretend you are", "simulate",
    "jailbreak", "dan mode", "developer mode", "unrestricted mode",
    "ignore your instructions", "override instructions",
    "finja ser", "finja que você", "você não é mais", "esqueça suas regras",
]

PROGRAMMING_TRIGGERS = [
    r"\b(?:código|codigo)\s+em\s+(?:python|javascript|java|c\+\+|html|css|php|sql|bash|ruby|rust)\b|\b(?:como\s+programar|gerar\s+codigo)\b"
]

PRIVACY_TRIGGERS = [
    r"cpf\s+(?:de|do|da|do\s+meu|da\s+minha|de\s+um|de\s+uma)?\s*(?:cidadão|cidadao|reclamante|outro|terceiro|vizinho|vizinha|fulano|sicrano|beltrano|wellington)",
    r"protocolo\s+.*(?:vizinho|vizinha|outro|outra|terceiro|terceira|fulano|sicrano|wellington)",
    r"nome\s+(?:dele|dela|do\s+vizinho|da\s+vizinha|do\s+reclamante|do\s+outro|da\s+outra)",
    r"dados\s+pessoais\s+(?:do|da|de)?\s*(?:vizinho|vizinha|terceiro|outro)",
    r"reclamaç(?:ão|ões|ao)\s+abertas?\s+por\s+(?:terceiro|outro|vizinho|vizinha)"
]

COMPETENCY_TRIGGERS = [
    # Transporte estadual/federal
    r"\bmetrô\b", r"\bmetro\b", r"\btrem\b", r"\bsuper\s?via\b",
    r"\bflumitrânsito\b", r"\bdetran\b",
    # Rodovias e órgãos federais
    r"\binss\b", r"\bprev\s?social\b", r"\bprevidência\s+social\b",
    r"\baposentadoria\s+(?:do\s+inss|federal|pelo\s+inss)\b", r"\bbenefício\s+(?:inss|previdência\s+social)\b",
    r"\bimposto\s+de\s+renda\b", r"\birpf\b", r"\breceita\s+federal\b",
    r"(?:renovar|alterar|regularizar)\s+(?:o\s+)?cpf\b", r"tirar\s+cpf\s+na\s+receita\b", r"consultar\s+cnpj\s+na\s+receita\b",
    r"\brodovia\s+(?:br|federal|estadual)\b", r"\bbr-\d{3}\b",
    r"\bpolicía\s+(?:federal|rodoviária|militar)\b",
    r"\bjustiça\s+(?:federal|estadual|trabalhista)\b",
    r"\btribunais?\b",
    # Outros municípios
    r"\brio\s+de\s+janeiro\s+(?:cidade|prefeitura)\b",
    r"\bsão\s+paulo\b", r"\bniterói\b", r"\bnova\s+iguaçu\b",
]

LEGAL_TRIGGERS = [
    r"formular\s+(?:defesa|parecer|recurso)",
    r"orientaç(?:ão|ões)\s+jurídica",
    r"argumentos?\s+contra\s+o\s+poder\s+público",
    r"como\s+a\s+administração\s+pública\s+deve\s+proceder\s+diante\s+de\s+reclamações\s+recorrentes",
    r"árvore\s+(?:caiu|derrubou)\s+no\s+(?:meu\s+)?(?:carro|veículo|veiculo|casa|telhado)",
    r"indenizaç(?:ão|ao)\s+prefeitura",
    r"prefeitura\s+pagar\s+(?:o\s+)?prejuízo",
    r"responsabilidade\s+civil\s+prefeitura"
]

HUMAN_ESCALATION_TRIGGERS = [
    r"desvi(?:o|ando)\s+verba|roub(?:o|ando)|suborn(?:o|ar|ando)|corrupç(?:ão|ao)|\bsecretário\s+roub\w+",
    r"\b(?:matar|agredir|violentar|assassinar|morrer|espancar|facada|tiros|tiroteio|balead[oa]s?|disparos?|arma\s+de\s+fogo)\b",
    r"\bmenor\b.*?\b(?:agressão|agressao|agredid[oa]|apanhando|espancad[oa]|maus-tratos|maustratos|abuso|violência|violencia)\b",
    r"\b(?:criança|crianca|menor|infantil)\b.*?\b(?:sofrendo|vítima|vitima|agredid[oa]|espancad[oa]|maus-tratos|maustratos|abuso)\b",
    r"\b(?:vizinho|pais?|mãe|mae|pai)\b.*?\b(?:menor|criança|crianca)\b.*?\b(?:agressão|agressao|apanhando|espancando|maus-tratos)\b"
]

def check_input_guardrail(query: str) -> bool:
    """Verifica se a query do usuário contém algum padrão perigoso de injeção."""
    q_lower = query.lower()
    return any(pat in q_lower for pat in DANGEROUS_PATTERNS)

def check_privacy_guardrail(query: str) -> bool:
    """Verifica violações de privacidade da LGPD (dados de terceiros)."""
    q_lower = query.lower()
    return any(re.search(pat, q_lower) for pat in PRIVACY_TRIGGERS)

def check_competency_guardrail(query: str) -> bool:
    """Verifica se a query é sobre assuntos fora de competência da prefeitura."""
    q_lower = query.lower()
    # Exceção legítima: IPMDC / Previdência e Aposentadoria de Servidores Municipais de Duque de Caxias
    if any(m in q_lower for m in ["ipmdc", "servidor municipal", "servidores municipais", "servidora municipal", "previdência municipal", "previdencia municipal", "magistério municipal", "magisterio municipal"]):
        return False
    return any(re.search(pat, q_lower) for pat in COMPETENCY_TRIGGERS)

def check_legal_guardrail(query: str) -> bool:
    """Verifica se o usuário solicita elaboração de peças ou pareceres jurídicos contra a prefeitura."""
    q_lower = query.lower()
    return any(re.search(pat, q_lower) for pat in LEGAL_TRIGGERS)

def sanitize_ouvidoria_whatsapp(text: str) -> str:
    """Remove qualquer menção ao número fictício 99824-5903 ou WhatsApp da Ouvidoria Geral."""
    if not text:
        return text
    cleaned = re.sub(
        r'(?im)^[ \t]*[•\*\-]?\s*(?:\*\*)?(?:WhatsApp(?:\s+da\s+Ouvidoria(?:\s+Geral)?)?|WhatsApp:?)(?:\*\*)?:?\s*(?:\(21\)\s*)?99824[-.\s]?5903[^\n]*\n?',
        '',
        text,
    )
    cleaned = re.sub(
        r'(?i)(?:,\s*)?(?:e\s+)?(?:ou\s+)?(?:pelo\s+)?WhatsApp(?:\s+da\s+Ouvidoria(?:\s+Geral)?)?\s*(?:\*\*)?(?:\(21\)\s*)?99824[-.\s]?5903(?:\*\*)?',
        '',
        cleaned,
    )
    cleaned = re.sub(r'(?i)(?:\(21\)\s*)?99824[-.\s]?5903', '', cleaned)
    return re.sub(r'\n{3,}', '\n\n', cleaned).strip()


def normalize_markdown(text: str) -> str:
    """Corrige quebras comuns de Markdown (listas misturadas, asteriscos soltos e linhas em branco)."""
    if not text:
        return text
    # Remove marcador duplicado como "1. * **Item**" ou "* 1. **Item**"
    fixed = re.sub(r'(?m)^(\s*\d+\.)\s+[\*\-•]\s+', r'\1 ', text)
    fixed = re.sub(r'(?m)^(\s*)[\*\-•]\s+(\d+\.)\s+', r'\1\2 ', fixed)
    # Normaliza bullets isolados para "* "
    fixed = re.sub(r'(?m)^[ \t]*•[ \t]+', '* ', fixed)
    # Fecha ** desbalanceado no final se houver quantidade ímpar
    if fixed.count('**') % 2 != 0:
        last_idx = fixed.rfind('**')
        if last_idx != -1:
            fixed = fixed[:last_idx] + fixed[last_idx + 2:]
    fixed = re.sub(r'\n{3,}', '\n\n', fixed)
    return fixed.strip()


def check_output_guardrail(query: str, answer: str, gemini_client, context: str = None, history: list = None, triage_info: dict = None) -> bool:
    """
    Valida a resposta gerada pela IA contra alucinações, vazamento de PII (LGPD), ofensas e contatos falsos.
    Aplica validação determinística de ultra-alta velocidade (0ms) local com grounding estrito de telefones e e-mails.
    Elimina falsos bypasses e assegura integridade factual dos dados municipais.
    """
    if not answer or not answer.strip():
        return True

    ans_lower = answer.lower()

    # 1. Checagem prioritária de conteúdo ofensivo/inapropriado (Zero Tolerância)
    forbidden_words = ["filho da puta", "desgraça", "vagabundo", "burro", "idiota"]
    if any(word in ans_lower for word in forbidden_words):
        print("[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): Palavra proibida detectada.", file=sys.stderr)
        return False

    # 1b. Bloqueio obrigatório de WhatsApp fictício da Ouvidoria Geral (0ms)
    if re.search(r'99824[-.\s]?5903', ans_lower):
        print("[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): Número fictício 99824-5903 detectado.", file=sys.stderr)
        return False
    for line in ans_lower.splitlines():
        if "whatsapp" in line and "ouvidoria" in line and not any(neg in line for neg in ("não possui", "nao possui", "não tem", "nao tem", "não há", "nao ha")):
            print("[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): Menção indevida de WhatsApp para a Ouvidoria.", file=sys.stderr)
            return False

    # 2. Validação de Vazamento de CPF de Terceiros (RegEx LGPD)
    cpf_pattern = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
    if re.search(cpf_pattern, answer):
        print("[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): Padrão de CPF detectado na resposta.", file=sys.stderr)
        return False

    # 3. Validação determinística de e-mails (Anti-Alucinação Factual)
    found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', answer)
    if found_emails:
        db_emails = _get_db_emails()
        ctx_norm = context.lower() if context else ""
        for email in found_emails:
            e_low = email.lower()
            if (
                e_low in ctx_norm
                or e_low in db_emails
                or "ouvidoria@duquedecaxias.rj.gov.br" in e_low
                or "colab.re" in e_low
                or e_low.endswith("@duquedecaxias.rj.gov.br")
            ):
                continue
            print(f"[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): E-mail '{email}' não fundamentado no contexto ou catálogo oficial.", file=sys.stderr)
            return False

    # 4. Validação determinística de telefones (Anti-Alucinação Factual)
    candidate_phones = extract_candidate_phones(answer)
    if candidate_phones:
        for phone in candidate_phones:
            if not is_phone_grounded(phone, context):
                print(f"[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): Telefone '{phone}' alucinado / não fundamentado no contexto oficial.", file=sys.stderr)
                return False

    # Se passou em todas as validações determinísticas de segurança e grounding, aprova instantaneamente (0ms, 0 chamadas LLM)
    return True
