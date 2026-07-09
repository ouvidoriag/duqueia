import sqlite3
import hashlib
import json
import re
import os
import sys

# Modelo e versão do prompt para controle de cache
MODEL_VERSION = "gemini-3.1-flash-lite"
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
    "RAG_GERAL"
}

# --------------------------------------------------------------------------
# FAST GATE / SECURITY POLICIES
# --------------------------------------------------------------------------
FAST_SECURITY_PATTERNS = [
    # PROGRAMACAO: Pedidos de códigos em linguagens de programação
    (
        r"\b(?:código|codigo)\s+em\s+(?:python|javascript|java|c\+\+|html|css|php|sql|bash|ruby|rust)\b|\b(?:como\s+programar|gerar\s+codigo)\b",
        "PROGRAMACAO",
        "Solicitação de programação bloqueada localmente."
    ),
    # LGPD: Pedidos explícitos de dados confidenciais, CPF, nomes de reclamantes ou andamento de terceiros
    (
        r"cpf\s+(?:de|do|da|do\s+meu|da\s+minha|de\s+um|de\s+uma)?\s*(?:cidadão|cidadao|reclamante|outro|terceiro|vizinho|vizinha|fulano|sicrano|beltrano|wellington)",
        "LGPD",
        "Solicitação de CPF de terceiro bloqueada localmente."
    ),
    (
        r"protocolo\s+.*(?:vizinho\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|vizinha\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|outro|outra|terceiro|terceira|fulano|sicrano|wellington)",
        "LGPD",
        "Solicitação de protocolo de terceiro bloqueada localmente."
    ),
    (
        r"nome\s+(?:dele|dela|do\s+vizinho\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|da\s+vizinha\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|do\s+reclamante|do\s+outro|da\s+outra)",
        "LGPD",
        "Solicitação de nome de reclamante/vizinho bloqueada localmente."
    ),
    (
        r"reclamaç(?:ão|ões|ao)\s+abertas?\s+sobre\s+(?:o\s+bar|o\s+estabelecimento|vizinho\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|vizinha\b(?![^#]*?(?:som|barulho|musica|música|festa|algazarra))|outro|terceiro)",
        "LGPD",
        "Solicitação de visualização de reclamações de terceiros bloqueada localmente."
    ),
    # FORA_COMPETENCIA: Temas federais/estaduais fora da alçada municipal
    (
        r"\bmetrô\b|\bmetro\b",
        "FORA_COMPETENCIA",
        "Assunto sobre metrô (âmbito estadual) bloqueado localmente."
    ),
    # JURIDICO: Tentativa de obter pareceres legais contra a prefeitura
    (
        r"formular\s+(?:defesa|parecer|recurso)",
        "JURIDICO",
        "Solicitação de defesa ou parecer legal contra a administração pública bloqueada localmente."
    ),
    (
        r"argumentos?\s+contra\s+o\s+poder\s+público",
        "JURIDICO",
        "Solicitação de formulação de argumentos jurídicos bloqueada localmente."
    ),
    # ESCALONAMENTO_HUMANO: Denúncias de corrupção, suborno, desvio de verbas envolvendo funcionários/secretários
    (
        r"desvi(?:o|ando)\s+verba|roub(?:o|ando)|suborn(?:o|ar|ando)|corrupç(?:ão|ao)|\bsecretário\s+roub\w+",
        "ESCALONAMENTO_HUMANO",
        "Denúncia grave contra a administração municipal encaminhada para escalonamento humano."
    ),
    # ESCALONAMENTO_HUMANO: Ameaças de agressão, violência ou morte (ex: quero matar meu vizinho)
    (
        r"\b(?:matar|agredir|bater|violentar|assassinar|morrer|espancar|facada|tiro)\b",
        "ESCALONAMENTO_HUMANO",
        "Assuntos sensíveis, ameaças de agressão ou injúria grave encaminhados para escalonamento humano."
    )
]

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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
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
    conn.commit()
    conn.close()

def get_query_hash(query: str) -> str:
    """Gera um hash md5 único a partir da query normalizada."""
    normalized = query.lower().strip()
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def get_cached_triage(db_path: str, query: str) -> dict | None:
    """Busca o resultado da triagem no cache SQLite."""
    init_cache_db(db_path)
    query_hash = get_query_hash(query)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT intent, confidence, needs_clarification, reason FROM triage_cache "
            "WHERE query_hash = ? AND prompt_version = ? AND model_version = ?",
            (query_hash, PROMPT_VERSION, MODEL_VERSION)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "intent": row[0],
                "confidence": float(row[1]),
                "needs_clarification": bool(row[2]),
                "reason": row[3],
                "source": "SQLITE_CACHE"
            }
    except Exception as e:
        print(f"[Triage Cache Warning] Falha ao ler cache: {e}", file=sys.stderr)
    return None

def save_triage_to_cache(db_path: str, query: str, triage_res: dict):
    """Salva o resultado da triagem no cache SQLite."""
    init_cache_db(db_path)
    query_hash = get_query_hash(query)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO triage_cache "
            "(query_hash, intent, confidence, needs_clarification, reason, model_version, prompt_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                query_hash,
                triage_res["intent"],
                triage_res["confidence"],
                1 if triage_res["needs_clarification"] else 0,
                triage_res.get("reason", ""),
                MODEL_VERSION,
                PROMPT_VERSION
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Triage Cache Warning] Falha ao gravar cache: {e}", file=sys.stderr)

# --------------------------------------------------------------------------
# CLASSIFICADOR LLM & VALIDAÇÃO
# --------------------------------------------------------------------------
def call_triage_llm(query: str, gemini_client, history: list = None) -> dict:
    """Chama o Gemini para classificar a intenção e valida o resultado."""
    history_context = ""
    if history:
        history_context = "Histórico de mensagens anteriores nesta conversa:\n"
        for i, msg in enumerate(history, 1):
            history_context += f"Mensagem anterior {i}: \"{msg}\"\n"
        history_context += "\n"

    prompt = (
        "Você é o Agente de Triagem oficial do Duque IA da Prefeitura de Duque de Caxias.\n"
        "Sua função é classificar a consulta do cidadão em uma intenção municipal estruturada.\n"
        "Analise a consulta atual à luz das mensagens anteriores (se fornecidas no histórico abaixo) para entender o contexto e saber se alguma ambiguidade já foi esclarecida.\n"
        "\n"
        "REGRAS DE RESOLUÇÃO DE HISTÓRICO:\n"
        "- Se o munícipe foi anteriormente questionado sobre uma escolha ambígua (ex: 'é na sua casa ou iluminação pública / poste na rua?', ou 'é barulho de vizinho ou evento público/rua?') e a última mensagem dele é uma resposta a essa pergunta (ex: 'lâmpada', 'é uma lâmpada', 'poste', 'rua', 'é da rua', 'vizinho', 'casa', 'queimada', 'queimanda prora'), NÃO classifique como AMBIGUO. Use o histórico para inferir a intenção e resolver a ambiguidade:\n"
        "  * Se ele responde 'lâmpada', 'é uma lâmpada', 'poste', 'rua', 'queimada', 'queimanda prora' etc., após perguntarmos de iluminação pública vs residencial, classifique como RAG_GERAL (needs_clarification=false).\n"
        "  * Se ele responde 'na minha casa', 'no meu quarto', 'minha casa', 'aqui em casa' etc., classifique como RESIDENCIAL (needs_clarification=false).\n"
        "  * Se ele responde 'vizinho', 'casa ao lado' etc., para barulho, classifique como RAG_GERAL (needs_clarification=false) para que a resposta informe Polícia (190).\n"
        "  * Se ele responde 'rua', 'show', 'praça' etc., para barulho, classifique como RAG_GERAL (needs_clarification=false) para orientar o Colab.\n"
        "Não responda à pergunta do usuário. Apenas identifique a intenção e classifique-a.\n\n"
        "Categorias permitidas:\n"
        "- SAUDACAO: Cumprimentos simples (oi, olá, bom dia, tchau).\n"
        "- IDENTIDADE: Perguntas sobre quem é você ou suas capacidades.\n"
        "- LGPD: Solicitação de CPFs, nomes de reclamantes ou andamento de protocolos de terceiros (vizinhos).\n"
        "- JURIDICO: Pedido de formulação de defesas, pareceres ou recursos contra o poder público.\n"
        "- FORA_COMPETENCIA: Assuntos que competem ao Estado ou União (ex: linhas de metrô, rodovias federais).\n"
        "- AMBIGUO_LUZ: Dúvida sobre falta de luz (distribuição Light) ou lâmpada apagada no poste da rua.\n"
        "- AMBIGUO_LAMPADA: Dúvida sobre troca de lâmpada dentro da residência vs poste público de rua.\n"
        "- AMBIGUO_BARULHO: Reclamação de barulho excessivo, som alto, festas ou algazarra onde NÃO esteja claro se a origem é em local privado (vizinho/residência) ou em local público (rua, praça, evento, bar).\n"
        "  * Defina needs_clarification=true e intent=AMBIGUO_BARULHO se o cidadão reclamar de barulho/som/festa mas NÃO especificar a origem. Ex: 'tem barulho perto de casa', 'ta tendo festa e não consigo dormir', 'muito barulho aqui na minha rua'.\n"
        "  * EXCEÇÃO RAG_GERAL: Se o cidadão especificar claramente que é vizinho/residência particular (ex: 'meu vizinho com som alto', 'festa na casa ao lado', 'apartamento do Rildo'), classifique como RAG_GERAL — o RAG direciona para a Polícia (190).\n"
        "  * EXCEÇÃO RAG_GERAL: Se o cidadão especificar claramente que é evento público/rua/praça (ex: 'show na praça', 'baile funk na rua', 'bar na esquina'), classifique como RAG_GERAL — o RAG direciona para Ordem Urbana/Colab.\n"
        "  * Exemplo AMBIGUO_BARULHO: 'ta tendo um barulho insuportavel perto da minha casa' → needs_clarification=true (não se sabe se é vizinho ou rua).\n"
        "  * Exemplo AMBIGUO_BARULHO: 'tem uma festa que não me deixa dormir' → needs_clarification=true (não se sabe se é casa ao lado ou rua).\n"
        "- RESIDENCIAL: Manutenção elétrica interna em área particular ou condomínio privado.\n"
        "- OUVIDORIA_MANIFESTACAO: O cidadão quer registrar uma manifestação oficial na Ouvidoria Geral (reclamação, denúncia, sugestão ou elogio).\n"
        "  * ATENÇÃO (CRÍTICO - ZELADORIA URBANA): Se o cidadão está relatando um problema de zeladoria urbana pela primeira vez (ex: 'tem um buraco na minha rua', 'lixo acumulado na calçada', 'poste apagado na rua') sem mencionar que já fez um pedido anterior ou que possui um protocolo não atendido, classifique como RAG_GERAL. O objetivo é orientá-lo a abrir uma 'Solicitação de Serviço' de zeladoria comum no Colab, e não uma reclamação na Ouvidoria.\n"
        "  * Classifique como OUVIDORIA_MANIFESTACAO apenas se: (1) O cidadão disser expressamente que já solicitou o serviço anteriormente e o problema não foi resolvido; (2) O cidadão disser que possui um número de protocolo pendente/atrasado; ou (3) O cidadão expressar a intenção direta de reclamar da Ouvidoria/Prefeitura em geral.\n"
        "  * Defina needs_clarification=true apenas se o cidadão indicou que quer abrir uma manifestação, mas NÃO especificou qual é o assunto municipal (ex: 'quero fazer uma reclamação', 'quero abrir uma manifestação', 'como faço uma denúncia' - sem citar o problema).\n"
        "  * Defina needs_clarification=false se o cidadão já especificou o assunto ou problema municipal (ex: 'cratera na rua', 'poste caindo', 'lixo acumulado', 'buraco na rua'), mesmo que ele NÃO tenha fornecido a localização ou o endereço exato do fato. Não insista no endereço, pois ele será direcionado a preenchê-lo no aplicativo Colab.\n"
        "  * Exemplo com clarification=false: 'quero reclamar de buraco na rua que já solicitei mês passado' — tipo_manifestacao=reclamacao, assunto=buraco na rua, needs_clarification=false.\n"
        "  * Exemplo com clarification=true: 'quero fazer uma reclamação' — tipo_manifestacao=reclamacao, assunto não especificado, então needs_clarification=true.\n"
        "- ESCALONAMENTO_HUMANO: Denúncias graves contra a administração, desvios de verbas, subornos ou corrupção envolvendo servidores.\n"
        "- PROGRAMACAO: Solicitações de codificação, scripts, programação de computadores ou TI em geral (ex: 'me de um codigo em python').\n"
        "- CONVERSA: Bate-papo geral, piadas, conversa fiada, discussões filosóficas ou perguntas sobre o mundo fora do domínio municipal.\n"
        "- RAG_GERAL: Dúvidas específicas de serviços municipais (tapa-buracos, CRAS, IPTU, escolas, cursos FUNDEC, telefones, endereços, iluminação pública resolvida, obras resolvidas).\n\n"
        f"{history_context}"
        f"Consulta atual do cidadão: \"{query}\"\n\n"
        "Retorne EXCLUSIVAMENTE um objeto JSON válido contendo:\n"
        "{\n"
        '  "intent": "SAUDACAO"|"IDENTIDADE"|"LGPD"|"JURIDICO"|"FORA_COMPETENCIA"|"AMBIGUO_LUZ"|"AMBIGUO_LAMPADA"|"AMBIGUO_BARULHO"|"RESIDENCIAL"|"OUVIDORIA_MANIFESTACAO"|"ESCALONAMENTO_HUMANO"|"PROGRAMACAO"|"CONVERSA"|"RAG_GERAL",\n'
        '  "tipo_manifestacao": "reclamacao"|"denuncia"|"elogio"|"sugestao"|"geral"|null,\n'
        '  "confidence": 0.0-1.0,\n'
        '  "needs_clarification": true|false,\n'
        '  "reason": "Breve justificativa técnica da classificação."\n'
        "}"
    )
    
    try:
        response_text = gemini_client.generate_response(prompt, model="gemini-3.1-flash-lite", temperature=0.0, max_output_tokens=150)
        match = re.search(r'\{.*\}', response_text.replace('\n', ' '), re.DOTALL)
        if match:
            triage_data = json.loads(match.group(0))
            intent = triage_data.get("intent", "").upper().strip()
            tipo_manifestacao = triage_data.get("tipo_manifestacao", None)
            
            # Validação do Schema
            if intent not in ALLOWED_INTENTS:
                raise ValueError(f"Intenção inválida retornada pelo LLM: {intent}")
                
            confidence = float(triage_data.get("confidence", 0.0))
            needs_clarification = bool(triage_data.get("needs_clarification", False))
            
            # Ajuste de Confiança (< 0.70 força esclarecimento)
            if confidence < 0.70:
                needs_clarification = True
                
            result = {
                "intent": intent,
                "confidence": confidence,
                "needs_clarification": needs_clarification,
                "reason": triage_data.get("reason", "Classificação estruturada.")
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
