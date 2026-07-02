"""
LLM Router - Roteador de provedores de LLM para o DUQUE IA
===========================================================
Gerencia a rotação automática entre provedores (Gemini, Groq) de forma
transparente. Quando um provedor falha ou esgota cota, tenta o próximo.

Estratégia:
  - Gemini 2.5 Flash: modelo principal (geração RAG e triagem)
  - Groq llama-3.1-8b-instant: fallback ultrarrápido e gratuito
  - Groq llama-3.3-70b-versatile: fallback de qualidade alta
"""

import os
import time
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.gemini_client import GeminiClient
from utils.groq_client import GroqClient

# Instâncias singleton (criadas uma vez, reutilizadas)
_gemini_client: GeminiClient = None
_groq_client: GroqClient = None


def get_gemini() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def get_groq() -> GroqClient:
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client


class LLMRouter:
    """
    Roteador principal de LLMs do DUQUE IA.
    
    Estratégias de uso:
      - generate_response(): usa Gemini primeiro, Groq como fallback
      - generate_triage(): usa Groq 8b (velocidade) primeiro, Gemini como fallback
      - generate_rag_response(): usa Gemini primeiro (qualidade RAG), Groq 70b como fallback
    """

    def __init__(self):
        self.gemini = get_gemini()
        self.groq = get_groq()
        self._provider_stats = {
            "gemini_ok": 0, "gemini_fail": 0,
            "groq_ok": 0, "groq_fail": 0
        }

    def generate_response(
        self,
        prompt: str,
        system_instruction: str = None,
        model: str = None
    ) -> tuple:
        """
        Geração de texto com fallback automático Gemini → Groq.
        Retorna: (texto, provedor_usado)
        """
        # Tenta Gemini primeiro
        if self.gemini.api_keys:
            try:
                text = self.gemini.generate_response(
                    prompt,
                    system_instruction=system_instruction,
                    model=model
                )
                self._provider_stats["gemini_ok"] += 1
                return text, "gemini"
            except Exception as e:
                self._provider_stats["gemini_fail"] += 1
                print(f"[LLMRouter] Gemini falhou: {str(e)[:80]}. Tentando Groq...", file=sys.stderr)

        # Fallback para Groq
        if self.groq.available:
            try:
                text = self.groq.generate_response(
                    prompt,
                    system_instruction=system_instruction,
                    prefer_quality=False
                )
                self._provider_stats["groq_ok"] += 1
                return text, "groq-8b"
            except Exception as e:
                self._provider_stats["groq_fail"] += 1
                print(f"[LLMRouter] Groq 8b falhou: {str(e)[:80]}. Tentando Groq 70b...", file=sys.stderr)
                try:
                    text = self.groq.generate_response(
                        prompt,
                        system_instruction=system_instruction,
                        prefer_quality=True
                    )
                    self._provider_stats["groq_ok"] += 1
                    return text, "groq-70b"
                except Exception as e2:
                    self._provider_stats["groq_fail"] += 1
                    print(f"[LLMRouter] Groq 70b falhou: {str(e2)[:80]}", file=sys.stderr)

        raise RuntimeError("Todos os provedores LLM falharam. Sistema em modo offline.")

    def generate_triage(
        self,
        prompt: str,
        system_instruction: str = None
    ) -> tuple:
        """
        Geração otimizada para triagem: Groq 8b (velocidade máxima) → Gemini.
        Retorna: (texto, provedor_usado)
        """
        # Tenta Groq primeiro (mais rápido para triagem)
        if self.groq.available:
            try:
                text = self.groq.generate_triage(prompt, system_instruction=system_instruction)
                self._provider_stats["groq_ok"] += 1
                return text, "groq-8b"
            except Exception as e:
                self._provider_stats["groq_fail"] += 1
                print(f"[LLMRouter] Groq falhou na triagem: {str(e)[:80]}. Tentando Gemini...", file=sys.stderr)

        # Fallback para Gemini
        if self.gemini.api_keys:
            try:
                text = self.gemini.generate_response(prompt, system_instruction=system_instruction)
                self._provider_stats["gemini_ok"] += 1
                return text, "gemini"
            except Exception as e:
                self._provider_stats["gemini_fail"] += 1
                raise RuntimeError(f"Todos os provedores falharam na triagem: {e}")

        raise RuntimeError("Nenhum provedor LLM disponível para triagem.")

    def generate_rag_response(
        self,
        prompt: str,
        system_instruction: str = None,
        previous_interaction_id: str = None
    ) -> tuple:
        """
        Geração para respostas RAG: Gemini (contexto nativo) → Groq 70b.
        Retorna: (texto, novo_interaction_id, provedor_usado)
        """
        # Gemini primeiro para RAG (suporte a interaction ID e contexto)
        if self.gemini.api_keys:
            try:
                text, new_id, model = self.gemini.generate_interaction(
                    prompt,
                    system_instruction=system_instruction,
                    previous_interaction_id=previous_interaction_id
                )
                self._provider_stats["gemini_ok"] += 1
                return text, new_id, f"gemini:{model}"
            except Exception as e:
                self._provider_stats["gemini_fail"] += 1
                print(f"[LLMRouter] Gemini RAG falhou: {str(e)[:80]}. Tentando Groq 70b...", file=sys.stderr)

        # Fallback Groq 70b (qualidade para RAG)
        if self.groq.available:
            try:
                text = self.groq.generate_response(
                    prompt,
                    system_instruction=system_instruction,
                    prefer_quality=True
                )
                self._provider_stats["groq_ok"] += 1
                return text, None, "groq:llama-3.3-70b-versatile"
            except Exception as e:
                self._provider_stats["groq_fail"] += 1
                # Último fallback: Groq 8b
                try:
                    text = self.groq.generate_response(
                        prompt,
                        system_instruction=system_instruction,
                        prefer_quality=False
                    )
                    self._provider_stats["groq_ok"] += 1
                    return text, None, "groq:llama-3.1-8b-instant"
                except Exception as e2:
                    self._provider_stats["groq_fail"] += 1

        raise RuntimeError("Todos os provedores LLM falharam no RAG. Sistema em modo offline.")

    def get_stats(self) -> dict:
        """Retorna estatísticas de uso dos provedores."""
        total = sum(self._provider_stats.values())
        return {
            **self._provider_stats,
            "total_requests": total
        }


# Instância global para uso em main.py e triage.py
_router: LLMRouter = None


def get_router() -> LLMRouter:
    """Retorna a instância singleton do roteador."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
