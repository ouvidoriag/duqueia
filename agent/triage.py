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
    "RESIDENCIAL",
    "OUVIDORIA_MANIFESTACAO",
    "ESCALONAMENTO_HUMANO",
    "PROGRAMACAO",
    "CONVERSA",
    "RAG_GERAL",
    "POSSIVEL_DENUNCIA",
    "AUTORIDADE_PUBLICA"
}

# --------------------------------------------------------------------------
# FAST GATE / SECURITY POLICIES
# --------------------------------------------------------------------------
FAST_SECURITY_PATTERNS = []

for pat in PROGRAMMING_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "PROGRAMACAO", "Solicitação de programação bloqueada localmente."))

for pat in PRIVACY_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "LGPD", "Solicitação de dados/privacidade de terceiro bloqueada localmente."))

for pat in COMPETENCY_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "FORA_COMPETENCIA", "Assunto fora da competência municipal bloqueado localmente."))

for pat in LEGAL_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "JURIDICO", "Solicitação jurídica bloqueada localmente."))

for pat in HUMAN_ESCALATION_TRIGGERS:
    FAST_SECURITY_PATTERNS.append((pat, "ESCALONAMENTO_HUMANO", "Assunto sensível ou denúncia encaminhada para escalonamento humano."))


# Detecta queries de barulho/som onde o cidadão NÃO especifica se a origem é pública ou privada.
# Deve ficar ABAIXO dos padrões de segurança (LGPD/ESCALONAMENTO) que têm prioridade.
# Dispara AMBIGUO_BARULHO com needs_clarification=True para acionar o Agente Coletor.
AMBIGUITY_FAST_PATTERNS = [
    # Frases ambíguas de barulho sem menção explícita de vizinho/residência privada OU local público
    (
        r"(?:tem|tá|ta|tem|há|ha)\s+(?:um|uma|muito|um)\s+(?:barulho|som|algazarra|zoeira|bagunça|bagunceira)\b"
        r"(?!.*(?:vizinho|vizinha|apartamento|casa\s+(?:do|da|ao\s+lado)|residência|andar))"
        r"(?!.*(?:rua|praça|largo|parque|show|evento|bar\b|boate))",
        "AMBIGUO_BARULHO",
        "Reclamação de barulho sem origem explícita detectada — aguardando esclarecimento."
    ),
    # 'barulho insuportavel / excessivo / muito alto' sem local claro
    (
        r"barulho\s+(?:insuportáve[l]?|insuportave[l]?|excess[i]?vo|muito\s+alto|absurdo|horríve[l]?|horrivel)"
        r"(?!.*(?:vizinho|vizinha|apartamento|casa\s+(?:do|da|ao\s+lado)|residência|andar))"
        r"(?!.*(?:rua|praça|largo|parque|show|evento|bar\b|boate))",
        "AMBIGUO_BARULHO",
        "Reclamação de barulho intenso sem origem explícita — aguardando esclarecimento."
    ),
]

POSSIVEL_DENUNCIA_FAST_PATTERNS = [
    (r"\b(?:me\s+(?:\w+\s+)?xingou|me\s+(?:\w+\s+)?xingaram|xingou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de ofensa ou xingamento sofrido."),
    (r"\b(?:me\s+(?:\w+\s+)?tratou\s+(?:\w+\s+)?mal|me\s+(?:\w+\s+)?trataram\s+(?:\w+\s+)?mal|fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?tratado|fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?tratada)\b", "POSSIVEL_DENUNCIA", "Relato de mau tratamento sofrido."),
    (r"\b(?:foi\s+(?:\w+\s+)?grosseiro|foi\s+(?:\w+\s+)?grosseira|foram\s+(?:\w+\s+)?grosseiros)\b", "POSSIVEL_DENUNCIA", "Relato de grosseria sofrida."),
    (r"\b(?:me\s+(?:\w+\s+)?ofendeu|me\s+(?:\w+\s+)?ofenderam|ofendeu\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de ofensa sofrida."),
    (r"\b(?:foi\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?educado|foi\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?educada|foram\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?educados)\b", "POSSIVEL_DENUNCIA", "Relato de atitude mal educada."),
    (r"\b(?:me\s+(?:\w+\s+)?humilhou|me\s+(?:\w+\s+)?humilharam|humilhou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de humilhação sofrida."),
    (r"\b(?:me\s+(?:\w+\s+)?ameaçou|me\s+(?:\w+\s+)?ameaçaram|ameaçou\s+me|me\s+(?:\w+\s+)?ameacou|me\s+(?:\w+\s+)?ameacaram|ameacou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de ameaça sofrida."),
    (r"\b(?:me\s+(?:\w+\s+)?destratou|me\s+(?:\w+\s+)?destrataram|destratou\s+me)\b", "POSSIVEL_DENUNCIA", "Relato de desrespeito sofrido."),
    (r"\b(?:fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?atendido|fui\s+(?:\w+\s+)?mal\s+(?:\w+\s+)?atendida|mau\s+(?:\w+\s+)?atendimento|atendimento\s+(?:\w+\s+)?ruim)\b", "POSSIVEL_DENUNCIA", "Relato de atendimento inadequado."),
    (r"\b(?:fui\s+(?:\w+\s+)?vítima|fui\s+(?:\w+\s+)?vitima)\b", "POSSIVEL_DENUNCIA", "Relato de ter sido vítima de algo."),
    (r"\b(?:aconteceu\s+(?:\w+\s+)?comigo)\b", "POSSIVEL_DENUNCIA", "Relato pessoal de ocorrido.")
]

AUTORIDADE_PUBLICA_FAST_PATTERNS = [
    (r"\b(?:quem\s+é\s+o\s+prefeito|quem\s+e\s+o\s+prefeito|quem\s+é\s+o\s+prefeitor|qual\s+o\s+prefeito|qual\s+é\s+o\s+prefeito)\b", "AUTORIDADE_PUBLICA", "Busca direta pelo prefeito."),
    (r"\b(?:quem\s+é\s+o\s+vice|quem\s+e\s+o\s+vice|quem\s+é\s+a\s+vice|quem\s+e\s+a\s+vice|vice-prefeito|vice\s+prefeito|vice-prefeita|vice\s+prefeita)\b", "AUTORIDADE_PUBLICA", "Busca pelo vice-prefeito."),
    (r"\b(?:quem\s+é\s+o\s+secretário|quem\s+e\s+o\s+secretario|quem\s+é\s+a\s+secretária|quem\s+e\s+a\s+secretaria|qual\s+o\s+secretário|qual\s+o\s+secretario)\b", "AUTORIDADE_PUBLICA", "Busca por secretário."),
    (r"\b(?:quem\s+dirige|quem\s+administra|quem\s+comanda|quem\s+ocupa\s+o\s+cargo|responsável\s+pela\s+secretaria|responsavel\s+pela\s+secretaria|responsável\s+pelo\s+órgão|responsavel\s+pelo\s+orgao)\b", "AUTORIDADE_PUBLICA", "Busca pelo responsável de secretaria/órgão."),
    (r"\b(?:quem\s+é\s+o\s+ouvidor|quem\s+e\s+o\s+ouvidor|quem\s+é\s+o\s+procurador|quem\s+e\s+o\s+procurador|quem\s+é\s+o\s+controlador|quem\s+e\s+o\s+controlador)\b", "AUTORIDADE_PUBLICA", "Busca por autoridades de controle.")
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
    (r"\b(?:ouvidoria|colab|telefone|endereço|endereco|contato|horário|horario|secretaria|prefeitura)\b", "RAG_GERAL", "Consulta informativa de canais/secretarias detectada localmente.")
]

def check_fast_gate(query: str) -> dict | None:
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

    # 1º B: Relatos de ofensas/xingamentos/mau atendimento (alta prioridade, antes de conversa casual)
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
        "Regras Rápidas:\n"
        "- FORA_COMPETENCIA = Usar APENAS para órgãos Estaduais (Metrô, Trem/Supervia, DETRAN), Federais (INSS, IRPF/Receita Federal) ou Prefeituras de OUTROS municípios. Perguntas sobre bairros de Caxias (Jardim Primavera, Xerém, 25 de Agosto, etc.), comércio local, restaurantes, passeios, história ou locais do município NÃO são FORA_COMPETENCIA -> use RAG_GERAL.\n"
        "- Zeladoria urbana (buraco, lixo, lâmpada pública) primeira vez sem protocolo = RAG_GERAL (needs_clarification=false).\n"
        "- Se o histórico contém uma dúvida sobre luz/iluminação (AMBIGUO_LUZ) e o usuário desambigua para postes ou lâmpadas da rua = RAG_GERAL (needs_clarification=false).\n"
        "- Manifestação de Ouvidoria com protocolo/atraso ou sem assunto = OUVIDORIA_MANIFESTACAO (needs_clarification=true se sem assunto).\n"
        "- Barulho sem local explícito = AMBIGUO_BARULHO (needs_clarification=true).\n"
        "- Perguntas de secretários, prefeito, vice = AUTORIDADE_PUBLICA.\n\n"
        f"{history_context}"
        f"Consulta: \"{query}\"\n\n"
        "Retorne APENAS um JSON:\n"
        "{\n"
        '  "intent": "SAUDACAO"|"LGPD"|"JURIDICO"|"FORA_COMPETENCIA"|"AMBIGUO_LUZ"|"AMBIGUO_LAMPADA"|"AMBIGUO_BARULHO"|"RESIDENCIAL"|"OUVIDORIA_MANIFESTACAO"|"ESCALONAMENTO_HUMANO"|"POSSIVEL_DENUNCIA"|"AUTORIDADE_PUBLICA"|"PROGRAMACAO"|"CONVERSA"|"RAG_GERAL",\n'
        '  "tipo_manifestacao": "reclamacao"|"denuncia"|"elogio"|"sugestao"|"geral"|null,\n'
        '  "confidence": 0.0-1.0,\n'
        '  "needs_clarification": true|false,\n'
        '  "rewritten_query": "versão completa e autossuficiente",\n'
        '  "reason": "justificativa curta"\n'
        "}"
    )
    
    try:
        response_text = gemini_client.generate_response(prompt, model="gemini-3.1-flash-lite", temperature=0.0, max_output_tokens=150)
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
    fast_res = check_fast_gate(query)
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
    if intent in ["LGPD", "ESCALONAMENTO_HUMANO", "FORA_COMPETENCIA", "JURIDICO"]:
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
    elif intent in ["AMBIGUO_LUZ", "AMBIGUO_LAMPADA", "AMBIGUO_BARULHO"]:
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
    else:
        # Default: RAG_GERAL e outros informativos
        triage_res["next_agent"] = "RAG_HANDLER"
        triage_res["workflow"] = "RAG"
        triage_res["clarification_type"] = "RAG" if needs_clarification else None
        
    return triage_res
