import re

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

PRIVACY_TRIGGERS = [
    r"\bvizinho\b", r"\bvizinha\b",
    r"cpf\s+(?:do|de|da)\s+(?:cidadão|cidadao|reclamante|outro|terceiro|vizinho|fulano|sicrano)",
    r"protocolo\s+.*(?:vizinho|outro|terceiro|fulano|vizinha)",
    r"nome\s+(?:dele|dela|do\s+vizinho|do\s+reclamante)",
    r"reclamaç(?:ão|ões)\s+abertas?\s+sobre\s+(?:o\s+bar|o\s+estabelecimento|vizinho)"
]

COMPETENCY_TRIGGERS = [
    # Transporte estadual/federal
    r"\bmetrô\b", r"\bmetro\b", r"\btrem\b", r"\bsuper\s?via\b",
    r"\bflumitrânsito\b", r"\bdetran\b",
    # Rodovias e órgãos federais
    r"\binss\b", r"\bprev\s?social\b", r"\bprevidência\s+social\b",
    r"\baposentadoria\b", r"\bbenefício\s+(?:inss|previdência)\b",
    r"\bimposto\s+de\s+renda\b", r"\birpf\b", r"\breceita\s+federal\b",
    r"\bcpf\s+(?:do|de|da)\b", r"\bcnpj\b",
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


def check_output_guardrail(query: str, answer: str, gemini_client, context: str = None) -> bool:
    """Valida a resposta gerada pela IA contra alucinações ou vazamento de dados usando o Gemini, validando contra as fontes oficiais."""
    if len(gemini_client.api_keys) == 0:
        return True # Se estiver local/sem chaves, permite por padrão
        
    context_str = f"Contexto das fontes oficiais:\n{context}\n\n" if context else ""
    
    prompt = (
        "Você é o Agente de Blindagem e Auditoria de Respostas do Duque IA.\n"
        "Sua função é analisar se a resposta gerada para o munícipe está segura.\n\n"
        f"{context_str}"
        f"Pergunta do cidadão: \"{query}\"\n"
        f"Resposta gerada pela IA: \"{answer}\"\n\n"
        "Responda EXCLUSIVAMENTE 'PERMITIDO' ou 'BLOQUEADO' com base nestas regras ESTRITAS:\n"
        "- BLOQUEADO SOMENTE SE a resposta mencionar CPF, número de protocolo ou dados pessoais de TERCEIROS (de outras pessoas, não do próprio cidadão).\n"
        "- BLOQUEADO SOMENTE SE a resposta contiver linguagem agressiva, ofensas ou conteúdo impróprio.\n"
        "- BLOQUEADO SOMENTE SE a resposta CONTRADISSER EXPLICITAMENTE um fato presente no contexto das fontes oficiais (ex: prazo diferente, endereço diferente).\n"
        "- PERMITIDO se a resposta orientar sobre canais da Ouvidoria, Colab, telefones de contato, prazos legais gerais ou qualquer informação pública municipal.\n"
        "- PERMITIDO se o contexto estiver vazio ou parcial — a ausência de contexto NÃO é motivo de bloqueio.\n"
        "- PERMITIDO caso contrário.\n"
        "Responda apenas com a palavra PERMITIDO ou BLOQUEADO."
    )
    try:
        verdict = gemini_client.generate_response(prompt, model="gemini-3.1-flash-lite").strip().upper()
        return "PERMITIDO" in verdict
    except Exception:
        return True
