import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding='utf-8')

from agent.agent import DuqueIAAgent

json_path = os.path.join("scripts", "results_23_casos_novas_respostas.json")
with open(json_path, "r", encoding="utf-8") as f:
    cases = json.load(f)

agent = DuqueIAAgent()

# Atualizar apenas casos 20, 22, 23 (ou todos os que tiveram melhorias de código)
target_ids = [20, 22, 23]

for c in cases:
    cid = c["id"]
    if cid in target_ids:
        print(f"Executando atualização para Caso {cid:02d}: {c['titulo']}...")
        q = c["pergunta"]
        t0 = time.time()
        res = agent.process_query(q)
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        
        c["nova_resposta"] = {
            "answer": res.get("answer", ""),
            "confidence": res.get("confidence", 0.95),
            "intent_detected": res.get("intent_detected", "general"),
            "sources": res.get("sources", []),
            "elapsed_ms": elapsed_ms
        }
        print(f" -> Sucesso! Intent: {res.get('intent_detected')}, Tempo: {elapsed_ms}ms")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(cases, f, ensure_ascii=False, indent=2)

print("\nArquivo scripts/results_23_casos_novas_respostas.json atualizado com sucesso!")
