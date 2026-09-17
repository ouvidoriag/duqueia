import re
import unicodedata
from typing import List, Tuple, Dict
from agent.candidate import Candidate

class ContextBuilder:
    """
    Formata e constrói o bloco de contexto oficial a ser injetado no Prompt da LLM (Gemini).
    Aplica fusão, deduplicação inter-fontes e limitação de orçamento de caracteres
    para evitar prompts inchados (ex: >4.000 tokens) e reduzir drasticamente a latência.
    """

    @staticmethod
    def _normalize_key(title: str, content: str) -> str:
        """Gera chave canônica para detectar duplicatas entre tabelas (ex: regras_negocio vs bancoduqueia)."""
        t_clean = re.sub(r'^(?:regra canônica:?|serviço:?)\s*', '', title or '', flags=re.IGNORECASE).strip().lower()
        t_clean = ''.join(c for c in unicodedata.normalize('NFKD', t_clean) if not unicodedata.combining(c))
        t_clean = re.sub(r'[^a-z0-9]', '', t_clean)[:40]
        return t_clean

    @staticmethod
    def build_context(candidates: List[Candidate], top_k: int = 4, max_context_chars: int = 6000) -> Tuple[str, List[str], List[Candidate]]:
        top_candidates = candidates[:max(top_k * 2, 8)]
        
        # 1. Deduplicação semântica inter-fontes (elimina cópias idênticas entre bancos diferentes)
        seen_keys = set()
        seen_prefixes = []
        deduped_candidates: List[Candidate] = []

        for cand in top_candidates:
            key = ContextBuilder._normalize_key(cand.title, cand.content)
            clean_content = cand.content.strip()
            prefix = clean_content[:150].lower()

            # Se a chave do título já existe ou o início do texto é idêntico a outro chunk, ignora cópia
            if key and key in seen_keys:
                continue
            if any(prefix in sp or sp in prefix for sp in seen_prefixes if len(prefix) > 80):
                continue

            seen_keys.add(key)
            seen_prefixes.append(prefix)
            deduped_candidates.append(cand)
            if len(deduped_candidates) >= top_k:
                break

        # 2. Aglutinação hierárquica por fonte (source)
        grouped_sources: Dict[str, Dict] = {}
        ordered_sources: List[str] = []

        for cand in deduped_candidates:
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
                new_content = cand.content.strip()
                existing_text = "\n".join(grouped_sources[src]["contents"])
                if new_content not in existing_text:
                    grouped_sources[src]["contents"].append(new_content)
                if cand.retrieval_score > grouped_sources[src]["max_score"]:
                    grouped_sources[src]["max_score"] = cand.retrieval_score

        # 3. Ordena fontes garantindo que Regras Canônicas relevantes fiquem no topo,
        # mas priorizando serviços com correspondência direta muito alta (>= 0.88)
        def source_sort_key(src_key):
            data = grouped_sources[src_key]
            cat = data.get("category", "").lower()
            is_regra = 1 if ("regra" in cat or src_key.startswith("regras_negocio") or src_key.startswith("bancoduqueia (regra_")) else 0
            score = data["max_score"]
            if is_regra and score >= 0.85:
                tier = 3
            elif score >= 0.88:
                tier = 2
            elif is_regra:
                tier = 1
            else:
                tier = 0
            return (tier, score)

        ordered_sources.sort(key=source_sort_key, reverse=True)

        context_blocks = []
        sources_used = []
        final_candidates = []
        current_chars = 0

        for src in ordered_sources:
            data = grouped_sources[src]
            merged_content = "\n".join(data["contents"])
            
            cat = data.get("category", "").lower()
            is_regra = "regra" in cat or src.startswith("regras_negocio") or src.startswith("bancoduqueia (regra_")
            
            if is_regra:
                header = f"--- [DIRETRIZ DE GOVERNANÇA MÁXIMA E OBRIGATÓRIA] FONTE: {src} | PRIORIDADE: MÁXIMA ---"
            else:
                header = f"--- FONTE: {src} | CATEGORIA: {data['category']} | SCORE: {data['max_score']:.2f} ---"

            block_text = f"{header}\n{merged_content}"
            
            # Limita orçamento total de caracteres para não explodir o prompt
            if current_chars + len(block_text) > max_context_chars and len(context_blocks) >= 2:
                # Se já temos pelo menos 2 blocos essenciais, interrompe para não inchar o contexto
                break

            context_blocks.append(block_text)
            sources_used.append(src)
            final_candidates.append(data["candidate_obj"])
            current_chars += len(block_text)

        context_text = "\n\n".join(context_blocks)
        return context_text, sources_used, final_candidates
