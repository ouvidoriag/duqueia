import unicodedata
from typing import List, Tuple
from agent.candidate import Candidate
from agent.rules_config import BOOST_RULES, BOOST_WEIGHTS, KNOWN_LOCALITIES

class CandidateRanker:
    """
    Motor Declarativo de Ranking e Avaliação de Confiança.
    Aplica as BOOST_RULES declarativas, registra a explicabilidade de cada score
    e calcula o nível de confiança do contexto recuperado (ALTA, MÉDIA, BAIXA).
    """

    @staticmethod
    def apply_ranking(query: str, candidates: List[Candidate]) -> List[Candidate]:
        query_norm = ''.join(c for c in unicodedata.normalize('NFKD', query.lower()) if not unicodedata.combining(c))

        for cand in candidates:
            # Inicializa o retrieval_score com base no score híbrido/semântico inicial
            if cand.retrieval_score == 0.0:
                cand.retrieval_score = round(0.85 * cand.semantic_score + 0.15 * cand.keyword_score, 4)
                cand.add_explanation(f"Base híbrida: semântico ({cand.semantic_score:.2f}) + palavra-chave ({cand.keyword_score:.2f})")

            # 1. Aplicação do motor declarativo BOOST_RULES
            for rule in BOOST_RULES:
                rule_name = rule["name"]
                query_terms = rule.get("query_terms", [])
                source_contains = rule.get("source_contains", [])
                category_match = rule.get("category_match", [])
                boost_val = rule.get("boost", 0.0)

                # Verifica se a query do usuário combina com algum termo da regra
                if any(term in query_norm for term in query_terms):
                    # Verifica se o candidato pertence à fonte ou categoria desejada
                    match_source = any(sc in str(cand.source).lower() for sc in source_contains)
                    match_cat = cand.category in category_match

                    if match_source or match_cat:
                        cand.retrieval_score = round(cand.retrieval_score + boost_val, 4)
                        cand.add_explanation(f"Regra [{rule_name}]: +{boost_val:.2f} (termo de busca detectado)")

                    # Aplica penalizações associadas à regra
                    for pen in rule.get("penalty_rules", []):
                        pen_cat = pen.get("category")
                        pen_val = pen.get("penalty", 0.0)
                        if cand.category == pen_cat:
                            cand.retrieval_score = round(cand.retrieval_score + pen_val, 4)
                            cand.add_explanation(f"Penalidade [{rule_name}]: {pen_val:.2f} (categoria {pen_cat})")

            # 2. Regra de Localidade (Localidade exata mencionada)
            for loc in KNOWN_LOCALITIES:
                loc_norm = ''.join(c for c in unicodedata.normalize('NFKD', loc.lower()) if not unicodedata.combining(c))
                if loc_norm in query_norm:
                    content_norm = ''.join(c for c in unicodedata.normalize('NFKD', cand.content.lower()) if not unicodedata.combining(c))
                    title_norm = ''.join(c for c in unicodedata.normalize('NFKD', cand.title.lower()) if not unicodedata.combining(c))
                    if loc_norm in content_norm or loc_norm in title_norm:
                        b_val = BOOST_WEIGHTS["LOCALITY"]
                        cand.retrieval_score = round(cand.retrieval_score + b_val, 4)
                        cand.add_explanation(f"Boost de Localidade [{loc}]: +{b_val:.2f}")
                    break

            # 3. Penalização de Fontes Genéricas em Perguntas Quantitativas / Objetivas
            is_quantitative_query = any(q_term in query_norm for q_term in ["quantos", "quantas", "quais os", "quais as", "lista de", "onde fica", "endereco de"])
            if is_quantitative_query:
                generic_sources = ["lacunas_dados_resolvidas.md", "home.md", "index.md", "a_cidade.md", "ouvidoria_geral_info.md"]
                if any(gen_src in str(cand.source).lower() for gen_src in generic_sources):
                    cand.retrieval_score = round(cand.retrieval_score - 0.15, 4)
                    cand.add_explanation("Penalidade [Perguntas Fatuais]: -0.15 (fonte institucional genérica)")

            # 4. Trava de Segurança: Garante intervalo [0.0, 1.0]
            cand.retrieval_score = min(max(round(cand.retrieval_score, 4), 0.0), 1.0)

        # Ordena decrecente pelo retrieval_score
        candidates.sort(key=lambda x: x.retrieval_score, reverse=True)
        return candidates

    @staticmethod
    def evaluate_confidence(ranked_candidates: List[Candidate]) -> Tuple[str, float]:
        """
        Calcula o nível de confiança (ALTA, MÉDIA, BAIXA) para acionar o Confidence Gate:
        - ALTA  (>= 0.85): Resposta oficial direta com autoridade máxima.
        - MÉDIA (0.55 - 0.84): Resposta oficial + orientação para confirmação no portal/Colab.
        - BAIXA (< 0.55): Aciona Confidence Gate (Fallback Inteligente / Busca Externa ou Ouvidoria Geral).
        """
        if not ranked_candidates:
            return "BAIXA", 0.0

        top1 = ranked_candidates[0].retrieval_score
        top2 = ranked_candidates[1].retrieval_score if len(ranked_candidates) > 1 else 0.0

        if top1 >= 0.85 and (top1 - top2) >= 0.10:
            return "ALTA", top1
        elif top1 >= 0.55:
            return "MÉDIA", top1
        else:
            return "BAIXA", top1
