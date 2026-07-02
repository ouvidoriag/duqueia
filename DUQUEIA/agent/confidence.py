def calibrate_confidence(base_score: float, query: str, results: list) -> float:
    """Calibra a confidence com base no tipo de dado e especificidade dos chunks."""
    query_lower = query.lower()

    # Dados de alta certeza institucional
    high_certainty_terms = [
        "prefeito", "secretário", "secretaria", "endereço", "telefone",
        "secretario", "cargo", "gestão", "gestao"
    ]
    is_high_certainty = any(t in query_lower for t in high_certainty_terms)

    multi_doc = len(set(r["source"] for r in results)) > 1

    # Resultado de listagem global: confiança baseada na cobertura da base
    is_list_result = any(r.get("is_list_result") for r in results)
    if is_list_result:
        return 1.0

    if is_high_certainty and base_score >= 0.75:
        calibrated = max(base_score, 0.90)
    elif multi_doc and base_score >= 0.70:
        calibrated = max(base_score, 0.95)
    elif len(results) == 1 and base_score >= 0.65:
        calibrated = max(base_score, 0.80)
    elif base_score < 0.60:
        calibrated = max(base_score, 0.60)   # Piso mínimo para inferências
    else:
        calibrated = base_score

    return round(min(calibrated, 1.0), 2)
