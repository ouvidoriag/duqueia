"""
collector.py — DUQUE IA
========================
Coletor centralizado de métricas de execução do grafo.
Armazena dados em JSONL para fácil análise pelo dashboard.
"""

import os
import json
import time

METRICS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "metrics", "requests.jsonl"))

class MetricsCollector:
    @staticmethod
    def record(state) -> None:
        """Registra as métricas finais de um request baseado no AgentState final."""
        # state é do tipo AgentState
        try:
            os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
            
            # Extrai info do AgentState (graph.py)
            nodes = getattr(state, "nodes_executed", [])
            resp = getattr(state, "response", {})
            triage = getattr(state, "triage_info", {})
            start = getattr(state, "start_time", time.time())
            
            # O último nó tem o tempo total desde o start
            total_time_ms = round((time.time() - start) * 1000, 1)
            
            # Extrai métricas internas da resposta se existirem
            inner_metrics = resp.get("metrics", {})
            
            # Determina o provedor utilizado dinamicamente
            provider = inner_metrics.get("provider_used")
            if not provider or provider == "unknown":
                if inner_metrics.get("llm_time_ms", 0) > 0:
                    from utils.gemini_client import GeminiClient
                    provider = "gemini" if len(GeminiClient().api_keys) > 0 else "mock"
                else:
                    provider = "system"
            
            record_data = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "conversation_id": getattr(state, "conversation_id", ""),
                "intent": resp.get("intent_detected", triage.get("intent", "UNKNOWN")),
                "total_time_ms": total_time_ms,
                "nodes": nodes,
                "llm_time_ms": inner_metrics.get("llm_time_ms", 0),
                "retrieval_time_ms": inner_metrics.get("retrieval_time_ms", 0),
                "tokens_used": inner_metrics.get("tokens_used", 0),
                "cost_usd": inner_metrics.get("cost_usd", 0.0),
                "provider_used": provider,
                "cache_hit": inner_metrics.get("cache_hit", False),
                "similarity": inner_metrics.get("similarity_score", 0.0),
                "hybrid_score": inner_metrics.get("hybrid_score", 0.0),
                "cross_score": inner_metrics.get("cross_score", 0.0),
                "error": len(getattr(state, "errors", [])) > 0
            }
            
            with open(METRICS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record_data, ensure_ascii=False) + "\n")
                
        except Exception as e:
            import sys
            print(f"[Metrics Error] Falha ao gravar métricas: {e}", file=sys.stderr)
