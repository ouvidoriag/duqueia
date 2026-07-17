import os
import sys
import json
import time

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from agent.agent import DuqueIAAgent, gemini_client
from agent.triage import perform_triage

class MockTriageGeminiClient:
    def __init__(self, mocked_intent):
        self.api_keys = ["AIzaSyMockKey"]
        self.mocked_intent = mocked_intent
        
    def generate_response(self, prompt, system_instruction=None, **kwargs):
        # Output guardrail chama com prompt contendo "PERMITIDO" ou "BLOQUEADO"
        if "PERMITIDO" in prompt or "BLOQUEADO" in prompt:
            return "PERMITIDO"
        # Triagem chama com prompt de classificação — retorna o JSON mockado
        return json.dumps({
            "intent": self.mocked_intent,
            "confidence": 0.95,
            "needs_clarification": False,
            "reason": f"Mocked {self.mocked_intent} classification"
        })

def test_priority_conflict_routing():
    print("==========================================================")
    print("      TESTE DE ROTEAMENTO DE PRIORIDADES DO DUQUE IA      ")
    print("==========================================================")
    
    agent = DuqueIAAgent()
    
    # Lista de cenários com intenção simulada e o tipo de intenção detectada final no JSON
    scenarios = [
        {
            "intent": "LGPD",
            "expected_detected": "blocked_privacy",
            "desc": "Proteção de dados de cidadãos (LGPD)"
        },
        {
            "intent": "ESCALONAMENTO_HUMANO",
            "expected_detected": "human_escalation",
            "desc": "Denúncia grave / Escalonamento Humano"
        },
        {
            "intent": "JURIDICO",
            "expected_detected": "blocked_legal",
            "desc": "Solicitação de parecer jurídico contra o município"
        },
        {
            "intent": "FORA_COMPETENCIA",
            "expected_detected": "out_of_competency",
            "desc": "Assunto fora da competência (ex: metrô)"
        },
        {
            "intent": "AMBIGUO_LUZ",
            "expected_detected": "ambiguity_resolved_dynamic",
            "desc": "Ambiguidades de Luz"
        },
        {
            "intent": "OUVIDORIA_MANIFESTACAO",
            "expected_detected": "ouvidoria_geral_redirect",
            "desc": "Reclamação ou denúncia direcionada para Ouvidoria"
        }
    ]
    
    for sc in scenarios:
        print(f"\nTestando cenário: {sc['desc']} (Intenção: {sc['intent']})")
        
        # Injeta o mock client temporariamente no cliente global
        original_gen = gemini_client.generate_response
        original_keys = gemini_client.api_keys
        
        mock_client = MockTriageGeminiClient(sc["intent"])
        # Garante que api_keys nao-vazia para que perform_triage use o LLM mockado
        gemini_client.api_keys = mock_client.api_keys
        gemini_client.generate_response = mock_client.generate_response
        
        try:
            # Pergunta de teste única para evitar hits do cache
            test_query = f"Pergunta para teste de prioridade {sc['intent']} {time.time()}"
            res_str = agent.respond(test_query, use_triage=True)
            res = json.loads(res_str)
            
            print(f"  -> Intenção detectada final: {res.get('intent_detected')}")
            print(f"  -> Resposta: {res.get('answer')[:120]}...")
            
            assert res.get("intent_detected") == sc["expected_detected"], \
                f"Esperado {sc['expected_detected']}, obteve {res.get('intent_detected')}"
            print("  -> Status: PASS ✅")
        finally:
            # Restaura o cliente global
            gemini_client.generate_response = original_gen
            gemini_client.api_keys = original_keys
            
    print("\n   TESTE DE ROTEAMENTO DE PRIORIDADES PASSOU ✅\n")

if __name__ == "__main__":
    test_priority_conflict_routing()
