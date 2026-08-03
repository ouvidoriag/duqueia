"""
LLM Router — Roteador Exclusivo Gemini do DUQUE IA
===================================================
Gerencia a execução e fallback entre modelos do Google Gemini
utilizando rotação transparente entre 11 chaves de API ativas.

Modelos Suportados:
  - Gemini 2.5 Flash: modelo principal de alta capacidade (RAG e resposta)
  - Gemini 3.1 Flash Lite: modelo ultra-rápido de menor latência (triagem e fallback)
"""

import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.gemini_client import GeminiClient

# Instância singleton do cliente Gemini
_gemini_client: GeminiClient = None


def get_gemini() -> GeminiClient:
    """Retorna o cliente Gemini único compartilhado."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


class LLMRouter:
    """
    Roteador principal de LLMs do DUQUE IA (Exclusivo para o ecossistema Gemini).
    """

    def __init__(self):
        self.gemini = get_gemini()
        self._provider_stats = {
            "gemini_ok": 0,
            "gemini_fail": 0
        }

    def generate_response(
        self,
        prompt: str,
        system_instruction: str = None,
        model: str = None
    ) -> tuple:
        """
        Geração de texto com rotação automática de chaves do Gemini.
        Retorna: (texto, provedor_usado)
        """
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
                print(f"[LLMRouter] Gemini primário falhou: {str(e)[:80]}. Tentando modelo Lite de fallback...", file=sys.stderr)
                # Tenta fallback para o modelo lite
                try:
                    text = self.gemini.generate_response(
                        prompt,
                        system_instruction=system_instruction,
                        model="gemini-3.1-flash-lite"
                    )
                    self._provider_stats["gemini_ok"] += 1
                    return text, "gemini-3.1-flash-lite"
                except Exception as e2:
                    self._provider_stats["gemini_fail"] += 1
                    raise RuntimeError(f"Todos os modelos Gemini falharam na geração: {e2}")

        raise RuntimeError("Nenhuma chave Gemini disponível.")

    def generate_triage(
        self,
        prompt: str,
        system_instruction: str = None
    ) -> tuple:
        """
        Geração otimizada para triagem utilizando o modelo Lite (baixa latência) ou Flash primário.
        Retorna: (texto, provedor_usado)
        """
        if self.gemini.api_keys:
            try:
                text = self.gemini.generate_response(
                    prompt,
                    system_instruction=system_instruction,
                    model="gemini-3.1-flash-lite"
                )
                self._provider_stats["gemini_ok"] += 1
                return text, "gemini-3.1-flash-lite"
            except Exception as e:
                self._provider_stats["gemini_fail"] += 1
                print(f"[LLMRouter] Gemini Lite falhou na triagem: {str(e)[:80]}. Tentando modelo padrão...", file=sys.stderr)
                try:
                    text = self.gemini.generate_response(
                        prompt,
                        system_instruction=system_instruction
                    )
                    self._provider_stats["gemini_ok"] += 1
                    return text, "gemini"
                except Exception as e2:
                    self._provider_stats["gemini_fail"] += 1
                    raise RuntimeError(f"Falha na triagem com Gemini: {e2}")

        raise RuntimeError("Nenhum provedor Gemini disponível para triagem.")

    def generate_rag_response(
        self,
        prompt: str,
        system_instruction: str = None,
        previous_interaction_id: str = None
    ) -> tuple:
        """
        Geração para respostas RAG usando o modelo principal do Gemini.
        Retorna: (texto, novo_interaction_id, provedor_usado)
        """
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
                raise RuntimeError(f"Falha no Gemini RAG: {e}")

        raise RuntimeError("Nenhum provedor Gemini disponível para RAG.")

    def get_stats(self) -> dict:
        """Retorna estatísticas de uso do Gemini."""
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

