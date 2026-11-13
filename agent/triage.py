import hashlib
import json
import re
import os
import sys
from utils.db_client import get_db_connection, query_one, execute_db
from storage import storage_manager
from config.settings import GEMINI_FAST_MODEL
from agent.guardrails import (
    PROGRAMMING_TRIGGERS,
    PRIVACY_TRIGGERS,
    COMPETENCY_TRIGGERS,
    LEGAL_TRIGGERS,
    HUMAN_ESCALATION_TRIGGERS
)

# Modelo e versão do prompt para controle de cache
MODEL_VERSION = GEMINI_FAST_MODEL
PROMPT_VERSION = "triage_v2.1"

# Lista de intenções válidas e permitidas
ALLOWED_INTENTS = {
    "SAUDACAO",
    "IDENTIDADE",
    "LGPD",
    "JURIDICO",
    "FORA_COMPETENCIA",
    "AMBIGUO_LUZ",
    "AMBIGUO_LAMPADA",
    "AMBIGUO_BARULHO",
    "AMBIGUO_LOCALIZACAO",
    "DEFESA_CIVIL_EMERGENCIA",
    "SEGURANCA_PUBLICA_EMERGENCIA",
    "RESIDENCIAL",
    "OUVIDORIA_MANIFESTACAO",
    "ESCALONAMENTO_HUMANO",
    "PROGRAMACAO",
    "CONVERSA",
    "RAG_GERAL",
    "POSSIVEL_DENUNCIA",
    "AUTORIDADE_PUBLICA",
    "MEMORIA_CONVERSACIONAL",
    "CLARIFICACAO_RESPOSTA",
    "AI_META_INFO"
}

# --------------------------------------------------------------------------
# FAST GATE / SECURITY POLICIES
# --------------------------------------------------------------------------
FAST_SECURITY_PATTERNS = []

for pat in HUMAN_ESCALATION_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "ESCALONAMENTO_HUMANO", "Assunto sensível ou denúncia encaminhada para escalonamento humano."))

for pat in PROGRAMMING_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "PROGRAMACAO", "Solicitação de programação bloqueada localmente."))

for pat in PRIVACY_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "LGPD", "Solicitação de dados/privacidade de terceiro bloqueada localmente."))

for pat in COMPETENCY_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "FORA_COMPETENCIA", "Assunto fora da competência municipal bloqueado localmente."))

for pat in LEGAL_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "JURIDICO", "Solicitação jurídica bloqueada localmente."))


# Detecta queries de barulho/som onde o cidadão NÃO especifica se a origem é pública/comercial ou privada.
# Deve ficar ABAIXO dos padrões de segurança (LGPD/ESCALONAMENTO) que têm prioridade.
# Dispara AMBIGUO_BARULHO com needs_clarification=True para acionar o Agente Coletor.
AMBIGUITY_FAST_PATTERNS = [
    # Frases de som alto/música/barulho onde é necessário esclarecer se vem de residência particular (190) ou comércio/espaço público (Prefeitura/Colab)
    (
        r"\b(?:som\s+alto|música\s+alta|musica\s+alta|barulho\s+(?:de\s+)?som|vizinho\s+(?:com\s+|tá\s+com\s+|ta\s+com\s+|está\s+com\s+)?som\s+alto)\b",
        "AMBIGUO_BARULHO",
        "Reclamação de som alto/barulho necessitando esclarecimento de origem (residência particular ou estabelecimento/espaço público)."
    ),
    # Frases ambíguas de barulho sem menção explícita de local público ou privado
    (
        r"(?:tem|tá|ta|tem|há|ha)\s+(?:um|uma|muito|um)\s+(?:barulho|som|algazarra|zoeira|bagunça|bagunceira)\b"
        r"(?!.*(?:rua|praça|largo|parque|show|evento|bar\b|boate))",
        "AMBIGUO_BARULHO",
        "Reclamação de barulho sem origem explícita detectada — aguardando esclarecimento."
    ),
    # 'barulho insuportavel / excessivo / muito alto' sem local claro
    (
        r"barulho\s+(?:insuportáve[l]?|insuportave[l]?|excess[i]?vo|muito\s+alto|absurdo|horríve[l]?|horrivel)"
        r"(?!.*(?:rua|praça|largo|parque|show|evento|bar\b|boate))",
        "AMBIGUO_BARULHO",
        "Reclamação de barulho intenso sem origem explícita — aguardando esclarecimento."
    ),
    # Solicitação de unidade/serviço mais próximo sem menção de bairro ou rua
    (
        r"\b(?:qual|onde\s+fica|qual\s+é|onde\s+tem)\s+(?:a|o)?\s*(?:creche|posto\s+de\s+saúde|posto\s+de\s+saude|escola|ubs|cras)\s+(?:mais\s+próxim[ao]|mais\s+perto)\b(?!.*(?:bairro|rua|centro|xerém|xerem|saracuruna|imparti|pantanal|manoa|25\s+de\s+agosto|figueira))",
        "AMBIGUO_LOCALIZACAO",
        "Solicitação de proximidade de unidade sem informação de bairro ou rua."
    )
]

DEFESA_CIVIL_FAST_PATTERNS = [
    (r"\b(?:desabando|desabamento|casa\s+(?:está\s+)?desabando|casa\s+(?:está\s+)?caindo|risco\s+de\s+desabamento|deslizamento|barranco\s+caindo|alagamento\s+grave)\b", "DEFESA_CIVIL_EMERGENCIA", "Ocorrência grave de emergência de Defesa Civil detectada localmente.")
]

SEGURANCA_PUBLICA_FAST_PATTERNS = [
    (r"\b(?:tráfico|trafico|tráfico\s+de\s+drogas|trafico\s+de\s+drogas|boca\s+de\s+fumo|tiroteio)\b", "SEGURANCA_PUBLICA_EMERGENCIA", "Ocorrência de segurança pública / crime detectada localmente.")
]

POSSIVEL_DENUNCIA_FAST_PATTERNS = [
    (r"\b(?:me\s+(?:\w+\s+)?xingou|me\s+(?:\w+\s+)?xingaram|xingou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de ofensa ou xingamento sofrido."),
    (r"\b(?:me\s+(?:\w+\s+)?tratou\s+(?:\w+\s+)?mal|me\s+(?:\w+\s+)?trataram\s+(?:\w+\s+)?mal|fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?tratado|fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?tratada|fui\s+(?:\w+\s+)?maltratad[ao]|me\s+(?:\w+\s+)?maltrat(?:ou|aram))\b", "POSSIVEL_DENUNCIA", "Relato de mau tratamento sofrido."),
    (r"\b(?:foi\s+(?:\w+\s+)?grosseiro|foi\s+(?:\w+\s+)?grosseira|foram\s+(?:\w+\s+)?grosseiros)\b", "POSSIVEL_DENUNCIA", "Relato de grosseria sofrida."),
    (r"\b(?:me\s+(?:\w+\s+)?ofendeu|me\s+(?:\w+\s+)?ofenderam|ofendeu\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de ofensa sofrida."),
    (r"\b(?:foi\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?educado|foi\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?educada|foram\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?educados)\b", "POSSIVEL_DENUNCIA", "Relato de atitude mal educada."),
    (r"\b(?:me\s+(?:\w+\s+)?humilhou|me\s+(?:\w+\s+)?humilharam|humilhou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de humilhação sofrida."),
    (r"\b(?:me\s+(?:\w+\s+)?ameaçou|me\s+(?:\w+\s+)?ameaçaram|ameaçou\s+me|me\s+(?:\w+\s+)?ameacou|me\s+(?:\w+\s+)?ameacaram|ameacou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de ameaça sofrida."),
    (r"\b(?:me\s+(?:\w+\s+)?destratou|me\s+(?:\w+\s+)?destrataram|destratou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de desrespeito sofrido."),
    (r"\b(?:fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?atendido|fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?atendida|mau\s+(?:\w+\s+)?atendimento|atendimento\s+(?:\w+\s+)?ruim)\b", "POSSIVEL_DENUNCIA", "Relato de atendimento inadequado."),
    (r"\b(?:fui\s+(?:\w+\s+)?vítima|fui\s+(?:\w+\s+)?vitima)\b", "POSSIVEL_DENUNCIA", "Relato de ter sido vítima de algo."),
    (r"\b(?:aconteceu\s+(?:\w+\s+)?comigo)\b", "POSSIVEL_DENUNCIA", "Relato pessoal de ocorrido."),
    (r"\b(?:pediu\s+dinheiro|pediram\s+dinheiro|cobrou\s+propina|pediu\s+propina|cobrando\s+propina|suborno|concussão|concussao)\b", "POSSIVEL_DENUNCIA", "Relato de cobrança indevida ou corrupção de agente público."),
    (r"\b(?:praticou\s+(?:uma\s+)?irregularidade|cometeu\s+(?:uma\s+)?irregularidade|desvio\s+de\s+conduta)\b", "POSSIVEL_DENUNCIA", "Relato de conduta irregular ou infração disciplinar de agente.")
]

MEMORIA_CONVERSACIONAL_FAST_PATTERNS = [
    (r"\b(?:qual\s+(?:foi|era)|sabe\s+qual\s+foi|lembra\s+qual\s+foi|o\s+que\s+(?:eu\s+)?perguntei)\s+(?:a\s+|minha\s+)?(?:primeira|1ª|1a)\s+(?:pergunta|dúvida|duvida|coisa)\b", "MEMORIA_CONVERSACIONAL", "Consulta sobre a primeira pergunta da sessão."),
    (r"\b(?:qual\s+foi\s+a\s+primeira|minha\s+primeira\s+pergunta)\b", "MEMORIA_CONVERSACIONAL", "Consulta sobre a primeira pergunta da sessão."),
    (r"\b(?:o\s+que\s+(?:você|vc|voce)\s+(?:me\s+)?respondeu\s+(?:antes|no\s+turno\s+anterior|anteriormente)|qual\s+foi\s+(?:a\s+)?última\s+resposta|qual\s+foi\s+(?:a\s+)?ultima\s+resposta)\b", "MEMORIA_CONVERSACIONAL", "Consulta sobre a resposta anterior da sessão."),
    (r"\b(?:repita\s+(?:a\s+)?(?:primeira|segunda|terceira|quarta|última|ultima|\d+ª|\d+a)\s+(?:resposta|mensagem))\b", "MEMORIA_CONVERSACIONAL", "Solicitação de repetição de turno específico."),
    (r"\b(?:sobre\s+o\s+que\s+(?:nós\s+)?(?:estávamos|estamos|a\s+gente\s+estava)\s+(?:conversando|falando)|quais\s+perguntas\s+(?:eu\s+)?já\s+fiz)\b", "MEMORIA_CONVERSACIONAL", "Consulta sobre o histórico geral de assuntos da sessão.")
]

CLARIFICACAO_RESPOSTA_FAST_PATTERNS = [
    (r"\b(?:não\s+entendi|nao\s+entendi|não\s+compreendi|nao\s+compreendi|não\s+ficou\s+claro|nao\s+ficou\s+claro|ficou\s+confuso|muito\s+confuso|não\s+foi\s+isso\s+que\s+(?:eu\s+)?perguntei|nao\s+foi\s+isso\s+que\s+(?:eu\s+)?perguntei|explique\s+melhor|explica\s+melhor|explica\s+de\s+novo|explique\s+de\s+novo|pode\s+explicar\s+melhor|pode\s+explicar\s+de\s+novo|desenha\s+pra\s+mim|simplifica|não\s+ajudou|nao\s+ajudou)\b", "CLARIFICACAO_RESPOSTA", "Pedido de esclarecimento ou simplificação da resposta anterior."),
    (r"\b(?:vai\s+à\s+merda|vai\s+a\s+merda|vai\s+se\s+foder|vai\s+se\s+ferrar|vai\s+tomar\s+no|robô\s+burro|robo\s+burro|inútil|inutil|assistente\s+burro|péssimo\s+assistente)\b", "CLARIFICACAO_RESPOSTA", "Frustração ou insatisfação com a comunicação do assistente virtual.")
]

AI_META_INFO_FAST_PATTERNS = [
    (r"\b(?:invent\w*)\s+(?:.*?)(?:protocol|telefon|informaç|dado|contato|encaminha|respost)", "AI_META_INFO", "Questionamento sobre não-invenção de dados e protocolos pela IA."),
    (r"\b(?:a\s+ia|duque\s+ia|voc[eê]|voc[eê]s)\s+(?:invent\w*|mente|mentir|alucin\w*|engan\w*|fariam\s+isso)", "AI_META_INFO", "Questionamento sobre veracidade e limites da IA."),
    (r"\b(?:para|pra)\s+(?:\w+\s+)?(?:me\s+)?agradar\b", "AI_META_INFO", "Questionamento sobre invenção de respostas para agradar o munícipe."),
    (r"\b(?:posso\s+confiar|confi[aá]vel|como\s+posso\s+ter\s+certeza|s[aã]o\s+verdadeiras?|informaç[õo]es\s+verdadeiras?)\b", "AI_META_INFO", "Pergunta sobre confiabilidade e veracidade da IA."),
    (r"\b(?:como\s+(?:você|voce|a\s+ia|duque\s+ia)\s+funciona|de\s+onde\s+v[eê]m\s+(?:suas|as)\s+informaç[õo]es)\b", "AI_META_INFO", "Pergunta sobre funcionamento e fontes da IA.")
]

AUTORIDADE_PUBLICA_FAST_PATTERNS = [
    (r"\b(?:quem\s+(?:é|e)\s+o\s+prefeito|qual\s+(?:é\s+)?o\s+prefeito|prefeito\s+municipal)\b", "AUTORIDADE_PUBLICA", "Busca direta pelo prefeito."),
    (r"\b(?:quem\s+(?:é|e)\s+(?:o|a)\s+vice|vice-prefeita?|vice\s+prefeita?)\b", "AUTORIDADE_PUBLICA", "Busca pelo vice-prefeito."),
    (r"\b(?:(?:qual\s+(?:é\s+)?(?:o\s+)?nome\s+d[oa]|quem\s+(?:é|e)\s+[oa]|qual\s+(?:é\s+)?[oa])\s+secret[áa]ri[oa]|secret[á]ri[oa]\s+d[ea]|secretario\s+d[ea]|titular\s+d[ea]\s+secretaria)\b", "AUTORIDADE_PUBLICA", "Busca por secretário municipal."),
    (r"\b(?:quem\s+dirige|quem\s+administra|quem\s+comanda|quem\s+ocupa\s+o\s+cargo|responsável\s+pel[ao]|responsavel\s+pel[ao])\s+(?:secretaria|órgão|orgao|pasta|prefeitura)\b", "AUTORIDADE_PUBLICA", "Busca pelo responsável de secretaria/órgão."),
    (r"\b(?:(?:qual\s+(?:é\s+)?(?:o\s+)?nome\s+d[oa]|quem\s+(?:é|e)\s+[oa]|qual\s+(?:é\s+)?[oa])\s+(?:ouvidor|procurador|controlador|presidente\s+d[ao]|subprefeito)|presidente\s+d[ao]\s+(?:fundec|ipmdc)|quem\s+preside\s+(?:a\s+fundec|o\s+ipmdc))\b", "AUTORIDADE_PUBLICA", "Busca por autoridades de controle, autarquias ou fundações.")
]

RAG_GERAL_FAST_PATTERNS = [
    # Zeladoria Urbana, Obras, Limpeza e Iluminação
    (r"\b(?:tapa\s*buraco|buracos?|asfalto|pavimentação|pavimentacao|bueiro|drenagem|boca\s+de\s+lobo)\b", "RAG_GERAL", "Serviço de obras e pavimentação detectado localmente."),
    (r"\b(?:limpeza|capina|roçada|rocada|roçagem|entulho|lixo|varrição|varricao|mato)\b", "RAG_GERAL", "Serviço de limpeza e conservação urbana detectado localmente."),
    (r"\b(?:iluminação|iluminacao|lâmpadas?|lampadas?|postes?|luzes?\s+(?:da\s+rua|pública|publica)?)\b", "RAG_GERAL", "Serviço de iluminação pública detectado localmente."),
    
    # Tributos, Finanças e Certidões
    (r"\b(?:iptu|alvará|alvara|iss|2ª\s*via|segunda\s+via|carnê|carne|certidão|certidao|imposto|taxa)\b", "RAG_GERAL", "Serviço de tributos e receitas municipais detectado localmente."),
    
    # Assistência Social, Saúde, Educação e Cursos
    (r"\b(?:cras|creas|bolsa\s+família|bolsa\s+familia|cadúnico|cadunico|assistência\s+social|assistencia\s+social)\b", "RAG_GERAL", "Serviço de assistência social detectado localmente."),
    (r"\b(?:hospital|upa|posto\s+de\s+saúde|posto\s+de\s+saude|ubs|vacina|exame|consulta|marcar|médico|medico|remédio|remedio|farmácia|farmacia)\b", "RAG_GERAL", "Serviço de saúde municipal detectado localmente."),
    (r"\b(?:escola|creche|matrícula|matricula|vaga|educação|educacao|fundec|curso|cursos)\b", "RAG_GERAL", "Serviço de educação ou cursos detectado localmente."),
    
    # Transportes, Mobilidade e Canais da Prefeitura
    (r"\b(?:ônibus|onibus|transporte|tarifa\s+zero|passe\s+livre|estacionamento|sinal|semáforo|semaforo)\b", "RAG_GERAL", "Serviço de transportes e mobilidade detectado localmente."),
    (r"\b(?:multas?|recorrer\s+de\s+multa|recurso\s+de\s+multa|jari|defesa\s+prévia|defesa\s+previa|autuação|autuacao|processo\s+de\s+multa)\b", "RAG_GERAL", "Consulta sobre multas e recursos de trânsito detectada localmente."),
    (r"\b(?:veterin[aá]ri[ao]s?|castram[oó]ve[li]s?|cachorros?|cães|cao|gatos?|pets?|animais|animal|zoonoses?|socorro\s+animal|hmv)\b", "RAG_GERAL", "Serviço de saúde animal e hospital veterinário detectado localmente."),
    (r"\b(?:ouvidoria|colab|telefone|endereço|endereco|contato|horário|horario|secretaria|prefeitura)\b", "RAG_GERAL", "Consulta informativa de canais/secretarias detectada localmente.")
]

# Palavras-chave de mudança de assunto e tópicos independentes para blindagem do Fast Gate
INTENT_CHANGE_SIGNALS = [
    "esquece", "esqueça", "cancela", "deixa pra lá", "deixa para la",
    "mudei de ideia", "outro assunto", "outra coisa", "na verdade, não",
    "não quero mais", "mudando de assunto", "na verdade"
]

INDEPENDENT_TOPIC_KEYWORDS = [
    "horário", "horario", "ambulante", "higiene", "alvará", "alvara",
    "abrir empresa", "abrir um", "abrir uma", "endereço", "endereco",
    "onde fica", "onde tem", "trabalho", "iptu", "segunda via", "2ª via",
    "iluminação", "iluminacao", "lixo", "buraco", "asfalto", "bueiro",
    "vacina", "matrícula", "matricula", "remédio", "remedio", "hospital",
    "veterinário", "veterinario", "cachorro", "gato", "pet", "animal", "hmv",
    "upa", "creche", "escola", "inventa", "inventaria", "alucina",
    "confiável", "confiavel", "como você funciona", "como voce funciona"
]

INDEPENDENT_QUESTION_PREFIXES = [
    "quero saber", "gostaria de saber", "como faço para", "como faco para",
    "como posso", "onde posso", "preciso saber", "preciso do", "qual o horário",
    "qual o horario", "tenho uma reclamação sobre o comércio ambulante",
    "reclamação sobre o comércio ambulante", "quero denunciar um comércio funcionando irregularmente",
    "o estabelecimento onde trabalho", "quero abrir uma reclamação contra um estabelecimento por falta de higiene",
    "você inventaria", "voce inventaria", "você inventa", "voce inventa",
    "você mente", "voce mente", "você é confiável", "voce e confiavel",
    "posso confiar", "como você funciona", "como voce funciona"
]

def check_fast_gate(query: str, history: list = None) -> dict | None:
    """Valida a query usando regras locais de baixíssima latência (0ms)."""
    query_lower = query.lower().strip()
    
    # Validações básicas de tamanho
    if not query_lower:
        return {
            "intent": "SAUDACAO",
            "confidence": 1.0,
            "needs_clarification": False,
            "reason": "Query vazia tratada como saudação padrão.",
            "source": "FAST_GATE"
        }
    if len(query_lower) < 3:
        return {
            "intent": "SAUDACAO",
            "confidence": 1.0,
            "needs_clarification": False,
            "reason": "Query extremamente curta tratada como saudação padrão.",
            "source": "FAST_GATE"
        }
    if re.match(r"^(?:ol[áa]+|oi+|oie+|bom\s+dia|boa\s+tarde|boa\s+noite|tudo\s+bem\??|td\s+bem\??|e\s*a[íi]+|opa+|salve|hello|hi)(?:\s+(?:duque|ia|tudo\s+bem\??))?[!.,\s?]*$", query_lower):
        return {
            "intent": "SAUDACAO",
            "confidence": 1.0,
            "needs_clarification": False,
            "reason": "Saudação inicial detectada no Fast Gate.",
            "source": "FAST_GATE"
        }

    # 0º Prioridade Máxima: Integridade e Transparência da IA (não-invenção de dados/protocolos)
    for regex, intent, reason in AI_META_INFO_FAST_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }

    # Desambiguação instantânea multi-turno (0ms) baseada no histórico recente
    if history:
        is_intent_change = any(sig in query_lower for sig in INTENT_CHANGE_SIGNALS)
        last_assistant_turn = ""
        for turn in reversed(history):
            if "DUQUE IA:" in turn or "DUQUE" in turn or "assistente:" in turn.lower():
                last_assistant_turn = turn.lower()
                break
        if not last_assistant_turn and len(history) > 0:
            last_assistant_turn = history[-1].lower()

        # Retomada explícita de manifestação pausada (ex: "Quero voltar ao buraco", "Quero voltar à reclamação")
        if re.search(r"\b(?:quero\s+)?voltar\s+(?:ao|à|a|para\s+o|para\s+a)\s+(?:buraco|reclamação|reclamacao|manifestação|manifestacao|atendimento|denúncia|denuncia|assunto\s+anterior)\b", query_lower):
            return {
                "intent": "OUVIDORIA_MANIFESTACAO",
                "tipo_manifestacao": "reclamacao",
                "confidence": 0.95,
                "needs_clarification": False,
                "reason": "Retomada explícita de manifestação/coleta anterior.",
                "source": "FAST_GATE"
            }

        # Continuidade prioritária de Coleta / Manifestação Ativa (APENAS quando o turno anterior foi uma pergunta explícita de coleta)
        is_explicit_collection_prompt = any(w in last_assistant_turn for w in [
            "qual problema ou assunto você deseja relatar",
            "qual é o problema na rua que você deseja relatar",
            "qual é o problema que você deseja relatar",
            "qual é a rua e o bairro",
            "qual é o nome da rua",
            "qual é o assunto da reclamação",
            "qual é o assunto da denúncia",
            "protocolo diretamente no sistema",
            "deixar a categoria e o texto prontos",
        ])
        is_operational_q = any(p in query_lower for p in [
            "você que vai abrir", "voce que vai abrir", "você vai abrir", "voce vai abrir",
            "você abre", "voce abre", "você registra", "voce registra", "abre pra mim",
            "você consegue abrir", "voce consegue abrir", "consegue abrir por mim",
            "mas aí eu marco", "mas ai eu marco", "eu marco o quê", "eu marco o que",
            "marco o quê", "marco o que", "qual categoria", "qual tema"
        ])
        is_conversational_or_meta = any(p in query_lower for p in [
            "conversar", "conversa", "bate-papo", "bate papo",
            "você faz", "voce faz", "o que você", "o que voce", "oq você", "oq voce",
            "quem é você", "quem e voce", "deixa isso", "esquece", "outro assunto", "mudar de assunto",
            "na verdade"
        ])
        starts_indep_q = any(query_lower.startswith(p) for p in INDEPENDENT_QUESTION_PREFIXES)
        if (
            not is_intent_change
            and not is_conversational_or_meta
            and is_explicit_collection_prompt
            and (is_operational_q or (len(query_lower.split()) <= 4 and "?" not in query_lower and not starts_indep_q))
        ):
            return {
                "intent": "OUVIDORIA_MANIFESTACAO",
                "tipo_manifestacao": "reclamacao",
                "confidence": 0.95,
                "needs_clarification": False,
                "reason": "Continuação de fluxo ativo de coleta/orientação de manifestação.",
                "source": "FAST_GATE"
            }

        # Se o usuário estiver explicitamente mudando de assunto ou fazendo uma pergunta independente completa,
        # NÃO interceptar no Fast Gate de desambiguação multi-turno. Deixe fluir para triagem/resolução de entidade.
        is_independent_query = (
            any(k in query_lower for k in INDEPENDENT_TOPIC_KEYWORDS) or
            starts_indep_q
        )

        if not is_intent_change and not is_independent_query:

            # Desambiguação de Barulho / Som Alto
            is_noise_context = any(w in last_assistant_turn for w in [
                "origem do ruído", "origem do barulho", "som alto", "ruído", "ruido",
                "residência particular", "residencia particular", "190", "comércio, obra",
                "estabelecimento comercial", "ambiguo_barulho", "poluição sonora",
                "barulho vem de", "barulho vem", "ruído vem", "som vem", "barulho",
                "residência ou de um comércio", "residencia ou de um comercio",
                "residência ou comércio", "residencia ou comercio"
            ])

            if is_noise_context:
                # Caso A: Residencial (Polícia Militar 190)
                is_residential = (
                    any(w in query_lower for w in [
                        "casa", "residencia", "residência", "apartamento", "vizinho", "vizinha",
                        "particular", "residencial", "casa ao lado", "na casa do vizinho",
                        "casa de vizinho", "família", "familia", "meu vizinho"
                    ]) or
                    query_lower in ["não", "nao", "não é comércio", "nao é comercio", "não, é na minha casa", "não, é casa", "não, casa"]
                )

                # Caso B: Comércio / Estabelecimento (Colab / Ouvidoria - Ordem Pública)
                is_commercial = (
                    any(w in query_lower for w in [
                        "comercial", "comércio", "comercio", "comérciu", "comerciu", "estabelecimento",
                        "bar", "loja", "restaurante", "boate", "mercado", "supermercado", "salão", "salao",
                        "casa de festa", "casa de festas", "lanchonete", "padaria", "quiosque", "boteco",
                        "oficina", "igreja", "templo", "empresa", "barulho do bar", "som alto do bar",
                        "bar tá com som", "bar ta com som", "bar da esquina", "comercio ta com",
                        "vizinho é um bar", "vizinho e um bar"
                    ]) or
                    query_lower in ["sim", "sim, é um bar", "sim é um bar", "sim, comercial", "sim comercial", "é comercial", "e comercial"]
                )

                # Caso C: Via Pública / Veículos / Paredão / Eventos (Colab / Ordem Pública)
                is_public_or_vehicle = any(w in query_lower for w in [
                    "rua", "na rua", "praça", "praca", "calçada", "calcada", "via pública", "via publica",
                    "carro", "carro de som", "carro com som", "veículo", "veiculo", "automotivo",
                    "som automotivo", "paredão", "paredao", "evento", "show", "evento na rua"
                ])

                if is_residential and not is_commercial:
                    return {
                        "intent": "RESIDENCIAL",
                        "confidence": 1.0,
                        "needs_clarification": False,
                        "reason": "Desambiguação rápida de som alto: origem confirmada em residência particular (Polícia 190).",
                        "rewritten_query": f"Perturbação do sossego por som alto em residência particular ({query}).",
                        "source": "FAST_GATE"
                    }
                elif is_commercial:
                    return {
                        "intent": "OUVIDORIA_MANIFESTACAO",
                        "tipo_manifestacao": "reclamacao",
                        "sub_intent": "poluicao_sonora_comercial",
                        "confidence": 1.0,
                        "needs_clarification": False,
                        "reason": "Desambiguação rápida de som alto: origem confirmada em estabelecimento comercial (Colab Ordem Pública).",
                        "rewritten_query": f"Reclamação de poluição sonora e ruído em estabelecimento comercial ou bar ({query}).",
                        "source": "FAST_GATE"
                    }
                elif is_public_or_vehicle:
                    subtype = "veiculo" if any(w in query_lower for w in ["carro", "veículo", "veiculo", "paredão", "paredao", "automotivo"]) else "via_publica"
                    return {
                        "intent": "OUVIDORIA_MANIFESTACAO",
                        "tipo_manifestacao": "reclamacao",
                        "sub_intent": f"poluicao_sonora_{subtype}",
                        "confidence": 1.0,
                        "needs_clarification": False,
                        "reason": f"Desambiguação rápida de som alto: origem em {subtype.replace('_', ' ')} (Colab Ordem Pública).",
                        "rewritten_query": f"Reclamação de poluição sonora em via pública / som automotivo ({query}).",
                        "source": "FAST_GATE"
                    }

            # Desambiguação de Iluminação Pública vs Residencial
            is_light_context = any(w in last_assistant_turn for w in [
                "falta de energia elétrica dentro da sua residência", "iluminação pública (como um poste",
                "poste ou lâmpada", "ambiguo_luz", "poste apagado", "lâmpada queimada"
            ])
            if is_light_context:
                if any(w in query_lower for w in ["poste", "rua", "fora", "apagado", "apagada", "quebrada", "pública", "publica", "na rua"]):
                    return {
                        "intent": "RAG_GERAL",
                        "confidence": 1.0,
                        "needs_clarification": False,
                        "reason": "Desambiguação rápida de iluminação: poste de iluminação pública na rua.",
                        "rewritten_query": f"Solicitação de troca ou manutenção de lâmpada em poste de rua ({query}).",
                        "source": "FAST_GATE"
                    }
                elif any(w in query_lower for w in ["casa", "minha casa", "dentro", "light", "relógio", "relogio", "residência", "residencia"]):
                    return {
                        "intent": "RESIDENCIAL",
                        "confidence": 1.0,
                        "needs_clarification": False,
                        "reason": "Desambiguação rápida de iluminação: falta de energia dentro de casa (Light).",
                        "rewritten_query": f"Falta de luz dentro de residência particular ({query}).",
                        "source": "FAST_GATE"
                    }
        
    # 1º: Matcher de políticas de segurança / escopo (máxima prioridade)
    for regex, intent, reason in FAST_SECURITY_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }

    # 1º A: Ocorrências de Emergência de Defesa Civil
    for regex, intent, reason in DEFESA_CIVIL_FAST_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }

    # 1º A2: Ocorrências de Crimes / Segurança Pública de Emergência
    for regex, intent, reason in SEGURANCA_PUBLICA_FAST_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }

    # 1º B1: Memória Conversacional (meta-perguntas sobre perguntas e respostas anteriores)
    for regex, intent, reason in MEMORIA_CONVERSACIONAL_FAST_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }

    # 1º B2: Pedidos de Clarificação Didática e Insatisfação com a Comunicação do Assistente
    for regex, intent, reason in CLARIFICACAO_RESPOSTA_FAST_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }

    # 1º B3: Relatos de ofensas/xingamentos/mau atendimento por agente/servidor (alta prioridade, antes de conversa casual)
    is_private_or_commercial = any(w in query_lower for w in [
        "comércio", "comercio", "loja", "bar", "restaurante", "lanchonete", "padaria",
        "mercado", "supermercado", "banco", "empresa", "vizinho", "vizinha", "motorista de ônibus",
        "motorista de van", "estabelecimento"
    ])
    has_municipal_agent = any(w in query_lower for w in [
        "servidor", "funcionário", "funcionario", "atendente da prefeitura", "prefeitura",
        "guarda municipal", "guarda", "fiscal", "secretaria", "posto de saúde", "posto de saude",
        "upa", "hospital municipal", "escola municipal", "creche municipal"
    ])
    is_bot_frustration = any(w in query_lower for w in [
        "resposta", "robô", "robo", "assistente", "você é", "voce e", "não entendi", "nao entendi",
        "vai à merda", "vai a merda", "vai se ferrar", "vai se foder", "inútil", "inutil"
    ])
    # Se mencionar entidade comercial privada ou frustração com a IA sem menção de servidor municipal, não é POSSIVEL_DENUNCIA funcional
    if not (is_private_or_commercial and not has_municipal_agent) and not is_bot_frustration:
        for regex, intent, reason in POSSIVEL_DENUNCIA_FAST_PATTERNS:
            if re.search(regex, query_lower):
                return {
                    "intent": intent,
                    "confidence": 1.0,
                    "needs_clarification": False,
                    "reason": reason,
                    "source": "FAST_GATE"
                }

    # 1º C: Perguntas de autoridades (alta prioridade, antes de conversa casual)
    for regex, intent, reason in AUTORIDADE_PUBLICA_FAST_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }

    # 1º D: Serviços Municipais Diretos (RAG_GERAL instantâneo em 0ms sem acionar Gemini)
    for regex, intent, reason in RAG_GERAL_FAST_PATTERNS:
        if re.search(regex, query_lower):
            return {
                "intent": intent,
                "confidence": 1.0,
                "needs_clarification": False,
                "reason": reason,
                "source": "FAST_GATE"
            }
    
    # 2º: Detector de ambiguidade de barulho (sem origem explícita)
    for regex, intent, reason in AMBIGUITY_FAST_PATTERNS:
        if re.search(regex, query_lower, re.IGNORECASE):
            return {
                "intent": intent,
                "confidence": 0.90,
                "needs_clarification": True,
                "reason": reason,
                "source": "FAST_GATE"
            }
            
    return None

# --------------------------------------------------------------------------
# PERSISTENT CACHE SQLITE
# --------------------------------------------------------------------------
def init_cache_db(db_path: str):
    """Inicializa a tabela de cache de triagem no SQLite."""
    execute_db(db_path, """
        CREATE TABLE IF NOT EXISTS triage_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT NOT NULL,
            intent TEXT NOT NULL,
            confidence REAL NOT NULL,
            needs_clarification INTEGER NOT NULL,
            reason TEXT,
            model_version TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(query_hash, prompt_version)
        )
    """)

_L1_RAM_TRIAGE_CACHE: dict = {}

def get_query_hash(query: str) -> str:
    """Gera um hash md5 único a partir da query normalizada."""
    normalized = query.lower().strip()
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def get_cached_triage(db_path: str, query: str) -> dict | None:
    """Busca o resultado da triagem no cache L1 RAM ou SQLite."""
    query_hash = get_query_hash(query)
    if query_hash in _L1_RAM_TRIAGE_CACHE:
        return _L1_RAM_TRIAGE_CACHE[query_hash]
    try:
        res = storage_manager.cache.get_cached_triage(query_hash, PROMPT_VERSION, MODEL_VERSION)
        if res:
            _L1_RAM_TRIAGE_CACHE[query_hash] = res
        return res
    except Exception as e:
        print(f"[Triage Cache Warning] Falha ao ler cache: {e}", file=sys.stderr)
    return None

def save_triage_to_cache(db_path: str, query: str, triage_res: dict):
    """Salva o resultado da triagem no cache L1 RAM e no SQLite."""
    query_hash = get_query_hash(query)
    cached_entry = dict(triage_res)
    cached_entry["source"] = "SQLITE_CACHE"
    _L1_RAM_TRIAGE_CACHE[query_hash] = cached_entry
    try:
        storage_manager.cache.save_triage_to_cache(
            query_hash,
            triage_res["intent"],
            triage_res["confidence"],
            1 if triage_res["needs_clarification"] else 0,
            triage_res.get("reason", ""),
            MODEL_VERSION,
            PROMPT_VERSION
        )
    except Exception as e:
        print(f"[Triage Cache Warning] Falha ao gravar cache: {e}", file=sys.stderr)




# --------------------------------------------------------------------------
# CLASSIFICADOR LLM & VALIDAÇÃO
# --------------------------------------------------------------------------
def call_triage_llm(query: str, gemini_client, history: list = None) -> dict:
    """Chama o Gemini com prompt ultradenso (<200 tokens) para classificar a intenção e reescrever a query."""
    history_context = ""
    if history:
        from agent.memory import ConversationMemory
        formatted = ConversationMemory.get_context(history, gemini_client)
        history_context = f"Histórico:\n{formatted}\n\n"

    prompt = (
        "Você é o triador do Duque IA (Prefeitura de Duque de Caxias - RJ).\n"
        "Classifique a pergunta do cidadão em uma intenção e reescreva-a para ser autossuficiente caso dependa do histórico.\n\n"
        "Intenções permitidas:\n"
        "SAUDACAO, IDENTIDADE, LGPD, JURIDICO, FORA_COMPETENCIA, AMBIGUO_LUZ, AMBIGUO_LAMPADA, AMBIGUO_BARULHO, "
        "RESIDENCIAL, OUVIDORIA_MANIFESTACAO, ESCALONAMENTO_HUMANO, POSSIVEL_DENUNCIA, AUTORIDADE_PUBLICA, PROGRAMACAO, CONVERSA, RAG_GERAL.\n\n"
        "Regras Rápidas e Desambiguação Multi-Turno:\n"
        "## REGRA CRÍTICA — PRESERVAÇÃO DA INTENÇÃO CONVERSACIONAL:\n"
        "Quando o usuário já tiver declarado uma intenção (como reclamação, solicitação, informação, denúncia, elogio, sugestão, pedido de serviço) e posteriormente fornecer informações para esclarecer ou detalhar essa intenção, NÃO altere a intenção original automaticamente.\n"
        "As novas mensagens devem ser interpretadas primeiro como possíveis complementos do contexto existente.\n"
        "Exemplo obrigatório:\n"
        "- Usuário: \"Quero abrir uma reclamação.\" -> intent = OUVIDORIA_MANIFESTACAO (tipo_manifestacao = reclamacao)\n"
        "- Usuário: \"Meu vizinho está com som alto.\" -> topic = SOM ALTO\n"
        "- Usuário: \"Estabelecimento comercial.\" -> intent = OUVIDORIA_MANIFESTACAO, topic = SOM ALTO, location_type = ESTABELECIMENTO COMERCIAL.\n"
        "A mensagem \"estabelecimento comercial\" NÃO deve ser classificada isoladamente como uma nova intenção!\n\n"
        "PROIBIDO:\n"
        "- Não transformar automaticamente: RECLAMAÇÃO -> DENÚNCIA\n"
        "- Não transformar automaticamente: ESTABELECIMENTO COMERCIAL -> ÓRGÃO/SERVIDOR DA PREFEITURA sem que o usuário tenha fornecido informação que justifique explicitamente essa mudança.\n\n"
        "MUDANÇA DE INTENÇÃO E RUPTURA TEMÁTICA:\n"
        "A intenção deve ser atualizada para uma nova demanda independente quando:\n"
        "1. o usuário fizer uma pergunta nova sobre outro serviço municipal (ex: perguntar sobre IPTU, vacina, ônibus Tarifa Zero, escola, hospital, biblioteca ou certidão após uma reclamação anterior);\n"
        "2. o usuário declarar explicitamente que mudou de assunto; ou\n"
        "3. a última mensagem contiver uma consulta autônoma e completa sobre políticas ou serviços da prefeitura.\n"
        "NÃO mantenha o usuário preso em fluxo de esclarecimento (needs_clarification=true) se ele fez uma pergunta nova e direta sobre outro assunto!\n\n"
        "REGRA DE DECISÃO ANTES DE REDIRECT:\n"
        "1. Se a última mensagem for um esclarecimento direto da pergunta anterior (ex: \"é na rua\", \"estabelecimento comercial\", \"meu bairro é Xerém\"): PRESERVAR INTENÇÃO e agregar contexto.\n"
        "2. Se a última mensagem for uma consulta factual nova e independente sobre serviços da Prefeitura: ATUALIZAR INTENÇÃO para RAG_GERAL com needs_clarification=false.\n\n"
        "- POSSIVEL_DENUNCIA = Usar ESTRITAMENTE para relatos de ofensas, xingamentos, ameaças, humilhações ou grosseria cometida por SERVIDORES PÚBLICOS MUNICIPAIS ou durante atendimento em postos/órgãos da Prefeitura. Reclamações de barulho, comércio, lixo, obras ou serviços urbanos NÃO são POSSIVEL_DENUNCIA.\n"
        "- FORA_COMPETENCIA = Usar APENAS para órgãos Estaduais (Metrô, Trem/Supervia, DETRAN), Federais (INSS, IRPF/Receita Federal) ou Prefeituras de OUTROS municípios. Perguntas sobre IPMDC (Instituto de Previdência dos Servidores de Duque de Caxias), previdência de servidores municipais, bairros de Caxias (Jardim Primavera, Xerém, 25 de Agosto, etc.), comércio local, restaurantes, passeios, história ou locais do município NÃO são FORA_COMPETENCIA -> use RAG_GERAL.\n"
        "- Zeladoria urbana (buraco, lixo, lâmpada pública) primeira vez sem protocolo = RAG_GERAL (needs_clarification=false).\n"
        "- Se o histórico contém uma dúvida sobre luz/iluminação (AMBIGUO_LUZ) e o usuário desambigua para postes ou lâmpadas da rua = RAG_GERAL (needs_clarification=false).\n"
        "- Manifestação de Ouvidoria com protocolo/atraso ou sem assunto = OUVIDORIA_MANIFESTACAO (needs_clarification=true se sem assunto).\n"
        "- Barulho sem local explícito = AMBIGUO_BARULHO (needs_clarification=true).\n"
        "- JURIDICO = Usar APENAS se o cidadão solicitar explicitamente que a IA formule petição jurídica, redija recurso/parecer legal ou elabore argumentos em ação judicial contra a prefeitura. Dúvidas sobre onde recorrer de multas municipais (JARI), prazos legais para recorrer de infrações, como consultar processos administrativos ou localização de secretarias NÃO são JURIDICO -> use RAG_GERAL.\n"
        "- Perguntas sobre QUEM É ou qual o nome do secretário/titular, prefeito ou vice = AUTORIDADE_PUBLICA (NÃO use para perguntas sobre o que faz uma secretaria ou diferença entre secretarias, que são RAG_GERAL).\n"
        "- Perguntas operacionais durante atendimento ('você que vai abrir?', 'você registra?', 'mas aí eu marco o quê?') = OUVIDORIA_MANIFESTACAO (NÃO use AI_META_INFO para isso).\n"
        "- MEMORIA_CONVERSACIONAL = Perguntas reflexivas sobre o histórico do diálogo, primeira pergunta feita, respostas anteriores ou assuntos já conversados (ex: \"qual foi minha primeira pergunta?\", \"o que você me respondeu antes?\", \"repita a segunda resposta\", \"sobre o que estamos conversando?\").\n"
        "- CLARIFICACAO_RESPOSTA = Pedidos de explicação didática, simplificação da resposta anterior (ex: \"não entendi\", \"explique melhor\", \"ficou confuso\") ou frustração e desabafo com a IA (ex: \"não entendi a resposta. vai à merda\", \"robô burro\"). NUNCA use POSSIVEL_DENUNCIA para insatisfação ou ofensas direcionadas ao assistente virtual!\n"
        "- AI_META_INFO = Perguntas sobre funcionamento, limites, confiabilidade ou se a IA inventa informações, números de protocolos, telefones ou encaminhamentos para agradar (ex: \"você inventaria informações para me agradar?\", \"você inventa protocolos?\", \"como você funciona?\"). NUNCA encaminhe para secretarias aleatórias!\n\n"
        f"{history_context}"
        f"Consulta: \"{query}\"\n\n"
        "Retorne APENAS um JSON:\n"
        "{\n"
        '  "intent": "SAUDACAO"|"LGPD"|"JURIDICO"|"FORA_COMPETENCIA"|"AMBIGUO_LUZ"|"AMBIGUO_LAMPADA"|"AMBIGUO_BARULHO"|"RESIDENCIAL"|"OUVIDORIA_MANIFESTACAO"|"ESCALONAMENTO_HUMANO"|"POSSIVEL_DENUNCIA"|"AUTORIDADE_PUBLICA"|"MEMORIA_CONVERSACIONAL"|"CLARIFICACAO_RESPOSTA"|"AI_META_INFO"|"PROGRAMACAO"|"CONVERSA"|"RAG_GERAL",\n'
        '  "tipo_manifestacao": "reclamacao"|"denuncia"|"elogio"|"sugestao"|"geral"|null,\n'
        '  "confidence": 0.0-1.0,\n'
        '  "needs_clarification": true|false,\n'
        '  "rewritten_query": "versão completa e autossuficiente",\n'
        '  "reason": "justificativa curta"\n'
        "}"
    )
    
    try:
        response_text = gemini_client.generate_response(prompt, model="gemini-3.1-flash-lite", temperature=0.0, max_output_tokens=350)
        match = re.search(r'\{.*\}', response_text.replace('\n', ' '), re.DOTALL)
        if match:
            triage_data = json.loads(match.group(0))
            intent = triage_data.get("intent", "").upper().strip()
            tipo_manifestacao = triage_data.get("tipo_manifestacao", None)
            
            if intent not in ALLOWED_INTENTS:
                raise ValueError(f"Intenção inválida retornada pelo LLM: {intent}")
                
            confidence = float(triage_data.get("confidence", 0.0))
            needs_clarification = bool(triage_data.get("needs_clarification", False))
            
            if confidence < 0.70:
                needs_clarification = True
                
            result = {
                "intent": intent,
                "confidence": confidence,
                "needs_clarification": needs_clarification,
                "reason": triage_data.get("reason", "Classificação estruturada."),
                "rewritten_query": triage_data.get("rewritten_query", query) or query
            }
            if tipo_manifestacao:
                result["tipo_manifestacao"] = tipo_manifestacao
            return result
    except Exception as e:
        print(f"[Triage Warning] Falha na chamada da LLM de Triagem: {e}", file=sys.stderr)
        
    # Fallback de Segurança
    return get_triage_fallback("Falha crítica ao obter classificação ou parsear JSON do LLM.")

def get_triage_fallback(reason: str) -> dict:
    """Retorna a resposta de fallback padrão segura para o RAG."""
    return {
        "intent": "RAG_GERAL",
        "confidence": 0.0,
        "needs_clarification": False,
        "reason": reason
    }

# --------------------------------------------------------------------------
# ENTRY POINT PRINCIPAL DA TRIAGEM
# --------------------------------------------------------------------------
def perform_triage(db_path: str, query: str, gemini_client, history: list = None) -> dict:
    """Orquestra as camadas de triagem (Fast Gate, Cache e LLM)."""
    # 1. Camada 0: Fast Gate (Regras Locais)
    fast_res = check_fast_gate(query, history=history)
    if fast_res:
        return _add_routing_metadata(fast_res)
        
    # Inicializa tabela de cache se necessário
    init_cache_db(db_path)
    
    # 2. Camada 1: Cache Persistente no SQLite (apenas se não houver histórico)
    if not history:
        cached_res = get_cached_triage(db_path, query)
        if cached_res:
            return _add_routing_metadata(cached_res)
        
    # 3. Camada 2: Agente de Triagem com LLM
    if gemini_client and len(gemini_client.api_keys) > 0:
        llm_res = call_triage_llm(query, gemini_client, history=history)
        # Salva no cache apenas classificações bem-sucedidas sem histórico
        if not history and llm_res.get("confidence", 0.0) > 0.0:
            save_triage_to_cache(db_path, query, llm_res)
        llm_res["source"] = "GEMINI_LLM"
        return _add_routing_metadata(llm_res)
        
    # Fallback caso não haja chaves de API
    return _add_routing_metadata(get_triage_fallback("Sem chaves de API disponíveis para o classificador remoto."))

def _add_routing_metadata(triage_res: dict) -> dict:
    """Enriquece o resultado da triagem com metadados de roteamento para a máquina de estados."""
    intent = triage_res.get("intent", "RAG_GERAL")
    needs_clarification = triage_res.get("needs_clarification", False)
    
    # Mapeamento de agentes e workflows
    if intent in ["LGPD", "ESCALONAMENTO_HUMANO", "FORA_COMPETENCIA", "JURIDICO", "DEFESA_CIVIL_EMERGENCIA", "SEGURANCA_PUBLICA_EMERGENCIA"]:
        triage_res["next_agent"] = "SECURITY_HANDLER"
        triage_res["workflow"] = "SECURITY_BLOCKED"
        triage_res["clarification_type"] = None
    elif intent in ["SAUDACAO", "CONVERSA", "IDENTIDADE"]:
        triage_res["next_agent"] = "CONVERSATION_HANDLER"
        triage_res["workflow"] = "CHAT"
        triage_res["clarification_type"] = None
    elif intent == "OUVIDORIA_MANIFESTACAO":
        triage_res["next_agent"] = "COLLECTOR_HANDLER"
        triage_res["workflow"] = "OUVIDORIA"
        triage_res["clarification_type"] = "OUVIDORIA" if needs_clarification else None
    elif intent == "POSSIVEL_DENUNCIA":
        triage_res["next_agent"] = "COLLECTOR_HANDLER"
        triage_res["workflow"] = "OUVIDORIA"
        triage_res["clarification_type"] = None
    elif intent == "AUTORIDADE_PUBLICA":
        triage_res["next_agent"] = "AUTHORITY_HANDLER"
        triage_res["workflow"] = "RAG"
        triage_res["clarification_type"] = None
    elif intent in ["AMBIGUO_LUZ", "AMBIGUO_LAMPADA", "AMBIGUO_BARULHO", "AMBIGUO_LOCALIZACAO"]:
        triage_res["next_agent"] = "AMBIGUITY_HANDLER"
        triage_res["workflow"] = "AMBIGUITY_RESOLVER"
        triage_res["clarification_type"] = "AMBIGUITY" if needs_clarification else None
    elif intent == "RESIDENCIAL":
        triage_res["next_agent"] = "PRIVATE_RESPONSIBILITY_HANDLER"
        triage_res["workflow"] = "PRIVATE"
        triage_res["clarification_type"] = None
    elif intent == "PROGRAMACAO":
        triage_res["next_agent"] = "PROGRAMACAO_HANDLER"
        triage_res["workflow"] = "PROGRAMACAO"
        triage_res["clarification_type"] = None
    elif intent == "MEMORIA_CONVERSACIONAL":
        triage_res["next_agent"] = "MEMORY_RECALL_HANDLER"
        triage_res["workflow"] = "MEMORY"
        triage_res["clarification_type"] = None
    elif intent == "CLARIFICACAO_RESPOSTA":
        triage_res["next_agent"] = "CLARIFICATION_HANDLER"
        triage_res["workflow"] = "CLARIFICATION"
        triage_res["clarification_type"] = None
    elif intent == "AI_META_INFO":
        triage_res["next_agent"] = "AI_META_HANDLER"
        triage_res["workflow"] = "AI_TRANSPARENCY"
        triage_res["clarification_type"] = None
    else:
        # Default: RAG_GERAL e outros informativos
        triage_res["next_agent"] = "RAG_HANDLER"
        triage_res["workflow"] = "RAG"
        triage_res["clarification_type"] = "RAG" if needs_clarification else None
        
    return triage_res
