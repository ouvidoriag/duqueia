import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.agent import DuqueIAAgent

def verify():
    agent = DuqueIAAgent()
    q = "temos aulas de saxofone na prefeitura ?"
    print("=== TESTANDO CONSULTA APÓS RE-INDEXAÇÃO DOS 372 SERVIÇOS ===")
    print(f"QUERY: {q}\n")
    res_str = agent.respond(user_query=q)
    res = json.loads(res_str) if isinstance(res_str, str) else res_str
    print("INTENT DETECTED:", res.get("intent_detected"))
    print("CONFIDENCE:", res.get("confidence"))
    print("SOURCES:", res.get("sources"))
    print("\nANSWER:\n", res.get("answer"))

if __name__ == "__main__":
    verify()
