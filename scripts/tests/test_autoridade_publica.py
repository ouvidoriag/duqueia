import os
import json
import sys
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

# Garante interceptação mock nos testes
os.environ["DUQUE_IA_TEST_MODE"] = "1"
from utils.mock_provider import install_mock_if_test_mode
install_mock_if_test_mode()

from agent.main import DuqueIAAgent

def run_autoridade_publica_tests():
    print("==========================================================")
    print("  SUÍTE DE TESTES: AUTORIDADES PÚBLICAS (DUQUE IA)        ")
    print("==========================================================")
    
    test_cases = [
        {
            "id": "AP01",
            "query": "Quem é o prefeito?",
            "expected_name": "Jonathas Monteiro Porto Neto (Netinho Reis)"
        },
        {
            "id": "AP02",
            "query": "Quem é o vice-prefeito de Duque de Caxias?",
            "expected_name": "Aline da Silva Santos (Aline do Mestre Lulinha)"
        },
        {
            "id": "AP03",
            "query": "Quem é o secretário de obras?",
            "expected_name": "Valber Rodrigues Januario"
        },
        {
            "id": "AP04",
            "query": "Quem dirige a secretaria de saúde?",
            "expected_name": "saúde" # Apenas verifica se encontra algo e a intenção é correta
        }
    ]
    
    agent = DuqueIAAgent()
    failures = 0
    
    for tc in test_cases:
        print(f"\n[{tc['id']}] Consulta: '{tc['query']}'")
        t0 = time.time()
        res_str = agent.respond(tc["query"], use_triage=True)
        latency = (time.time() - t0) * 1000
        
        try:
            res = json.loads(res_str)
            intent = res.get("intent_detected")
            answer = res.get("answer", "")
            sources = res.get("sources", [])
            
            print(f"  -> Intenção Detectada: {intent} | Latência: {latency:.1f}ms")
            print(f"  -> Resposta: {answer[:120]}...")
            print(f"  -> Fontes: {sources}")
            
            # Validações
            if intent != "AUTORIDADE_PUBLICA":
                print(f"  [FAIL] Intenção incorreta: esperada 'AUTORIDADE_PUBLICA', obtida '{intent}'")
                failures += 1
            elif tc["expected_name"] not in answer:
                # Caso especial para busca parcial de saúde
                if tc["id"] == "AP04" and len(answer) > 20:
                    print("  [PASS] Comportamento correto verificado.")
                else:
                    print(f"  [FAIL] Nome esperado '{tc['expected_name']}' não encontrado na resposta.")
                    failures += 1
            elif not sources:
                print("  [FAIL] Nenhuma fonte oficial retornada nos metadados.")
                failures += 1
            else:
                print("  [PASS] Comportamento correto verificado.")
                
        except Exception as e:
            print(f"  [ERROR] Falha ao testar ou parsear: {e}")
            failures += 1

    print("\n" + "=" * 50)
    if failures == 0:
        print("  🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print(f"  ❌ {failures} FALHAS ENCONTRADAS.")
        sys.exit(1)

if __name__ == "__main__":
    run_autoridade_publica_tests()
