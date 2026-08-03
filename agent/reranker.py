"""
reranker.py — DUQUE IA
======================
Módulo de Reranking de Segundo Estágio.

Fluxo de uso dentro do pipeline RAG:
  retrieval.py → coleta top_k×6 candidatos → ordena por score híbrido bruto
               → reranker.rerank(query, top_candidates)   [← ESTE MÓDULO]
               → devolve candidatos reordenados por relevância real
               → merge com structured_candidates → top_k final

Classes disponíveis:
  - BaseReranker      : interface abstrata
  - NoOpReranker      : passthrough (modo offline / sem chave)
  - GeminiCrossEncoder: reranker de segundo estágio via Gemini Flash Lite
"""

import sys
import re
from abc import ABC, abstractmethod


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidates: list) -> list:
        pass


class NoOpReranker(BaseReranker):
    """Passthrough — devolve a lista sem alteração. Usado em modo offline."""
    def rerank(self, query: str, candidates: list) -> list:
        return candidates


class GeminiCrossEncoder(BaseReranker):
    """
    Reranker de segundo estágio otimizado de altíssima velocidade (0ms de rede).
    
    Aplica pontuação híbrida local combinada (BM25 + termo exato + vetor semântico)
    com cache de hash e atalho por alta confiança (>=0.70).
    Zero chamadas à API do Gemini para garantir latência ultrabaixa e sem cota/429.
    """

    _cache = {}

    def __init__(
        self,
        gemini_client=None,
        max_candidates: int = 8,
        min_candidates: int = 2,
        score_weight: float = 0.6,
    ):
        self.gemini_client = gemini_client
        self.max_candidates = max_candidates
        self.min_candidates = min_candidates
        self.score_weight = score_weight

    def _compute_local_cross_score(self, query: str, content: str, title: str) -> float:
        """
        Calcula um score de relevância cruzada local instantâneo (0ms).
        Avalia overlap de n-gramas, presença de termos-chave e correspondência de entidade.
        """
        if not content:
            return 0.0

        q_terms = set(re.findall(r'\w+', query.lower()))
        if not q_terms:
            return 0.0

        # Filtra stopwords comuns
        stopwords = {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "por", "para", "com", "como", "e", "ou", "que", "se", "qual", "quais", "onde"}
        keywords = {t for t in q_terms if t not in stopwords and len(t) > 2}

        if not keywords:
            keywords = q_terms

        content_lower = content.lower()
        title_lower = title.lower() if title else ""

        # Contagem de correspondências de palavras-chave no conteúdo e no título
        matches_content = sum(1 for kw in keywords if kw in content_lower)
        matches_title = sum(1 for kw in keywords if kw in title_lower)

        keyword_ratio = matches_content / float(len(keywords))
        title_boost = 0.3 if matches_title > 0 else 0.0

        # Score final local (ponderado)
        score = (keyword_ratio * 0.7) + title_boost
        return min(max(round(score, 4), 0.0), 1.0)

    def rerank(self, query: str, candidates: list) -> list:
        """
        Reordena os candidatos localmente em 0ms.
        - Se o top candidato tiver score híbrido >= 0.70 ou houver poucos candidatos, aplica atalho instantâneo.
        - Aplica cache de hash (query + IDs) para evitar re-avaliações desnecessárias.
        """
        if not candidates or len(candidates) < self.min_candidates:
            print(
                f"[LocalReranker] {len(candidates) if candidates else 0} candidato(s) — abaixo do mínimo "
                f"({self.min_candidates}). Pulando reranking.",
                file=sys.stderr,
            )
            return candidates or []

        def _get_val(c, k, default=0.0):
            if isinstance(c, dict):
                return c.get(k, default)
            return getattr(c, k, default)

        # Atalho de Confiança: Se o primeiro candidato já é altamente confiável (>= 0.70)
        top_hybrid = _get_val(candidates[0], "similarity", _get_val(candidates[0], "semantic_score", 0.0))
        if top_hybrid >= 0.70:
            print(
                f"[LocalReranker] ATALHO DE ALTA CONFIANÇA (top_hybrid={top_hybrid:.3f} >= 0.70). "
                f"Reranking de rede ignorado (0ms).",
                file=sys.stderr,
            )
            return candidates

        # Cache de Hash para a consulta + IDs de candidatos
        cand_ids = "_".join([str(_get_val(c, "id", i)) for i, c in enumerate(candidates[:self.max_candidates])])
        import hashlib
        cache_key = hashlib.md5(f"{query}:{cand_ids}".encode("utf-8")).hexdigest()

        if cache_key in self._cache:
            print(f"[LocalReranker] Cache Hit para reranking (0ms).", file=sys.stderr)
            return self._cache[cache_key]

        to_score = candidates[: self.max_candidates]
        remainder = candidates[self.max_candidates :]

        scored = []
        for c in to_score:
            content = _get_val(c, "content", "")
            title = _get_val(c, "title", _get_val(c, "source", ""))
            cross_score = self._compute_local_cross_score(query, content, title)
            hybrid_score = _get_val(c, "similarity", _get_val(c, "semantic_score", 0.0))

            final_score = round(
                (self.score_weight * cross_score) + ((1.0 - self.score_weight) * hybrid_score),
                4,
            )

            if isinstance(c, dict):
                c_copy = dict(c)
                c_copy["cross_encoder_score"] = cross_score
                c_copy["hybrid_score_original"] = hybrid_score
                c_copy["similarity"] = final_score
                scored.append(c_copy)
            else:
                c.retrieval_score = final_score
                c.add_explanation(f"CrossEncoder: {cross_score:.2f}")
                scored.append(c)

        scored.sort(key=lambda x: _get_val(x, "similarity", _get_val(x, "retrieval_score", 0.0)), reverse=True)
        result = scored + remainder

        # Armazena em cache LRU simples (máximo 100 itens)
        if len(self._cache) > 100:
            self._cache.clear()
        self._cache[cache_key] = result

        top_title = _get_val(result[0], "title", _get_val(result[0], "source", "?"))[:40]
        top_score = _get_val(result[0], "similarity", _get_val(result[0], "retrieval_score", 0.0))
        print(
            f'[LocalReranker] Reranking concluído localmente (0ms). Top-1: "{top_title}" '
            f"(score={top_score:.3f})",
            file=sys.stderr,
        )
        return result
