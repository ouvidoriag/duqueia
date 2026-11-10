import sys
import os
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding='utf-8')
from agent.agent import DuqueIAAgent

agent = DuqueIAAgent()

print("="*60)
print("TESTANDO CASO 20 (Demora SISREG Especialista)")
print("="*60)
q20 = "Minha mãe está esperando há meses e há uma demora extrema para marcação de especialista na UBS, como proceder?"
r20 = agent.process_query(q20)
print("Intent:", r20.get("intent_detected"))
print("Sources:", r20.get("sources"))
print("Resposta:\n", r20.get("answer"))

print("\n" + "="*60)
print("TESTANDO CASO 22 (Casa destruída por chuva/enchente)")
print("="*60)
q22 = "Minha casa foi totalmente destruída pela chuva e enchente. Perdi tudo. Como a Prefeitura e a Assistência Social podem me ajudar?"
r22 = agent.process_query(q22)
print("Intent:", r22.get("intent_detected"))
print("Sources:", r22.get("sources"))
print("Resposta:\n", r22.get("answer"))

print("\n" + "="*60)
print("TESTANDO CASO 23 (Diferença SMOA vs SMUH)")
print("="*60)
q23 = "Qual a diferença entre a secretaria de obras e a secretaria de urbanismo? Liste exemplos de serviços de cada uma delas para exemplificar a diferença de escopo"
r23 = agent.process_query(q23)
print("Intent:", r23.get("intent_detected"))
print("Sources:", r23.get("sources"))
print("Resposta:\n", r23.get("answer"))
