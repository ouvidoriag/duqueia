import sys
import os
import json

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.agent import DuqueIAAgent

def run_tests():
    agent = DuqueIAAgent()
    queries = [
        "gostaria de saber qual restaurantes tem em jardim primavera"
    ]

    print("=== TESTANDO BUSCA WEB E FALLBACK PÓS-LLM ===")
    for q in queries:
        print(f"\n--------------------------------------------------")
        print(f"QUERY: {q}")
        res_json = agent.respond(user_query=q)
        res = json.loads(res_json) if isinstance(res_json, str) else res_json
        print(f"INTENT: {res.get('intent_detected')}")
        print(f"CONFIDENCE: {res.get('confidence')}")
        print(f"SOURCES: {res.get('sources')}")
        print(f"ANSWER SNIPPET:\n{res.get('answer', '')[:300]}...")

if __name__ == "__main__":
    run_tests()
