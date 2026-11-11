import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import DuqueIAAgent

agent = DuqueIAAgent()

queries = [
    "Quem é a vice-prefeita de Duque de Caxias?",
    "Quem é a vice prefeita?",
    "Quem é Aline do Aureo?",
    "Quem é Aline Ferreira Batista Ribeiro?"
]

print("==========================================================")
print("  TESTANDO CONSULTAS DA VICE-PREFEITA                    ")
print("==========================================================")

for q in queries:
    print(f"\n>>> Munícipe: {q}")
    res = agent.process_query(q, conversation_id="test_vice_session")
    print(f"Intent: {res.get('intent_detected')}")
    print(f"Resposta:\n{res.get('answer')}")
    assert "Aline Ferreira Batista Ribeiro" in res.get("answer") or "Aline do Aureo" in res.get("answer"), f"Falha na resposta: {res.get('answer')}"
    print("STATUS: ✅ APROVADO")

print("\nTodos os testes da Vice-Prefeita passaram com sucesso!")
