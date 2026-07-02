import os
import json
import sys
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from agent.main import DuqueIAAgent

def run_ambiguity_tests():
    print("==========================================================")
    print("  SUÍTE DE TESTES: TRATAMENTO DE AMBIGUIDADE (DUQUE IA)   ")
    print("==========================================================")
    
    test_cases = [
        {
            "id": "A01",
            "query": "Estou sem luz",
            "desc": "Concessionária Light vs Iluminação Pública"
        },
        {
            "id": "A02",
            "query": "Preciso trocar uma lâmpada",
            "desc": "Troca de lâmpada residencial vs Poste de rua (Zeladoria)"
        },
        {
            "id": "A03",
            "query": "Quero reclamar",
            "desc": "Reclamação genérica viga"
        },
        {
            "id": "A04",
            "query": "Trocar lâmpada do poste da minha rua",
            "desc": "Iluminação pública municipal (específico)"
        },
        {
            "id": "A05",
            "query": "Falta de luz no meu bairro inteiro",
            "desc": "Problema de distribuição elétrica (Light)"
        }
    ]
    
    agent = DuqueIAAgent()
    
    for tc in test_cases:
        print(f"\n[{tc['id']}] Consulta: '{tc['query']}' ({tc['desc']})")
        t0 = time.time()
        res_str = agent.respond(tc["query"], use_triage=True)
        latency = (time.time() - t0) * 1000
        
        try:
            res = json.loads(res_str)
            print(f"  -> Intenção: {res.get('intent_detected')} | Latência: {latency:.1f}ms")
            print(f"  -> Fontes: {res.get('sources')}")
            print(f"  -> Resposta:\n{res.get('answer')}")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            print(f"  Raw output: {res_str}")
        print("-" * 58)

if __name__ == "__main__":
    run_ambiguity_tests()
