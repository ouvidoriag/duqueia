import re

DANGEROUS_PATTERNS = [
    "drop table", "delete from", "insert into",
    "ignore as instruções", "ignore todas", "ignore previous"
]

PRIVACY_TRIGGERS = [
    r"\bvizinho\b", r"\bvizinha\b",
    r"cpf\s+(?:do|de|da)\s+(?:cidadão|cidadao|reclamante|outro|terceiro|vizinho|fulano|sicrano)",
    r"protocolo\s+.*(?:vizinho|outro|terceiro|fulano|vizinha)",
    r"nome\s+(?:dele|dela|do\s+vizinho|do\s+reclamante)",
    r"reclamaç(?:ão|ões)\s+abertas?\s+sobre\s+(?:o\s+bar|o\s+estabelecimento|vizinho)"
]

COMPETENCY_TRIGGERS = [
    r"\bmetrô\b", r"\bmetro\b"
]

LEGAL_TRIGGERS = [
    r"formular\s+(?:defesa|parecer|recurso)",
    r"orientaç(?:ão|ões)\s+jurídica",
    r"argumentos?\s+contra\s+o\s+poder\s+público",
    r"como\s+a\s+administração\s+pública\s+deve\s+proceder\s+diante\s+de\s+reclamações\s+recorrentes"
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


def check_output_guardrail(query: str, answer: str, gemini_client) -> bool:
    """Valida a resposta gerada pela IA contra alucinações ou vazamento de dados usando o Gemini."""
    if len(gemini_client.api_keys) == 0:
        return True # Se estiver local/sem chaves, permite por padrão
        
    prompt = (
        "Você é o Agente de Blindagem e Auditoria de Respostas do Duque IA.\n"
        "Sua função é analisar se a resposta gerada para o munícipe está segura e livre de alucinações, "
        "erros graves ou vazamento de dados confidenciais.\n\n"
        f"Pergunta do cidadão: \"{query}\"\n"
        f"Resposta gerada pela IA: \"{answer}\"\n\n"
        "Responda EXCLUSIVAMENTE 'PERMITIDO' ou 'BLOQUEADO' com base nas regras:\n"
        "- BLOQUEADO se a resposta mencionar dados pessoais (CPF, nome completo de terceiro, etc.).\n"
        "- BLOQUEADO se a resposta tiver inventado fatos (por exemplo, mencionar Junta Militar ou Alistamento se a pergunta for sobre atendimento/conduta geral e não sobre alistamento).\n"
        "- BLOQUEADO se a resposta for agressiva ou contiver linguagem imprópria.\n"
        "- PERMITIDO caso contrário."
    )
    try:
        verdict = gemini_client.generate_response(prompt, model="gemini-3.1-flash-lite").strip().upper()
        return "PERMITIDO" in verdict
    except Exception:
        return True

