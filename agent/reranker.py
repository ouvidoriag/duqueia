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
    Reranker de segundo estágio usando o Gemini Flash Lite como cross-encoder.

    Diferença em relação ao score híbrido do estágio 1:
      - Estágio 1 (retrieval.py): mede quão parecido o VETOR da query é com o
        vetor do chunk (similaridade de distribuição semântica).
      - Estágio 2 (este módulo): avalia o PAR (query, chunk) em conjunto e
        pergunta diretamente ao modelo: "esse trecho RESPONDE essa pergunta?"

    Parâmetros:
      gemini_client : instância do GeminiClient com chaves disponíveis
      max_candidates: quantos candidatos enviar ao cross-encoder (controle de custo)
      min_candidates: se houver menos candidatos que isso, pula o reranking
      score_weight   : peso do score do cross-encoder vs. score híbrido original
                       (0.0 = ignora cross-encoder, 1.0 = usa só cross-encoder)
    """

    def __init__(
        self,
        gemini_client,
        max_candidates: int = 8,
        min_candidates: int = 2,
        score_weight: float = 0.6,
    ):
        self.gemini_client = gemini_client
        self.max_candidates = max_candidates
        self.min_candidates = min_candidates
        self.score_weight = score_weight

    def _score_candidate(self, query: str, content: str, title: str) -> float:
        """
        Pede ao Gemini que avalie o par (query, chunk) e retorne um score 0.0-1.0.
        O modelo é instruído a responder APENAS com um número — sem explicações.
        """
        snippet = content[:500].strip()
        prompt = (
            "Você é um avaliador de relevância para um sistema RAG municipal.\n"
            "Sua única tarefa é avaliar se o trecho abaixo RESPONDE DIRETAMENTE "
            "à pergunta do munícipe.\n\n"
            f"Pergunta do munícipe: \"{query}\"\n\n"
            f"Título do trecho: \"{title}\"\n"
            f"Conteúdo do trecho:\n{snippet}\n\n"
            "Retorne SOMENTE um número decimal entre 0.0 e 1.0 representando "
            "a relevância direta:\n"
            "  1.0 = responde completamente e com precisão\n"
            "  0.5 = responde parcialmente ou de forma tangencial\n"
            "  0.0 = não responde à pergunta\n\n"
            "Score:"
        )
        try:
            raw = self.gemini_client.generate_response(
                prompt, model="gemini-3.1-flash-lite"
            ).strip()
            # Extrai o primeiro número decimal da resposta
            match = re.search(r"(\d+(?:\.\d+)?)", raw)
            if match:
                score = float(match.group(1))
                # Normaliza para 0.0-1.0 caso a LLM responda com "85" em vez de "0.85"
                if score > 1.0:
                    score = score / 100.0
                return min(max(score, 0.0), 1.0)
        except Exception as e:
            print(
                f"[CrossEncoder] Falha ao pontuar candidato '{title[:40]}': {e}",
                file=sys.stderr,
            )
        return 0.0

    def rerank(self, query: str, candidates: list) -> list:
        """
        Reordena a lista de candidatos com base no score cross-encoder.

        Estratégia de score final combinado:
          final = (score_weight × cross_score) + ((1 - score_weight) × hybrid_score)

        Isso garante que o cross-encoder tenha voz majoritária (60% por padrão)
        mas sem descartar completamente o score híbrido já calibrado (40%).

        Candidatos não avaliados (além de max_candidates) mantêm seu score original
        e são anexados ao final da lista já reordenada.
        """
        if len(candidates) < self.min_candidates:
            print(
                f"[CrossEncoder] {len(candidates)} candidato(s) — abaixo do mínimo "
                f"({self.min_candidates}). Pulando reranking.",
                file=sys.stderr,
            )
            return candidates

        # Divide em candidatos a avaliar e o restante (mantém score original)
        to_score = candidates[: self.max_candidates]
        remainder = candidates[self.max_candidates :]

        print(
            f"[CrossEncoder] Avaliando {len(to_score)} candidatos para query: "
            f'"{query[:60]}..."',
            file=sys.stderr,
        )

        scored = []
        for c in to_score:
            cross_score = self._score_candidate(
                query, c.get("content", ""), c.get("title", c.get("source", ""))
            )
            hybrid_score = c.get("similarity", c.get("semantic_score", 0.0))

            # Score final combinado
            final_score = round(
                self.score_weight * cross_score
                + (1.0 - self.score_weight) * hybrid_score,
                4,
            )

            c_copy = dict(c)
            c_copy["cross_encoder_score"] = cross_score
            c_copy["hybrid_score_original"] = hybrid_score
            c_copy["similarity"] = final_score  # sobrescreve para o pipeline usar

            scored.append(c_copy)
            print(
                f"  [{c.get('title', c.get('source', '?'))[:40]}] "
                f"hybrid={hybrid_score:.3f} cross={cross_score:.3f} final={final_score:.3f}",
                file=sys.stderr,
            )

        scored.sort(key=lambda x: x["similarity"], reverse=True)

        result = scored + remainder
        top_title = result[0].get("title", result[0].get("source", "?"))[:50]
        top_score = result[0].get("similarity", 0)
        print(
            f'[CrossEncoder] Reranking concluído. Top-1: "{top_title}" '
            f"(score={top_score:.3f})",
            file=sys.stderr,
        )
        return result
