import sys
import os
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agent.agent import DuqueIAAgent

def test_terreno():
    print("=== TESTE DA PERGUNTA: SOLICITAR LIMPEZA DE TERRENO ABANDONADO ===")
    agent = DuqueIAAgent()
    
    query = "como eu solicito uma limepza de um terreno abandonado ?"
    print(f"\nQuery enviado: '{query}'")
    
    t0 = time.time()
    resp_json = agent.respond(query, use_triage=True)
    t1 = time.time()
    
    data = json.loads(resp_json)
    print(f"\nTempo de Resposta: {(t1-t0)*1000:.2f} ms")
    print(f"Intenção Detectada: {data.get('intent_detected')}")
    print("\n--- RESPOSTA DA IA ---")
    print(data.get("answer"))
    print("\n--- FONTES RETORNADAS ---")
    print(data.get("sources"))

if __name__ == "__main__":
    test_terreno()
