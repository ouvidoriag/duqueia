import os
import re
import sqlite3
import unicodedata
from typing import List, Tuple, Dict, Optional
from agent.candidate import Candidate
from config.settings import DATABASE_VECTOR

class ContextBuilder:
    """
    Formata e constrói o bloco de contexto oficial a ser injetado no Prompt da LLM (Gemini).
    Aplica fusão, deduplicação inter-fontes, expansão hierárquica de chunks irmãos (sibling chunks)
    e limitação de orçamento de caracteres para garantir respostas factual e concisas sem estourar tokens.
    """

    @staticmethod
    def clean_metadata_and_ocr(text: str) -> str:
        """Limpa identificadores internos de OCR, números de arquivo e metadados de escaneamento."""
        if not text:
            return ""
        t = re.sub(r'\s*\*?\(OCR[^\)]*\)\*?', '', text, flags=re.IGNORECASE)
        t = re.sub(r'###\s*Página\s*\d+\s*\*?\(OCR[^\)]*\)\*?', '', t, flags=re.IGNORECASE)
        t = re.sub(r'\b\d{2}_([A-Za-z0-9_]+)', lambda m: m.group(1).replace('_', ' '), t)
        t = re.sub(r'\.(?:pdf|docx?|xlsx?|json|csv|md)\b', '', t, flags=re.IGNORECASE)
        return t.strip()

    @staticmethod
    def _normalize_key(title: str, content: str, source: str = "") -> str:
        """Gera chave canônica para detectar duplicatas entre tabelas (ex: regras_negocio vs bancoduqueia)."""
        t_clean = re.sub(r'^(?:regra canônica:?|serviço:?)\s*', '', title or '', flags=re.IGNORECASE).strip().lower()
        t_clean = ''.join(c for c in unicodedata.normalize('NFKD', t_clean) if not unicodedata.combining(c))
        base_key = re.sub(r'[^a-z0-9]', '', t_clean)[:40]
        # Preserva distinção de partes em chunks fracionados (_p1 / _p2 / parte 1 / parte 2)
        s_lower = (source or "").lower()
        t_lower = (title or "").lower()
        if "_p1" in s_lower or "parte 1" in t_lower:
            base_key += "_p1"
        elif "_p2" in s_lower or "parte 2" in t_lower:
            base_key += "_p2"
        return base_key

    @staticmethod
    def _fetch_sibling_chunk(source: str) -> Optional[Tuple[str, str]]:
        """
        Busca o chunk irmão complementar de um serviço fracionado (ex: servico_00086_p1 -> servico_00086_p2).
        Retorna tupla (sibling_source, sibling_content) ou None.
        """
        sibling_source = None
        if source.endswith("_p1"):
            sibling_source = source[:-3] + "_p2"
        elif source.endswith("_p2"):
            sibling_source = source[:-3] + "_p1"
            
        if not sibling_source:
            return None

        try:
            if not os.path.exists(DATABASE_VECTOR):
                return None
            conn = sqlite3.connect(DATABASE_VECTOR, timeout=2.0)
            cur = conn.cursor()
            cur.execute("SELECT content FROM duque_ia_chunks WHERE source = ? LIMIT 1", (sibling_source,))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return sibling_source, row[0].strip()
        except Exception:
            pass
        return None

    @staticmethod
    def build_context(candidates: List[Candidate], top_k: int = 4, max_context_chars: int = 6000) -> Tuple[str, List[str], List[Candidate]]:
        top_candidates = candidates[:max(top_k * 2, 8)]
        
        # 1. Deduplicação semântica inter-fontes (elimina cópias idênticas entre bancos diferentes)
        seen_keys = set()
        seen_prefixes = []
        deduped_candidates: List[Candidate] = []

        for cand in top_candidates:
            key = ContextBuilder._normalize_key(cand.title, cand.content, cand.source)
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

        # 2. Aglutinação hierárquica por fonte (source) e agrupamento de serviços
        grouped_sources: Dict[str, Dict] = {}
        ordered_sources: List[str] = []

        for cand in deduped_candidates:
            src = cand.source
            base_src = re.sub(r'_p[12]$', '', src)
            is_split_service = (base_src != src)

            if base_src not in grouped_sources:
                grouped_sources[base_src] = {
                    "source": base_src if is_split_service else src,
                    "original_sources": [src],
                    "category": cand.category,
                    "max_score": cand.retrieval_score,
                    "contents": [cand.content.strip()],
                    "candidate_obj": cand
                }
                ordered_sources.append(base_src)
            else:
                new_content = cand.content.strip()
                existing_text = "\n".join(grouped_sources[base_src]["contents"])
                if new_content not in existing_text:
                    if src.endswith("_p1"):
                        grouped_sources[base_src]["contents"].insert(0, new_content)
                    else:
                        grouped_sources[base_src]["contents"].append(new_content)
                if src not in grouped_sources[base_src]["original_sources"]:
                    grouped_sources[base_src]["original_sources"].append(src)
                if cand.retrieval_score > grouped_sources[base_src]["max_score"]:
                    grouped_sources[base_src]["max_score"] = cand.retrieval_score

        # 2.1 Expansão ativa de chunks irmãos (Sibling Expansion):
        # Se um serviço fracionado estiver no contexto com score relevante (>= 0.65), anexa a outra parte
        for base_src in list(ordered_sources):
            entry = grouped_sources[base_src]
            orig_srcs = entry.get("original_sources", [])
            if len(orig_srcs) == 1 and entry["max_score"] >= 0.65:
                single_src = orig_srcs[0]
                sibling_data = ContextBuilder._fetch_sibling_chunk(single_src)
                if sibling_data:
                    sib_src, sib_content = sibling_data
                    if sib_src not in orig_srcs:
                        est_len = sum(len(c) for c in entry["contents"]) + len(sib_content)
                        if est_len <= max_context_chars:
                            if single_src.endswith("_p1"):
                                entry["contents"].append(sib_content)
                            else:
                                entry["contents"].insert(0, sib_content)
                            entry["original_sources"].append(sib_src)
                            entry["source"] = f"{base_src} (Partes 1 e 2 Consolidadas)"

        # 3. Ordena fontes garantindo que Regras Canônicas relevantes fiquem no topo,
        # mas priorizando serviços com correspondência direta muito alta (>= 0.88)
        def source_sort_key(src_key):
            data = grouped_sources[src_key]
            cat = data.get("category", "").lower()
            src_str = str(data.get("source", "")).lower()
            is_regra = 1 if ("regra" in cat or src_str.startswith("regras_negocio") or src_str.startswith("bancoduqueia (regra_")) else 0
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
            merged_content = ContextBuilder.clean_metadata_and_ocr("\n\n".join(data["contents"]))
            
            cat = data.get("category", "").lower()
            src_name = ContextBuilder.clean_metadata_and_ocr(str(data["source"]))
            is_regra = "regra" in cat or src_name.startswith("regras_negocio") or src_name.startswith("bancoduqueia (regra_")
            
            if is_regra:
                header = f"--- [DIRETRIZ DE GOVERNANÇA MÁXIMA E OBRIGATÓRIA] FONTE: {src_name} | PRIORIDADE: MÁXIMA ---"
            else:
                header = f"--- FONTE: {src_name} | CATEGORIA: {data['category']} | SCORE: {data['max_score']:.2f} ---"

            block_text = f"{header}\n{merged_content}"
            
            # Limita orçamento total de caracteres para não explodir o prompt
            if current_chars + len(block_text) > max_context_chars and len(context_blocks) >= 2:
                # Se já temos pelo menos 2 blocos essenciais, interrompe para não inchar o contexto
                break

            context_blocks.append(block_text)
            sources_used.append(src_name)
            final_candidates.append(data["candidate_obj"])
            current_chars += len(block_text)

        context_text = "\n\n".join(context_blocks)
        return context_text, sources_used, final_candidates
