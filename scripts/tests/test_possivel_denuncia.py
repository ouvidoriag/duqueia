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

def run_possivel_denuncia_tests():
    print("==========================================================")
    print("  SUÍTE DE TESTES: POSSÍVEL DENÚNCIA (DUQUE IA)          ")
    print("==========================================================")
    
    test_cases = [
        {
            "id": "PD01",
            "query": "o rildo me xingou",
            "desc": "Relato específico com pessoa identificada e verbo agressivo"
        },
        {
            "id": "PD02",
            "query": "me trataram muito mal no atendimento",
            "desc": "Relato de mau tratamento"
        },
        {
            "id": "PD03",
            "query": "fui mal atendido na secretaria",
            "desc": "Relato de mau atendimento"
        },
        {
            "id": "PD04",
            "query": "um funcionario da prefeitura foi grosseiro comigo",
            "desc": "Relato de atitude grosseira"
        }
    ]
    
    agent = DuqueIAAgent()
    failures = 0
    
    for tc in test_cases:
        print(f"\n[{tc['id']}] Consulta: '{tc['query']}' ({tc['desc']})")
        t0 = time.time()
        res_str = agent.respond(tc["query"], use_triage=True)
        latency = (time.time() - t0) * 1000
        
        try:
            res = json.loads(res_str)
            intent = res.get("intent_detected")
            answer = res.get("answer", "")
            
            print(f"  -> Intenção Detectada: {intent} | Latência: {latency:.1f}ms")
            print(f"  -> Resposta: {answer[:120]}...")
            
            # Validações
            if "possivel_denuncia" not in intent.lower() and "ouvidoria" not in intent.lower():
                print(f"  [FAIL] Intenção inesperada para consulta '{tc['query']}': {intent}")
                failures += 1
            elif "ouvidoria" not in answer.lower() and "colab" not in answer.lower():
                print("  [FAIL] Resposta não contém direcionamento para a Ouvidoria ou Colab.")
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
    run_possivel_denuncia_tests()
