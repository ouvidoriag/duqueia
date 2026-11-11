import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import DuqueIAAgent

agent = DuqueIAAgent()
session_id = f"test_mem_{uuid.uuid4().hex[:8]}"

print("==================================================================")
print("  TESTE DAS 3 CORREÇÕES: REDUNDÂNCIA, OFENSA/CLARIFICAÇÃO E MEMÓRIA")
print(f"  Sessão ID: {session_id}")
print("==================================================================")

# --- TURNO 1: Quem é Netinho Reis? ---
print("\n[TURNO 1] Munícipe: Quem é Netinho Reis?")
r1 = agent.process_query("Quem é Netinho Reis?", conversation_id=session_id)
ans1 = r1.get("answer", "")
intent1 = r1.get("intent_detected")
print(f"Intent Turno 1: {intent1}")
print(f"Resposta Turno 1:\n{ans1}\n")

# Validação Turno 1: Não deve repetir "Netinho Reis é o Prefeito de Duque de Caxias" duas vezes
count_prefeito = ans1.lower().count("é o prefeito de duque de caxias")
print(f"Contagem da frase 'é o prefeito de duque de caxias': {count_prefeito}")
assert count_prefeito <= 1, f"FALHA: Redundância detectada! Frase repetida {count_prefeito} vezes."
assert "Jonathas Monteiro Porto Neto" in ans1 or "Netinho Reis" in ans1, "FALHA: Prefeito não identificado."
print("STATUS TURNO 1: ✅ APROVADO (Zero redundância)")

# --- TURNO 2: Não entendi a resposta. Vai à merda. ---
print("\n[TURNO 2] Munícipe: Não entendi a resposta. Vai à merda.")
r2 = agent.process_query("Não entendi a resposta. Vai à merda.", conversation_id=session_id)
ans2 = r2.get("answer", "")
intent2 = r2.get("intent_detected")
print(f"Intent Turno 2: {intent2}")
print(f"Resposta Turno 2:\n{ans2}\n")

# Validação Turno 2: NÃO deve ser POSSIVEL_DENUNCIA nem abrir Ouvidoria/Colab
assert intent2 != "POSSIVEL_DENUNCIA", f"FALHA: Classificado indevidamente como POSSIVEL_DENUNCIA: {intent2}"
assert "ouvidoria loop prevented" not in intent2, "FALHA: Sequestrado pelo loop da Ouvidoria."
assert "desculpa" in ans2.lower() or "compreender" in ans2.lower() or "explicar" in ans2.lower(), "FALHA: Não pediu desculpas ou não reexplicou."
print("STATUS TURNO 2: ✅ APROVADO (Tratado com civilidade/clarificação, sem Ouvidoria)")

# --- TURNO 3: Sabe qual foi a primeira pergunta que eu fiz? ---
print("\n[TURNO 3] Munícipe: Sabe qual foi a primeira pergunta que eu fiz?")
r3 = agent.process_query("Sabe qual foi a primeira pergunta que eu fiz?", conversation_id=session_id)
ans3 = r3.get("answer", "")
intent3 = r3.get("intent_detected")
print(f"Intent Turno 3: {intent3}")
print(f"Resposta Turno 3:\n{ans3}\n")

# Validação Turno 3: Deve citar literalmente "Quem é Netinho Reis?"
assert intent3 == "MEMORIA_CONVERSACIONAL", f"FALHA: Intent não foi MEMORIA_CONVERSACIONAL: {intent3}"
assert "quem é netinho reis" in ans3.lower(), f"FALHA: Primeira pergunta não foi lembrada! Resposta: {ans3}"
assert "turno 1" in ans3.lower(), f"FALHA: Não citou o Turno 1! Resposta: {ans3}"
print("STATUS TURNO 3: ✅ APROVADO (Primeira pergunta recuperada literalmente do SQLite)")

print("\n🎉 TODAS AS 3 CORREÇÕES VALIDADAS COM SUCESSO!")

