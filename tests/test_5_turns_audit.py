import os
import sys
sys.path.insert(0, os.path.abspath("."))

import json
from agent.agent import DuqueIAAgent

def run_test():
    agent = DuqueIAAgent()
    session_id = 'test_session_audit_1'

    queries = [
        "Onde posso tomar vacina?",
        "Como consultar meu IPTU?",
        "Qual o telefone da Ouvidoria?",
        "Qual a função da Secretaria de Obras?",
        "Quero reclamar de um buraco na rua."
    ]

    for idx, q in enumerate(queries, 1):
        print(f"\n=======================================================")
        print(f"TURNO {idx}: \"{q}\"")
        print(f"=======================================================")
        
        hist_before = list(DuqueIAAgent._history.get(session_id, []))
        print(f"Histórico antes ({len(hist_before)} msgs): {hist_before}")
        
        res_str = agent.respond(q, conversation_id=session_id)
        res = json.loads(res_str)
        
        print(f"Intent detectada: {res.get('intent_detected')}")
        print(f"Handler / nós executados: {res.get('_graph', {}).get('nodes_executed')}")
        print(f"Resposta:\n{res.get('answer', '')}")
        
        sess = DuqueIAAgent._session_state.get(session_id, {})
        print(f"Session state pós-execução: {sess}")

if __name__ == "__main__":
    run_test()
