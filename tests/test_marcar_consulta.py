import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import DuqueIAAgent

agent = DuqueIAAgent()
session_id = "test_consulta_after_colab"

print("--- TURNO 1: Solicitação anterior que envolve barulho ---")
r1 = agent.process_query("como faço uma reclamação de barulho?", conversation_id=session_id)
print("Turno 1 Intent:", r1.get("intent_detected"))
print("Turno 1 Answer snippet:", r1.get("answer")[:150], "...\n")

print("--- TURNO 2: Pergunta da foto do usuário: 'marcar uma consulta?' ---")
r2 = agent.process_query("marcar uma consulta?", conversation_id=session_id)
print("Turno 2 Intent:", r2.get("intent_detected"))
print("Turno 2 Answer:\n", r2.get("answer"))
