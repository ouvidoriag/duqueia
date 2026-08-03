"""
Engine de Cálculo do Score de Completude de Dados (Data Completeness Engine).
Avalia a riqueza dos dados de um candidato (estruturado SQL ou Markdown)
para evitar que registros relacionais com campos vazios (NULL) vençam
documentos descritivos ricos no ranking final do RAG.
"""

def calculate_completeness_score(candidate: dict) -> float:
    """
    Calcula o fator multiplicador de completude [0.10 a 1.00].
    
    Regra:
    final_score = retrieval_score * completeness_score
    """
    if not candidate:
        return 0.10

    category = candidate.get("category", "")
    content = candidate.get("content", "")
    source = str(candidate.get("source", ""))

    # 1. Chunks descritivos de Markdown ou FAQ auditados (ex: lacunas_dados_resolvidas.md)
    if "lacunas_dados_resolvidas" in source or "educacao.md" in source or category in ["general", "faq_chunks"]:
        if len(content) > 300:
            return 1.00
        elif len(content) > 100:
            return 0.85
        return 0.70

    # 2. Registros da view relacional vw_ia_servicos ou tabela de serviços
    if "vw_ia_servicos" in source or category == "carta_servicos":
        content_lower = content.lower()

        # Verifica campos nulos ou ausentes no texto formatado
        has_how = "como solicitar" in content_lower or "passo a passo" in content_lower
        has_docs = "documentação necessária" in content_lower or "documentacao" in content_lower
        has_address = "endereço de atendimento" in content_lower and "não cadastrado" not in content_lower
        has_desc = "descrição:" in content_lower and "não cadastrado" not in content_lower

        score = 0.55  # Base ajustada por ser registro oficial auditado da Carta de Serviços

        if has_how:
            score += 0.20
        if has_docs:
            score += 0.15
        if has_address:
            score += 0.10
        if has_desc:
            score += 0.10

        return min(round(score, 2), 1.00)

    # 3. Fichas cadastrais de Secretarias e Unidades Físicas (CRAS/Postos)
    if category in ["secretarias", "unidades"]:
        if "não disponível" in content.lower() or "não cadastrado" in content.lower():
            return 0.60
        return 0.95

    return 0.80
