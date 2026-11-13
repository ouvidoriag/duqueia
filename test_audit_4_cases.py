import sys
import json
import uuid
sys.path.append(r'C:\Users\501379.PMDC\Desktop\PROJETOS\PRODUCAO')
from agent.agent import DuqueIAAgent

agent = DuqueIAAgent()

print("=" * 60)
print("TESTE CASO 1: PROBLEMA NO POSTE (MULTI-TURNO)")
print("=" * 60)
conv_id_1 = str(uuid.uuid4())
# Turno 1: lâmpada
q1 = "A lâmpada do poste da minha rua está queimada, como faço para trocar?"
r1_raw = agent.respond(q1, conversation_id=conv_id_1)
r1 = json.loads(r1_raw)
print(f"Munícipe: {q1}")
print(f"IA Turno 1:\n{r1.get('answer')}\n")

# Turno 2: problema é no poste
q2 = "Mas o problema é no poste."
r2_raw = agent.respond(q2, conversation_id=conv_id_1)
r2 = json.loads(r2_raw)
print(f"Munícipe: {q2}")
print(f"IA Turno 2:\n{r2.get('answer')}\n")

print("=" * 60)
print("TESTE CASO 2: ITINERÁRIOS DE ÔNIBUS SEM BAIRRO (MULTI-TURNO)")
print("=" * 60)
conv_id_2 = str(uuid.uuid4())
# Turno 1: pergunta sem bairro
q_bus1 = "Quais são os itinerários e os horários dos ônibus municipais que atendem o meu bairro?"
r_bus1_raw = agent.respond(q_bus1, conversation_id=conv_id_2)
r_bus1 = json.loads(r_bus1_raw)
print(f"Munícipe: {q_bus1}")
print(f"IA Turno 1:\n{r_bus1.get('answer')}\n")

# Turno 2: cidadão informa o bairro
q_bus2 = "Pantanal"
r_bus2_raw = agent.respond(q_bus2, conversation_id=conv_id_2)
r_bus2 = json.loads(r_bus2_raw)
print(f"Munícipe: {q_bus2}")
print(f"IA Turno 2:\n{r_bus2.get('answer')}\n")

print("=" * 60)
print("TESTE CASO 3: TRANSPORTE ESCOLAR (LEGALIZAÇÃO E RENOVAÇÃO)")
print("=" * 60)
conv_id_3 = str(uuid.uuid4())
q_transp = "Como faço para legalizar ou renovar a permissão de transporte escolar em Duque de Caxias?"
r_transp_raw = agent.respond(q_transp, conversation_id=conv_id_3)
r_transp = json.loads(r_transp_raw)
print(f"Munícipe: {q_transp}")
print(f"IA Resposta:\n{r_transp.get('answer')}\n")

