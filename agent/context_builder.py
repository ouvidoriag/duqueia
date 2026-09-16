from typing import List, Tuple, Dict
from agent.candidate import Candidate

class ContextBuilder:
    """
    Formata e constrói o bloco de contexto oficial a ser injetado no Prompt da LLM (Gemini).
    Aplica fusão e aglutinação de chunks pertencentes à mesma fonte para evitar fragmentação de informação.
    """

    @staticmethod
    def build_context(candidates: List[Candidate], top_k: int = 5) -> Tuple[str, List[str], List[Candidate]]:
        top_candidates = candidates[:top_k]
        
        # Aglutinação hierárquica por fonte (source)
        grouped_sources: Dict[str, Dict] = {}
        ordered_sources: List[str] = []

        for cand in top_candidates:
            src = cand.source
            if src not in grouped_sources:
                grouped_sources[src] = {
                    "source": src,
                    "category": cand.category,
                    "max_score": cand.retrieval_score,
                    "contents": [cand.content.strip()],
                    "candidate_obj": cand
                }
                ordered_sources.append(src)
            else:
                # Se o chunk já é sub-trecho ou idêntico, evita duplicar o texto exato
                new_content = cand.content.strip()
                existing_text = "\n".join(grouped_sources[src]["contents"])
                if new_content not in existing_text:
                    grouped_sources[src]["contents"].append(new_content)
                if cand.retrieval_score > grouped_sources[src]["max_score"]:
                    grouped_sources[src]["max_score"] = cand.retrieval_score

        # Ordena fontes garantindo que Regras Canônicas fiquem no topo absoluto
        def source_sort_key(src_key):
            data = grouped_sources[src_key]
            cat = data.get("category", "").lower()
            is_regra = 1 if ("regra" in cat or src_key.startswith("regras_negocio") or src_key.startswith("bancoduqueia (regra_")) else 0
            return (is_regra, data["max_score"])

        ordered_sources.sort(key=source_sort_key, reverse=True)

        context_blocks = []
        sources_used = []
        final_candidates = []

        for src in ordered_sources:
            data = grouped_sources[src]
            sources_used.append(src)
            final_candidates.append(data["candidate_obj"])
            merged_content = "\n".join(data["contents"])
            
            cat = data.get("category", "").lower()
            is_regra = "regra" in cat or src.startswith("regras_negocio") or src.startswith("bancoduqueia (regra_")
            
            if is_regra:
                header = f"--- [DIRETRIZ DE GOVERNANÇA MÁXIMA E OBRIGATÓRIA] FONTE: {src} | PRIORIDADE: MÁXIMA ---"
            else:
                header = f"--- FONTE: {src} | CATEGORIA: {data['category']} | SCORE: {data['max_score']:.2f} ---"

            context_blocks.append(f"{header}\n{merged_content}")

        context_text = "\n\n".join(context_blocks)
        return context_text, sources_used, final_candidates
