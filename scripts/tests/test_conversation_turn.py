"""
Teste direto: simula 2 turnos de conversa com o agente para verificar se
o erro 400 (invalid argument) foi resolvido.
"""
import sys
import os
sys.path.append(os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()

from agent.main import DuqueIAAgent

agent = DuqueIAAgent()

print("=== Turno 1: Saudação ===")
resp1 = agent.respond("ola", use_triage=True)
import json
data1 = json.loads(resp1)
sess_id = data1.get("conversation_id")
print(f"  Intent: {data1.get('intent_detected')}")
print(f"  conversation_id: {sess_id}")
print(f"  Resposta: {data1.get('answer', '')[:80]}...")

print()
print("=== Turno 2: Pergunta real ===")
resp2 = agent.respond("onde fica o hospital moacyr?", use_triage=True, conversation_id=sess_id)
data2 = json.loads(resp2)
print(f"  Intent: {data2.get('intent_detected')}")
print(f"  Resposta: {data2.get('answer', '')[:120]}...")
print()
print("CONCLUÍDO - Sem erro 400!")
