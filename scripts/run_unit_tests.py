# -*- coding: utf-8 -*-
"""
run_unit_tests.py — DUQUE IA
============================
Runner determinístico de testes unitários e de integração local offline.
Garante execução rápida (<10 segundos), zero consumo de quota da API Gemini e 100% de confiabilidade.
Ativa DUQUE_IA_TEST_MODE=1 para utilizar o MockLLMProvider oficial.
"""

import os
import sys
import time
import glob
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT_DIR)

# Testes unitários e de componentes rápidos (cobertura total dos módulos do sistema)
FAST_COMPONENT_TESTS = [
    "test_agent_canonical_suite.py",
    "test_autoridade_publica.py",
    "test_bancoduqueia_retrieval.py",
    "test_barulho_multiturn.py",
    "test_cache.py",
    "test_completeness.py",
    "test_context_builder.py",
    "test_conversation_turn.py",
    "test_entity_resolver.py",
    "test_ontology.py",
    "test_ontology_benchmark.py",
    "test_possivel_denuncia.py",
    "test_priority_conflict.py",
    "test_rrf_fusion.py",
    "test_stateful_chat.py",
    "test_stateful_triage.py",
    "test_structured_db.py",
    "test_triage_fallback.py",
    "test_voice_integration.py"
]

def main():
    run_full = "--full" in sys.argv
    print("=" * 75, flush=True)
    print("       DUQUE IA — SUÍTE DE TESTES UNITÁRIOS DETERMINÍSTICOS (OFFLINE)", flush=True)
    print("=" * 75, flush=True)
    
    if run_full:
        all_tests = sorted(glob.glob("scripts/tests/test_*.py"))
        runnable_tests = [f for f in all_tests if "api_keys" not in f and "models_direct" not in f and "gemini_client_models" not in f]
    else:
        runnable_tests = [os.path.join("scripts", "tests", f) for f in FAST_COMPONENT_TESTS if os.path.exists(os.path.join("scripts", "tests", f))]
    
    print(f"Total de testes unitários selecionados: {len(runnable_tests)}", flush=True)
    print(f"Modo: {'COMPLETO / EXTENSIVO (--full)' if run_full else 'RÁPIDO / COMPONENTES (Padrão)'}\n", flush=True)
    
    env = dict(os.environ)
    env["DUQUE_IA_TEST_MODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    
    passed = 0
    failed = 0
    results = []
    
    total_start = time.time()
    
    for idx, test_path in enumerate(runnable_tests, 1):
        test_name = os.path.basename(test_path)
        print(f" [{idx:02d}/{len(runnable_tests):02d}] Executando {test_name:<36} ... ", end="", flush=True)
        t0 = time.time()
        try:
            res = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                timeout=25,
                cwd=ROOT_DIR,
                env=env
            )
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            
            if res.returncode == 0:
                passed += 1
                status = "PASS"
                err = ""
            else:
                failed += 1
                status = f"FAIL ({res.returncode})"
                err = res.stderr.decode('utf-8', errors='replace').strip()[:80].replace('\n', ' ')
        except subprocess.TimeoutExpired:
            failed += 1
            status = "TIMEOUT"
            err = "Tempo limite excedido (>25s)"
        except Exception as e:
            failed += 1
            status = "ERROR"
            err = str(e)[:80]
            
        results.append((test_name, status, elapsed_ms, err))
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {status:<10} ({elapsed_ms:>7.1f} ms)", flush=True)
        
    total_time = round(time.time() - total_start, 2)
    
    print("\n" + "=" * 75)
    print(f" RESUMO FINAL: {passed} PASS | {failed} FAIL | Tempo Total: {total_time}s")
    print("=" * 75)
    
    if failed > 0:
        print("\nFalhas detalhadas:")
        for name, status, ms, err in results:
            if status != "PASS":
                print(f" - {name} ({status}): {err}")
        sys.exit(1)
    else:
        print("\n🎉 TODOS OS TESTES DETERMINÍSTICOS PASSARAM COM SUCESSO!")
        sys.exit(0)

if __name__ == "__main__":
    main()
