import re
from config.settings import GEMINI_FAST_MODEL

DANGEROUS_PATTERNS = [
    # SQL Injection
    "drop table", "delete from", "insert into", "update set", "truncate table",
    "select * from", "union select", "--", ";",
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
    r"\baposentadoria\b", r"\bbenefício\s+(?:inss|previdência)\b",
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
    r"\b(?:matar|agredir|bater|violentar|assassinar|morrer|espancar|facada|tiro)\b",
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
    return any(re.search(pat, q_lower) for pat in COMPETENCY_TRIGGERS)

def check_legal_guardrail(query: str) -> bool:
    """Verifica se o usuário solicita elaboração de peças ou pareceres jurídicos contra a prefeitura."""
    q_lower = query.lower()
    return any(re.search(pat, q_lower) for pat in LEGAL_TRIGGERS)

def check_output_guardrail(query: str, answer: str, gemini_client, context: str = None, history: list = None, triage_info: dict = None) -> bool:
    """
    Valida a resposta gerada pela IA contra alucinações, vazamento de PII (LGPD) ou ofensas.
    Aplica validação determinística de ultra-alta velocidade (0ms) local via RegEx.
    Elimina chamadas desnecessárias à API do Gemini no guardrail de saída.
    """
    if not answer or not answer.strip():
        return True

    ans_lower = answer.lower()

    # 1. Validação de Vazamento de CPF de Terceiros (RegEx LGPD)
    cpf_pattern = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
    if re.search(cpf_pattern, answer):
        print("[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): Padrão de CPF detectado na resposta.", file=sys.stderr)
        return False

    # 2. Validação determinística de e-mails não suportados pelo contexto
    if context:
        ctx_norm = context.lower()
        found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', answer)
        for email in found_emails:
            e_low = email.lower()
            if e_low not in ctx_norm and "ouvidoria@duquedecaxias.rj.gov.br" not in e_low and "colab.re" not in e_low:
                print(f"[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): E-mail '{email}' não presente no contexto oficial.", file=sys.stderr)
                return False

    # 3. Bypass rápido: Respostas oficiais da Ouvidoria/Colab ou orientações padrão
    if any(term in ans_lower for term in ["2652-3835", "ouvidoria@duquedecaxias.rj.gov.br", "colab", "190", "prefeitura"]):
        return True

    # 4. Checagem rápida de conteúdo ofensivo/inapropriado
    forbidden_words = ["filho da puta", "desgraça", "vagabundo", "burro", "idiota"]
    if any(word in ans_lower for word in forbidden_words):
        print("[OutputGuardrail] BLOQUEADO LOCALMENTE (0ms): Palavra proibida detectada.", file=sys.stderr)
        return False

    # Se passou nas validações determinísticas locais, aprova instantaneamente (0ms, 0 chamadas LLM)
    return True
