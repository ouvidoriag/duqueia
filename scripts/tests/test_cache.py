import os
import sys
import json
import time

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from agent.agent import DuqueIAAgent
from agent.triage import get_cached_triage, save_triage_to_cache

def test_cache_triage():
    print("==========================================================")
    print("           TESTE DE CACHE PERSISTENTE DO SQLITE           ")
    print("==========================================================")
    
    agent = DuqueIAAgent()
    db_path = agent.db_path
    
    # Pergunta de teste única para evitar colisões
    test_query = f"Pergunta de teste de cache única {time.time()}"
    
    # 1. Primeira chamada: Deve consultar a LLM (ou retornar fallback se sem chaves, mas vamos simular inserindo no cache)
    print(f"1. Verificando ausência inicial da query no cache...")
    cached_before = get_cached_triage(db_path, test_query)
    assert cached_before is None, "A query não deveria estar no cache inicialmente!"
    print("  -> OK: Query não encontrada no cache.")
    
    # Simula gravação no cache
    mock_res = {
        "intent": "RAG_GERAL",
        "confidence": 0.85,
        "needs_clarification": False,
        "reason": "Test mock reason"
    }
    print(f"2. Gravando resultado no cache...")
    save_triage_to_cache(db_path, test_query, mock_res)
    
    # 2. Segunda chamada: Deve obter do cache
    print(f"3. Recuperando a query do cache...")
    cached_after = get_cached_triage(db_path, test_query)
    assert cached_after is not None, "A query deveria ser encontrada no cache!"
    assert cached_after["intent"] == "RAG_GERAL", f"Intenção esperada RAG_GERAL, obteve {cached_after['intent']}"
    assert cached_after["source"] == "SQLITE_CACHE", "O source do resultado deve ser 'SQLITE_CACHE'"
    
    print("  -> OK: Resultado recuperado com sucesso do cache SQLite!")
    print("\n   TESTE DE CACHE PASSOU ✅\n")

if __name__ == "__main__":
    test_cache_triage()
