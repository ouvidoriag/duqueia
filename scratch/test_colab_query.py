import os
import sys
import json

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent.agent import DuqueIAAgent

def test():
    agent = DuqueIAAgent()
    q = "quais serviços da prefeitura estão disponiveis no colab ?"
    print(f"Testando query: '{q}'")
    raw = agent.respond(q, use_triage=True)
    res = json.loads(raw)
    
    print("\n--- RESULTADO DA RESPOSTA ---")
    print(f"Fontes: {res.get('sources')}")
    print(f"Resposta:\n{res.get('answer')}")

if __name__ == "__main__":
    test()
