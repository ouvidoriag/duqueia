def build_fallback_guidance(query: str) -> str:
    """Retorna orientação contextual quando a base de conhecimento não contém a resposta."""
    query_lower = query.lower()
    
    # Se a pergunta menciona ouvidoria, reclamação ou problema, direciona diretamente
    if any(k in query_lower for k in ["ouvidoria", "reclamação", "reclamacao", "denunciar", "registrar", "colab"]):
        return (
            "Para registrar sua solicitação, utilize os canais oficiais da **Ouvidoria Geral de Duque de Caxias**:\n\n"
            "• Telefone: **(21) 2652-3835**\n"
            "• E-mail: **ouvidoria@duquedecaxias.rj.gov.br**\n"
            "• Presencial: **Alameda Esmeralda, 206 - Jardim Primavera**\n"
            "• Aplicativo: **Colab** (disponível para Android e iOS)"
        )
    
    # Resposta genérica informativa e natural
    return (
        "Sou especializado em serviços da **Prefeitura de Duque de Caxias — RJ**. "
        "Não encontrei informações sobre esse assunto específico na minha base de conhecimento oficial.\n\n"
        "Posso ajudar com:\n"
        "- **Secretarias** — endereços, telefones, atribuições\n"
        "- **Serviços Municipais** — IPTU, alvarás, capina, tapa-buraco, saúde\n"
        "- **Ouvidoria** — como registrar reclamações, sugestões e elogios\n"
        "- **Equipamentos Públicos** — CRAS, UPAs, escolas, FUNDEC\n\n"
        "Reformule sua pergunta ou entre em contato pela Ouvidoria Geral: **(21) 2652-3835** | ouvidoria@duquedecaxias.rj.gov.br | Presencial: **Alameda Esmeralda, 206 - Jardim Primavera**"
    )

def is_query_too_vague(query: str) -> bool:
    """Retorna True se a pergunta for curta demais para uma resposta objetiva."""
    words = query.strip().split()
    return len(words) <= 2
