import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class PermanentTelemetry:
    """
    Grava telemetria unificada por execução em metrics/telemetry/YYYY-MM-DDTHH-MM-SS.json
    e rastreia a métrica de Context Recall em 5 estágios.
    """

    @staticmethod
    def log_execution(
        query: str,
        retrieval_ms: float,
        ranking_ms: float,
        context_ms: float,
        llm_ms: float,
        candidates_found: int,
        top_candidates: List[Any],
        answer: str,
        sources_used: List[str],
        confidence_level: str
    ):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        telemetry_dir = os.path.join(base_dir, "metrics", "telemetry")
        os.makedirs(telemetry_dir, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")
        file_path = os.path.join(telemetry_dir, f"{timestamp_str}.json")

        top_candidates_meta = []
        for c in top_candidates:
            if hasattr(c, "to_dict"):
                top_candidates_meta.append(c.to_dict())
            else:
                top_candidates_meta.append(c)

        # Avaliação de Context Recall (5 Estágios)
        says_not_found = any(p in answer.lower() for p in ["não encontrei", "não possuo", "não há dados", "não constam", "não estão disponíveis"])
        has_sources = len(sources_used) > 0
        
        context_recall = {
            "db_has_data": has_sources,
            "retriever_found": candidates_found > 0,
            "entered_top_k": len(top_candidates) > 0,
            "injected_in_prompt": len(top_candidates) > 0,
            "utilized_by_llm": not says_not_found if has_sources else True,
            "stage_where_lost": "none" if not (has_sources and says_not_found) else "llm_generation"
        }

        data = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "latency_ms": {
                "retrieval": round(retrieval_ms, 2),
                "ranking": round(ranking_ms, 2),
                "context_builder": round(context_ms, 2),
                "llm": round(llm_ms, 2),
                "total": round(retrieval_ms + ranking_ms + context_ms + llm_ms, 2)
            },
            "candidates_found": candidates_found,
            "confidence_level": confidence_level,
            "sources_used": sources_used,
            "context_recall": context_recall,
            "top_candidates": top_candidates_meta[:5]
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Telemetry Error] Falha ao gravar arquivo de telemetria: {e}")

    @staticmethod
    def log_failure(query: str, intent: str = "UNKNOWN", top_source: str = "none", 
                    confidence: float = 0.0, expected_source: str = None, user_feedback: str = None):
        """Grava uma falha de busca na tabela retrieval_failures em data/db/telemetry.db para auditorias da Ouvidoria."""
        try:
            import sqlite3
            from config.settings import DATABASE_TELEMETRY
            if not os.path.exists(DATABASE_TELEMETRY):
                return
            conn = sqlite3.connect(DATABASE_TELEMETRY)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS retrieval_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    intent TEXT,
                    top_source TEXT,
                    expected_source TEXT,
                    user_feedback TEXT,
                    confidence REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                INSERT INTO retrieval_failures (query, intent, top_source, expected_source, user_feedback, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (query, intent, top_source, expected_source, user_feedback, confidence))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Telemetry Error] Falha ao registrar em retrieval_failures: {e}")

