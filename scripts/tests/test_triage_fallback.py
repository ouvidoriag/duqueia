import os
import sys
import json
import time

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from agent.triage import perform_triage
from agent.main import DuqueIAAgent

class MockBrokenGeminiClient:
    def __init__(self):
        self.api_keys = ["AIzaSyMockKey"]
        
    def generate_response(self, prompt, system_instruction=None, **kwargs):
        # Retorna texto que não contém JSON válido para simular falha de classificação / parse
        return "Olá! Eu acho que a pergunta é sobre iluminação de rua, mas não vou te dar um JSON."

def test_triage_fallback():
    print("==========================================================")
    print("         TESTE DE FALLBACK DA LLM DE TRIAGEM (SCHEMA)     ")
    print("==========================================================")
    
    agent = DuqueIAAgent()
    db_path = agent.db_path
    
    mock_client = MockBrokenGeminiClient()
    test_query = f"Uma query genérica de falha {time.time()}"
    
    print(f"Executando triagem com LLM que quebra o contrato de JSON...")
    res = perform_triage(db_path, test_query, mock_client)
    
    print("Resultado retornado pela triagem:")
    print(json.dumps(res, indent=2))
    
    assert res["intent"] == "RAG_GERAL", f"Intent esperado RAG_GERAL, obteve {res['intent']}"
    assert res["confidence"] == 0.0, f"Confidence esperada 0.0, obteve {res['confidence']}"
    assert res["needs_clarification"] is False, "needs_clarification deveria ser False no fallback permissivo"
    assert "Falha" in res["reason"] or "critical" in res["reason"].lower() or "llm" in res["reason"].lower()
    
    print("\n   TESTE DE FALLBACK PASSOU ✅\n")

if __name__ == "__main__":
    test_triage_fallback()
