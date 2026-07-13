from agent.config import OUVIDORIA_CONTACTS

def build_fallback_guidance(query: str) -> str:
    """Retorna orientação contextual quando a base de conhecimento não contém a resposta."""
    query_lower = query.lower()
    
    # Se a pergunta menciona ouvidoria, reclamação ou problema, direciona diretamente
    if any(k in query_lower for k in ["ouvidoria", "reclamação", "reclamacao", "denunciar", "registrar", "colab"]):
        return (
            "Para registrar sua solicitação, utilize os canais oficiais da **Ouvidoria Geral de Duque de Caxias**:\n\n"
            f"• Telefone: **{OUVIDORIA_CONTACTS['telefone']}**\n"
            f"• WhatsApp: **{OUVIDORIA_CONTACTS['whatsapp']}**\n"
            f"• E-mail: **{OUVIDORIA_CONTACTS['email']}**\n"
            f"• Presencial: **{OUVIDORIA_CONTACTS['presencial']}**\n"
            f"• Aplicativo: **Colab** (baixe no celular ou acesse [{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}))"
        )
    
    # Resposta genérica de redirecionamento quando não encontra informações
    return (
        "Desculpe, não encontrei informações sobre esse assunto específico na minha base de conhecimento oficial.\n\n"
        "Para registrar sua manifestação ou esclarecer sua dúvida, fale diretamente com a **Ouvidoria Geral de Duque de Caxias**:\n\n"
        f"• Telefone: **{OUVIDORIA_CONTACTS['telefone']}**\n"
        f"• WhatsApp: **{OUVIDORIA_CONTACTS['whatsapp']}**\n"
        f"• E-mail: **{OUVIDORIA_CONTACTS['email']}**\n"
        f"• Presencial: **{OUVIDORIA_CONTACTS['presencial']}**\n"
        f"• Online: aplicativo **Colab** ou site [{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']})."
    )

def is_query_too_vague(query: str) -> bool:
    """Retorna True se a pergunta for curta demais para uma resposta objetiva."""
    words = query.strip().split()
    return len(words) <= 2
