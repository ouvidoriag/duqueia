import sys
import re
import json
from config.settings import LIST_INTENT_MAP
from agent.models import QueryIntent

_SYSTEM_INTENTS = {
    "IDENTIDADE": {
        "triggers": [
            "quem é você", "quem és você", "quem e voce", "quem é voce",
            "o que é você", "o que é voce", "você é uma ia", "voce é uma ia",
            "você é um robô", "você é humano", "voce e humano",
            "você é da prefeitura", "voce e da prefeitura",
            "me apresente", "se apresente", "fale sobre você",
            "quem te criou", "quem te fez", "como você foi criado"
        ],
        "response": (
            "Sou o **DUQUE IA**, o assistente virtual oficial da Prefeitura de Duque de Caxias — RJ.\n\n"
            "Fui desenvolvido para ajudar cidadãos a encontrar informações sobre serviços municipais de forma rápida e precisa.\n\n"
            "Posso ajudar com:\n"
            "- **Secretarias municipais** — endereços, contatos, atribuições\n"
            "- **Carta de Serviços** — como solicitar serviços públicos\n"
            "- **Saúde, Educação e Assistência Social** — equipamentos e procedimentos\n"
            "- **Ouvidoria** — como registrar reclamações e sugestões\n"
            "- **IPTU, Alvarás e Previdência** — orientações tributárias e administrativas\n"
            "- **Localização** — endereços de órgãos e equipamentos municipais\n\n"
            "Faça sua pergunta e farei o possível para ajudar."
        ),
        "confidence": 1.0,
        "intent_label": "identidade_assistente"
    },
    "SAUDACAO": {
        "triggers": [
            "olá", "ola", "oi", "oi!", "olá!", "hey", "bom dia", "boa tarde",
            "boa noite", "boas", "e aí", "e ai", "tudo bem", "tudo bom",
            "como vai", "como você está", "como voce esta", "oi tudo bem"
        ],
        "response": (
            "Olá! Sou o **DUQUE IA**, assistente virtual da Prefeitura de Duque de Caxias.\n\n"
            "Como posso ajudar você hoje? Pode perguntar sobre secretarias, serviços municipais, "
            "endereços, ouvidoria ou qualquer outro assunto relacionado à prefeitura."
        ),
        "confidence": 1.0,
        "intent_label": "saudacao"
    },
    "AGRADECIMENTO": {
        "triggers": [
            "obrigado", "obrigada", "muito obrigado", "muito obrigada",
            "valeu", "vlw", "agradeço", "agradecida", "agradecido",
            "grato", "grata", "ótimo obrigado", "perfeito obrigado",
            "ok obrigado", "ok obrigada", "tá bom obrigado"
        ],
        "response": (
            "Por nada! Se precisar de mais informações sobre os serviços da Prefeitura de Duque de Caxias, "
            "estou à disposição."
        ),
        "confidence": 1.0,
        "intent_label": "agradecimento"
    },
    "DESPEDIDA": {
        "triggers": [
            "tchau", "tchauzinho", "até mais", "ate mais", "até logo", "ate logo",
            "xau", "falou", "flw", "até", "até breve", "até amanhã",
            "até outra", "até a próxima", "encerrar", "finalizar", "sair"
        ],
        "response": (
            "Até mais! Sempre que precisar de informações sobre os serviços da Prefeitura de Duque de Caxias, "
            "estarei aqui. Tenha um ótimo dia!"
        ),
        "confidence": 1.0,
        "intent_label": "despedida"
    },
    "AJUDA": {
        "triggers": [
            "ajuda", "help", "socorro", "não sei", "nao sei", "como usar",
            "como funciona", "como posso usar", "como você funciona",
            "como voce funciona", "me ajuda", "me ajude", "preciso de ajuda",
            "o que posso perguntar", "que tipo de pergunta"
        ],
        "response": (
            "Posso ajudar com informações sobre os serviços e estrutura da Prefeitura de Duque de Caxias.\n\n"
            "**Como usar:**\n"
            "- Digite sua pergunta em linguagem natural\n"
            "- Seja específico: informe o serviço, bairro ou órgão quando souber\n\n"
            "**Exemplos de perguntas:**\n"
            "- *Qual o endereço da Secretaria de Saúde?*\n"
            "- *Como solicitar capina ou limpeza urbana?*\n"
            "- *Quais cursos a FUNDEC oferece?*\n"
            "- *Como emitir a segunda via do IPTU?*\n"
            "- *Quais secretarias temos na prefeitura?*\n\n"
            "Para assuntos não encontrados aqui, entre em contato com a **Ouvidoria Geral**: **(21) 2652-3835** ou ouvidoria@duquedecaxias.rj.gov.br"
        ),
        "confidence": 1.0,
        "intent_label": "ajuda"
    },
    "CAPACIDADES": {
        "triggers": [
            "o que você faz", "o que voce faz", "o que você sabe", "o que voce sabe",
            "quais assuntos", "quais temas", "sobre o que você responde",
            "sobre o que fala", "quais perguntas", "que assuntos você conhece",
            "o que você pode responder", "do que você trata",
            "listar capacidades", "suas capacidades"
        ],
        "response": (
            "Sou especializado em informações sobre a **Prefeitura de Duque de Caxias — RJ**.\n\n"
            "**Áreas que atendo:**\n"
            "- 🏛️ **Secretarias** — estrutura, contatos, secretários responsáveis\n"
            "- 📋 **Carta de Serviços** — como solicitar cada serviço municipal\n"
            "- 🏥 **Saúde** — unidades, vacinas, consultas, exames\n"
            "- 🎓 **Educação** — matrículas, escolas, FUNDEC\n"
            "- 🤝 **Assistência Social** — CRAS, benefícios, programas sociais\n"
            "- 🏗️ **Obras e Urbanismo** — alvarás, licenciamentos, tapa-buracos\n"
            "- 💰 **Fazenda** — IPTU, tributos municipais\n"
            "- 📍 **Localização** — endereços e referências geográficas\n"
            "- 📣 **Ouvidoria** — como registrar reclamações e sugestões\n\n"
            "Para perguntas fora desse escopo, recomendo o site oficial: **www.duquedecaxias.rj.gov.br**"
        ),
        "confidence": 1.0,
        "intent_label": "capacidades"
    },
    "APRESENTACAO": {
        "triggers": [
            "me chamo", "meu nome é", "meu nome e", "sou o", "sou a",
            "pode me chamar de", "pode chamar de", "me apresento",
            "meu nome eh", "meu nome:", "sou eu", "sou wellington",
            "sou cidadao", "sou cidadão", "sou morador", "sou moradora"
        ],
        "response": "Prazer, **{nome}**! Como posso ajudar você com informações ou serviços da Prefeitura de Duque de Caxias?",
        "confidence": 1.0,
        "intent_label": "apresentacao"
    }
}

class SystemIntentHandler:
    """Intercepta perguntas sobre o próprio assistente antes do pipeline RAG.

    Opera por correspondência de keywords normalizadas (sem acentos, lowercase).
    Retorna uma resposta fixa de alta confiança sem consultar o banco vetorial.
    """

    @staticmethod
    def _normalize(text: str) -> str:
        """Normaliza texto: lowercase + remove acentos básicos para robustez."""
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o',
            'ô': 'o', 'õ': 'o', 'ú': 'u', 'ç': 'c'
        }
        t = text.lower().strip()
        for src, dst in replacements.items():
            t = t.replace(src, dst)
        return t

    @staticmethod
    def _extract_name(query: str) -> str:
        """Tenta extrair o nome do usuário de frases de apresentação."""
        # Padrões para extração: "me chamo NOME", "meu nome é NOME", "sou o NOME", etc.
        patterns = [
            r"me chamo\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)*)",
            r"meu nome[\s\wé:]+?([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)*)",
            r"pode(?:m)?\s+me\s+chamar\s+de\s+([A-ZÀ-Ú][a-zà-ú]+)",
            r"pode(?:m)?\s+chamar\s+de\s+([A-ZÀ-Ú][a-zà-ú]+)",
            r"sou\s+(?:o|a)\s+([A-ZÀ-Ú][a-zà-ú]+)",
            r"^([A-ZÀ-Ú][a-zà-ú]{2,})$",  # só o nome capitalizado
        ]
        text_cap = query.strip()
        text_cap_titled = ' '.join(w.capitalize() for w in text_cap.split())
        for pat in patterns:
            m = re.search(pat, text_cap_titled)
            if m:
                return m.group(1).strip()
        return "cidadão"

    @staticmethod
    def detect(query: str) -> dict | None:
        """Verifica se a query se encaixa em uma intenção de sistema."""
        normalized = SystemIntentHandler._normalize(query)
        original_lower = query.lower().strip()

        for intent_name, intent_cfg in _SYSTEM_INTENTS.items():
            for trigger in intent_cfg["triggers"]:
                trigger_norm = SystemIntentHandler._normalize(trigger)
                pattern_norm = rf"\b{re.escape(trigger_norm)}\b"
                pattern_orig = rf"\b{re.escape(trigger.lower())}\b"
                if re.search(pattern_norm, normalized) or re.search(pattern_orig, original_lower):
                    result = dict(intent_cfg)
                    if intent_name == "APRESENTACAO" and "{nome}" in result.get("response", ""):
                        nome = SystemIntentHandler._extract_name(query)
                        result = dict(result)
                        result["response"] = result["response"].replace("{nome}", nome)
                    return result
        return None

class QueryAnalyzer:
    """Analisador de intenções determinístico com suporte a fallback de LLM."""

    @staticmethod
    def _detect_list_intent(query_lower: str) -> dict | None:
        for key, cfg in LIST_INTENT_MAP.items():
            if any(trigger in query_lower for trigger in cfg["triggers"]):
                return cfg
        return None

    @staticmethod
    def analyze(query: str, gemini_client=None) -> dict:
        query_lower = query.lower()

        # 0. Detecção prioritária de intenção de LISTAGEM
        list_cfg = QueryAnalyzer._detect_list_intent(query_lower)
        if list_cfg:
            return {
                "intent": QueryIntent.LIST,
                "confidence": 0.95,
                "entities": [],
                "list_config": list_cfg
            }

        # 1. Detecção por Regex e Keywords locais
        gis_indicators = [
            "rua", "avenida", "travessa", "bairro", "lote", "quadra", "mapa",
            "limite", "geográfico", "gis", "localizado", "onde fica", "perto de",
            "distrito", "onde", "qual distrito"
        ]
        inst_indicators = [
            "cras", "iptu", "alvara", "alvará", "fundec", "secretaria", "secretario",
            "secretário", "saude", "saúde", "transporte", "ônibus", "ouvidoria",
            "limpeza", "capina", "buraco", "vacina", "previdência", "previdencia",
            "ipmdc", "inscrição", "curso", "atendimento", "tapa buraco",
            "fiscalização", "fiscalizacao"
        ]

        has_gis = any(ind in query_lower for ind in gis_indicators)
        has_inst = any(ind in query_lower for ind in inst_indicators)

        bairros_conhecidos = [
            "jardim primavera", "parque lafaiete", "25 de agosto", "imbarie",
            "xerem", "xerém", "saracuruna", "campos elyseos",
            "chácaras arpoador", "pantanal", "pilar"
        ]
        detected_bairro = None
        for b in bairros_conhecidos:
            if b in query_lower:
                detected_bairro = b
                break

        detected_category = None
        for s in ["cras", "iptu", "fundec", "ouvidoria", "ipmdc", "saude", "saúde"]:
            if s in query_lower:
                detected_category = s
                break

        entities = []
        if detected_bairro:
            entities.append({"type": "bairro", "value": detected_bairro})
        if detected_category:
            entities.append({"type": "category", "value": detected_category})

        # Determina intenção heurística e confiança inicial
        if detected_bairro:
            intent = QueryIntent.GIS
            confidence = 0.95
        elif has_gis and not has_inst:
            intent = QueryIntent.GIS
            confidence = 0.90
        elif has_inst:
            if "onde" in query_lower or "endereço" in query_lower or "fica" in query_lower or "distrito" in query_lower:
                intent = QueryIntent.GIS
            else:
                intent = QueryIntent.INSTITUTIONAL
            confidence = 0.85
        else:
            intent = QueryIntent.GENERAL
            confidence = 0.60

        # 2. Fallback para LLM se confiança for baixa
        if confidence < 0.75 and gemini_client and len(gemini_client.api_keys) > 0:
            try:
                prompt = (
                    f'Analise a pergunta do munícipe de Duque de Caxias e classifique em UMA das categorias:\n'
                    f'- gis (localizações, ruas, limites, mapas, onde fica)\n'
                    f'- institutional (procedimentos, secretarias, IPTU, alvarás, como solicitar)\n'
                    f'- general (explicações gerais, história, perguntas abertas)\n'
                    f'Pergunta: "{query}"\n'
                    f'Responda APENAS em JSON: {{"intent": "gis"|"institutional"|"general", "confidence": 0.0-1.0, "reason": "..."}}'  
                )
                response_text = gemini_client.generate_response(prompt)
                match = re.search(r'\{.*\}', response_text.replace('\n', ' '), re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    llm_intent = data.get("intent", "").lower()
                    llm_conf = float(data.get("confidence", 0.75))
                    if llm_intent == "gis":
                        intent = QueryIntent.GIS
                    elif llm_intent == "institutional":
                        intent = QueryIntent.INSTITUTIONAL
                    elif llm_intent == "general":
                        intent = QueryIntent.GENERAL
                    confidence = llm_conf
            except Exception as e:
                print(f"[QueryAnalyzer Warning] Falha no fallback do LLM: {e}", file=sys.stderr)

        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities
        }
