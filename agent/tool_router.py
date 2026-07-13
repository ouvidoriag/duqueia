"""
tool_router.py — DUQUE IA
==========================
Seleciona a(s) fonte(s) de dados mais adequada(s) com base na intenção
e plano gerado pelo Planner. Reduz alucinações filtrando as fontes disponíveis.
"""

class ToolRouter:
    """
    Roteador de ferramentas. Mapeia intents para ferramentas específicas
    em vez de jogar tudo no banco vetorial.
    """
    
    # Mapeamento de Intents -> Ferramentas Recomendadas
    TOOL_MAP = {
        "secretaria_info":        ["structured_db"],
        "service_location":       ["structured_db", "geo_units"],
        "OUVIDORIA_MANIFESTACAO": ["questionnaires"],
        "RAG_GERAL":              ["faq_chunks"],
        "AMBIGUO_LUZ":            ["faq_chunks"],
        "AMBIGUO_BARULHO":        ["faq_chunks"],
        "PROGRAMACAO":            [],
        "SAUDACAO":               [],
        "FORA_COMPETENCIA":       [],
        "LGPD":                   [],
    }

    @staticmethod
    def select_tools(intent: str, queries: list) -> list:
        """
        Retorna uma lista de ferramentas ordenadas por relevância para a intenção.
        Se 'queries' contiver nomes de bairros, pode adicionar geo_units.
        """
        base_tools = ToolRouter.TOOL_MAP.get(intent, ["faq_chunks"])
        
        # Heurísticas de refinamento
        selected = list(base_tools)
        
        # Se for busca genérica mas cita bairros ou unidades, joga geo_units junto
        if "RAG_GERAL" in intent:
            if any("CRAS" in q or "UBS" in q or "Clínica" in q for q in queries):
                if "geo_units" not in selected:
                    selected.append("geo_units")
                    
        return selected
