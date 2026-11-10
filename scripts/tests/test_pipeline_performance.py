import sys
import os
import time
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agent.agent import DuqueIAAgent

def test_performance():
    print("=== TESTE DE DESEMPENHO E LATÊNCIA DO PIPELINE RAG ===")
    agent = DuqueIAAgent()
    
    test_queries = [
        "Qual o horário de atendimento do CRAS?",
        "Como faço para pagar o IPTU?",
        "Qual o nome do prefeito de Duque de Caxias?"
    ]
    
    for q in test_queries:
        print(f"\n---> Testando pergunta: '{q}'")
        t0 = time.time()
        resp_json = agent.respond(q, use_triage=True)
        t1 = time.time()
        
        data = json.loads(resp_json)
        answer = data.get("answer", "")
        intent = data.get("intent_detected", "?")
        tot_ms = (t1 - t0) * 1000
        
        print(f"Intenção: {intent}")
        print(f"Tempo Total de Resposta: {tot_ms:.2f} ms ({t1-t0:.2f} s)")
        print(f"Resposta (resumo): {answer[:120]}...")

if __name__ == "__main__":
    test_performance()
