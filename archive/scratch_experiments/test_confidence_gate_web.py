import os
import sys
import json
import time

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

from agent.agent import DuqueIAAgent

def test_confidence_gate_web():
    print("="*75)
    print("TESTANDO CONFIDENCE GATE + BUSCA EXTERNA CONTROLADA NO PORTAL OFICIAL")
    print("="*75)

    agent = DuqueIAAgent()

    # Pergunta propositalmente com informação não cadastrada no DB local (ou genérica)
    query = "Onde consultar o resultado do concurso público da Prefeitura de Duque de Caxias?"
    print(f"\n[PERGUNTA DO MUNICEPE]: \"{query}\"\n")

    t0 = time.time()
    res_str = agent.respond(query)
    lat_ms = (time.time() - t0) * 1000.0

    try:
        res = json.loads(res_str)
    except Exception:
        res = {"answer": res_str, "sources": [], "confidence": 0.50}

    print("="*75)
    print(f"RESPOSTA GERADA (Latência: {lat_ms:.0f}ms | Confiança: {res.get('confidence', 0.50)}):")
    print("="*75)
    print(res.get("answer"))
    print("\nFONTES UTILIZADAS:")
    for s in res.get("sources", []):
        print(f"  • {s}")
    print("="*75)

if __name__ == "__main__":
    test_confidence_gate_web()
