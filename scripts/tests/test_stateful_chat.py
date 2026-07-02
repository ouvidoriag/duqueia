import os
import sys
import json
from dotenv import load_dotenv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

load_dotenv()

output_file = r"C:\Users\501379.PMDC\.gemini\antigravity\brain\321430f0-96bf-4add-9f11-615b93494518\scratch\test_stateful_chat_output.txt"
sys.stdout = open(output_file, "w", encoding="utf-8", buffering=1)
sys.stderr = sys.stdout

from agent.main import DuqueIAAgent

def test_stateful_chat():
    print("==========================================================")
    print("  TESTANDO CONVERSA COM ESTADO (INTERACTIONS API)         ")
    print("==========================================================")
    sys.stdout.flush()
    
    agent = DuqueIAAgent()
    
    # Caso 1: Testando memória com RAG real
    print("\nTurno 1: Perguntando sobre os cursos da FUNDEC...")
    sys.stdout.flush()
    res1_str = agent.respond("Quais cursos a FUNDEC oferece?", use_triage=False)
    res1 = json.loads(res1_str)
    
    conv_id = res1.get("conversation_id")
    print(f"-> Resposta 1:\n{res1.get('answer')}")
    print(f"-> Novo Conversation ID: {conv_id}")
    sys.stdout.flush()
    
    if not conv_id:
        print("Erro: Nenhum ID de conversa foi gerado/retornado pelo servidor.")
        sys.exit(1)
        
    print("\nTurno 2: Perguntando o endereço com base no contexto anterior...")
    sys.stdout.flush()
    res2_str = agent.respond("Onde fica a sede dela?", use_triage=False, conversation_id=conv_id)
    res2 = json.loads(res2_str)
    
    answer2 = res2.get("answer", "")
    print(f"-> Resposta 2:\n{answer2}")
    sys.stdout.flush()
    
    # Esperado que o modelo lembre que "dela" se refere à FUNDEC e traga o endereço
    if "Brigadeiro" in answer2 or "Parque Duque" in answer2 or "2672" in answer2:
        print("\nSUCESSO: O assistente lembrou do contexto e encontrou a sede da FUNDEC!")
        print("==========================================================")
        print(" STATUS: PASS ✅")
        print("==========================================================")
    else:
        print("\nFALHA: O assistente não conseguiu correlacionar o pronome 'dela' à FUNDEC.")
        print("==========================================================")
        print(" STATUS: FAIL ❌")
        print("==========================================================")
        sys.exit(1)

if __name__ == "__main__":
    test_stateful_chat()
