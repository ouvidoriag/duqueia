import os
import sys
import json
import time
import io

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = sys.stdout

from agent.main import DuqueIAAgent

def test_stateful_triage():
    print("==========================================================")
    print("  TESTANDO TRIAGEM COM ESTADO (ILUMINAÇÃO PÚBLICA)       ")
    print("==========================================================")
    
    agent = DuqueIAAgent()
    
    # 1. Turno 1
    query1 = "eu gostaria de informar uma rua sem luz"
    print(f"\nTurno 1: '{query1}'")
    res1_str = agent.respond(query1, use_triage=True)
    res1 = json.loads(res1_str)
    
    conv_id = res1.get("conversation_id")
    print(f"-> Intenção 1: {res1.get('intent_detected')}")
    print(f"-> Resposta 1:\n{res1.get('answer')}")
    print(f"-> Conv ID: {conv_id}")
    
    # 2. Turno 2
    query2 = "na verdade só dois postes apenas que está sem luz"
    print(f"\nTurno 2: '{query2}'")
    res2_str = agent.respond(query2, use_triage=True, conversation_id=conv_id)
    res2 = json.loads(res2_str)
    
    print(f"-> Intenção 2: {res2.get('intent_detected')}")
    print(f"-> Resposta 2:\n{res2.get('answer')}")
    
    # Validações
    intent1 = res1.get("triage_info", {}).get("intent")
    intent2 = res2.get("triage_info", {}).get("intent")
    
    print("\n----------------------------------------------------------")
    print(f"Intenção no Turno 1: {intent1} (Esperado: AMBIGUO_LUZ)")
    print(f"Intenção no Turno 2: {intent2} (Esperado: RAG_GERAL)")
    print("----------------------------------------------------------")
    
    if intent1 == "AMBIGUO_LUZ" and intent2 == "RAG_GERAL":
        print("\nSUCESSO: A memória conversacional resolveu a ambiguidade de iluminação! ✅")
    else:
        print("\nFALHA: A ambiguidade não foi resolvida corretamente no Turno 2. ❌")
        
if __name__ == "__main__":
    test_stateful_triage()
