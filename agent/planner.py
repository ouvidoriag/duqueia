"""
planner.py  —  Duque IA
Módulo orquestrador semântico (LORS).
Usa LLM para analisar a pergunta do cidadão e gerar uma estratégia de busca multi-query.
"""

import sys
import os
import json
import re
import unicodedata

def normalize_text(text: str) -> str:
    """Normaliza texto removendo acentos, caixa alta e pontuação para busca uniforme."""
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return re.sub(r'[^\w\s]', ' ', text).strip()

# Motor declarativo de regras de reescrita e planejamento semântico offline
OFFLINE_RULES = [
    {
        "intent": "service_location",
        "triggers": [r"\bcadastro\b", r"\bcadunico\b"],
        "queries": [
            "Cadastramento - cadastro único",
            "Secretaria Municipal de Assistência Social e Direitos Humanos",
            "CRAS"
        ],
        "focus": ["address", "steps", "phone"]
    },
    {
        "intent": "secretaria_info",
        "triggers": [r"\bobras\b", r"\bsmo\b"],
        "queries": ["Secretaria Municipal de Obras e Agricultura"],
        "focus": ["address", "phone"],
        "dynamic": [
            {"triggers": [r"\btapa\b", r"\bburaco\b"], "add_queries": ["Tapa Buraco"]}
        ]
    },
    {
        "intent": "secretaria_info",
        "triggers": [r"\burbanismo\b", r"\bsmu\b", r"\bsemuh\b", r"\burbanizmo\b"],
        "queries": ["Secretaria Municipal de Urbanismo e Habitação"],
        "focus": ["address", "phone"]
    },
    {
        "intent": "secretaria_info",
        "triggers": [r"\bsaude\b", r"\bhomem\b", r"\bmulher\b", r"\bmedico\b", r"\bposto\b"],
        "queries": ["Secretaria Municipal de Saúde", "saúde"],
        "focus": ["address", "phone"]
    },
    {
        "intent": "secretaria_info",
        "triggers": [r"\biptu\b", r"\bfazenda\b", r"\bimposto\b", r"\btributo\b", r"\balvara\b"],
        "queries": ["Secretaria Municipal de Fazenda", "IPTU"],
        "focus": ["address", "phone"]
    },
    {
        "intent": "secretaria_info",
        "triggers": [r"\bcomercio\b", r"\bambulante\b", r"\bposturas\b", r"\bcamel\b"],
        "queries": ["Secretaria Municipal de Segurança Pública", "Comércio irregular"],
        "focus": ["address", "phone"]
    },
    {
        "intent": "general_info",
        "triggers": [r"\bdistrito\b", r"\bbairro\b", r"\bhistoria\b", r"\borigem\b", r"\bprefeito\b", r"\bcidade\b"],
        "queries": ["a_cidade.md", "prefeito.md", "Duque de Caxias"],
        "focus": ["general"]
    }
]

class SemanticRecoveryPlanner:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.using_real = gemini_client is not None and len(gemini_client.api_keys) > 0

    def plan_recovery(self, query: str, history: list = None) -> dict:
        """Gera um plano de busca estruturado com múltiplas queries sugeridas pela LLM."""
        if not self.using_real:
            return self._generate_offline_plan(query, history)

        history_context = ""
        if history:
            history_context = "\n".join([f"Munícipe: {msg}" for msg in history[-3:]])

        prompt = (
            "Você é o Planejador Semântico (Planner) do RAG do Duque IA (atendimento municipal).\n"
            "Sua tarefa é analisar a pergunta atual do munícipe e o histórico recente e gerar um plano "
            "de busca de informações em formato JSON contendo até 3 consultas complementares a serem feitas no banco de dados "
            "para responder de forma completa.\n\n"
            "Diretriz de Geração de Queries:\n"
            "1. Se o munícipe pergunta sobre onde fazer um serviço (ex: 'onde faço cadastro único perto de mim?'), "
            "gere uma query para o serviço (ex: 'Cadastro Único'), uma query para a secretaria (ex: 'Secretaria de Assistência Social') "
            "e uma query para locais físicos de atendimento (ex: 'CRAS Duque de Caxias').\n"
            "2. Se for uma pergunta puramente de contato (ex: 'qual o telefone da secretaria de obras?'), "
            "gere queries focadas no órgão (ex: 'Secretaria de Obras') e canais de contato.\n"
            "3. Se for uma pergunta genérica, gere apenas a query reescrita principal.\n\n"
            "Retorne APENAS um JSON válido no seguinte formato, sem explicações, prefixos ou blocos markdown:\n"
            "{\n"
            '  "intent": "service_location",\n'
            '  "queries": [\n'
            '    "Cadastro Único",\n'
            '    "Secretaria de Assistência Social e Direitos Humanos",\n'
            '    "CRAS"\n'
            '  ],\n'
            '  "focus": ["address", "steps", "phone"]\n'
            "}\n\n"
            f"Histórico:\n{history_context}\n\n"
            f"Pergunta Atual: \"{query}\"\n\n"
            "JSON de Recuperação:"
        )

        try:
            res = self.gemini_client.generate_response(prompt, model="gemini-3.1-flash-lite").strip()
            # Remove blocos de markdown ```json se a LLM os incluir
            res = re.sub(r"^```json\s*", "", res)
            res = re.sub(r"\s*```$", "", res)
            
            plan = json.loads(res.strip())
            # Garante que temos a chave queries
            if "queries" in plan and isinstance(plan["queries"], list):
                return plan
        except Exception as e:
            print(f"[LORS Planner Warning] Falha na geração do plano de busca via LLM: {e}", file=sys.stderr)

        return self._generate_offline_plan(query, history)

    def _generate_offline_plan(self, query: str, history: list = None) -> dict:
        """Fallback local offline usando o motor declarativo de regras."""
        query_norm = normalize_text(query)
        
        for rule in OFFLINE_RULES:
            # Verifica se algum trigger da regra casa na query normalizada
            if any(re.search(trigger, query_norm) for trigger in rule["triggers"]):
                queries = list(rule["queries"])
                # Processa regras dinâmicas/complementares da regra principal
                if "dynamic" in rule:
                    for dyn in rule["dynamic"]:
                        if any(re.search(dt, query_norm) for dt in dyn["triggers"]):
                            queries.extend(dyn["add_queries"])
                return {
                    "intent": rule["intent"],
                    "queries": queries,
                    "focus": rule["focus"]
                }
                
        # Caso padrão se nenhuma regra casar
        return {
            "intent": "general",
            "queries": [query],
            "focus": ["general"]
        }
