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
    # Match vizinho/vizinha only if query doesn't mention sound or noise
    r"\bvizinho\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))",
    r"\bvizinha\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))",
    r"cpf\s+(?:de|do|da|do\s+meu|da\s+minha|de\s+um|de\s+uma)?\s*(?:cidadão|cidadao|reclamante|outro|terceiro|vizinho|vizinha|fulano|sicrano|beltrano|wellington)",
    r"protocolo\s+.*(?:vizinho\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|vizinha\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|outro|outra|terceiro|terceira|fulano|sicrano|wellington)",
    r"nome\s+(?:dele|dela|do\s+vizinho\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|da\s+vizinha\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|do\s+reclamante|do\s+outro|da\s+outra)",
    r"reclamaç(?:ão|ões|ao)\s+abertas?\s+sobre\s+(?:o\s+bar|o\s+estabelecimento|vizinho\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|vizinha\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|outro|terceiro)"
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

HUMAN_ESCALATION_TRIGGERS = [
    r"desvi(?:o|ando)\s+verba|roub(?:o|ando)|suborn(?:o|ar|ando)|corrupç(?:ão|ao)|\bsecretário\s+roub\w+",
    r"\b(?:matar|agredir|bater|violentar|assassinar|morrer|espancar|facada|tiro)\b"
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
    """Valida a resposta gerada pela IA contra alucinações ou vazamento de dados usando o Gemini, validando contra as fontes oficiais, considerando o histórico conversacional e metadados de triagem."""
    if len(gemini_client.api_keys) == 0:
        return True # Se estiver local/sem chaves, permite por padrão

    # Bypass de Segurança: Se a resposta contiver contatos públicos oficiais da Ouvidoria, permite diretamente
    # para evitar que o modelo de guardrail bloqueie falsamente respostas sobre canais de atendimento.
    ans_lower = answer.lower()
    if any(term in ans_lower for term in ["2652-3835", "ouvidoria@duquedecaxias.rj.gov.br", "alameda esmeralda"]):
        return True
        
    context_str = f"Contexto das fontes oficiais:\n{context}\n\n" if context else ""
    
    # Formata histórico conversacional
    history_str = ""
    if history:
        history_str = "Histórico conversacional recente:\n" + "\n".join(history) + "\n\n"
        
    # Formata informações de triagem
    triage_str = ""
    if triage_info:
        intent = triage_info.get("intent", "N/A")
        rewritten = triage_info.get("rewritten_query", "")
        triage_str = f"Metadados de Triagem:\n- Intenção: {intent}\n"
        if rewritten and rewritten != query:
            triage_str += f"- Pergunta Reescrevida: {rewritten}\n"
        triage_str += "\n"
    
    prompt = (
        "Você é o Agente de Blindagem e Auditoria de Respostas do Duque IA.\n"
        "Sua função é analisar se a resposta gerada para o munícipe está segura.\n\n"
        f"{history_str}"
        f"{triage_str}"
        f"{context_str}"
        f"Pergunta atual do cidadão: \"{query}\"\n"
        f"Resposta gerada pela IA: \"{answer}\"\n\n"
        "Responda EXCLUSIVAMENTE com a palavra 'PERMITIDO' ou 'BLOQUEADO' com base nestas regras ESTRITAS:\n"
        "- BLOQUEADO SOMENTE SE a resposta mencionar CPF, número de protocolo ou dados pessoais de TERCEIROS (de outras pessoas, não do próprio cidadão).\n"
        "- BLOQUEADO SOMENTE SE a resposta contiver linguagem agressiva, ofensas ou conteúdo impróprio.\n"
        "- BLOQUEADO SOMENTE SE a resposta CONTRADISSER EXPLICITAMENTE um fato presente no contexto das fontes oficiais (ex: prazo diferente cadastrado, endereço diferente cadastrado).\n"
        "- A ausência de menção direta a termos na fonte oficial NÃO é contradição. Perguntas de continuação (ex: 'qualquer pessoa pode usar?', 'quem tem direito?', 'qual o endereço?') sobre programas públicos ou transporte (como Tarifa Zero) ou serviços municipais devem ser sempre PERMITIDAS e nunca bloqueadas por falta de termos no contexto atual.\n"
        "- PERMITIDO para perguntas de continuação que se referem a tópicos explicados no histórico conversacional ou na pergunta reescrita (use o histórico conversacional para entender a referência e a pergunta reescrita para validar o contexto real da consulta).\n"
        "- PERMITIDO se a resposta orientar sobre canais da Ouvidoria, Colab, telefones de contato, prazos legais gerais, tarifas, transporte ou qualquer informação pública municipal.\n"
        "- PERMITIDO se a resposta orientar o cidadão a ligar para a Polícia (190) em caso de barulho de vizinho, festa particular ou perturbação do sossego em residência privada.\n"
        "- PERMITIDO se o contexto das fontes oficiais estiver vazio ou parcial — a ausência de contexto NÃO é motivo de bloqueio.\n"
        "- Se o assunto ou tema das fontes oficiais é sobre serviços municipais ou utilidade pública, reduza drasticamente a sensibilidade de contradição para evitar falsos positivos.\n"
        "- PERMITIDO caso contrário.\n"
        "Responda apenas com a palavra PERMITIDO ou BLOQUEADO."
    )
    try:
        verdict = gemini_client.generate_response(
            prompt, 
            model=GEMINI_FAST_MODEL,
            temperature=0.0,
            max_output_tokens=10
        ).strip().upper()
        return "PERMITIDO" in verdict
    except Exception:
        return True
