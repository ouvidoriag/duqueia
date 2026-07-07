"""
DUQUE IA - ORQUESTRADOR DE TODOS OS TESTES
Executa cada script de teste, captura saida e gera relatorio final.
"""
import os
import sys
import io
import subprocess
import time
import json
from datetime import datetime

# Forca saida UTF-8 no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON = sys.executable

TESTS = [
    # (label, arquivo relativo ao ROOT, args extras)
    ("test_api_keys",           "scripts/tests/test_api_keys.py",           []),
    ("test_models",             "scripts/tests/test_models.py",             []),
    ("test_cache",              "scripts/tests/test_cache.py",              []),
    ("test_triage_fallback",    "scripts/tests/test_triage_fallback.py",    []),
    ("test_priority_conflict",  "scripts/tests/test_priority_conflict.py",  []),
    ("test_structured_db",      "scripts/tests/test_structured_db.py",      []),
    ("test_ambiguity",          "scripts/tests/test_ambiguity.py",          []),
    ("test_stateful_triage",    "scripts/tests/test_stateful_triage.py",    []),
    ("test_questionnaires",     "scripts/tests/test_questionnaires.py",     [], 300),
    ("test_ask_batch",          "scripts/tests/test_ask.py",                ["--batch"], 300),
    ("test_groq",               "scripts/test_groq.py",                     []),
    ("test_openai",             "scripts/test_openai.py",                   []),
    ("test_llm_router",         "scripts/test_llm_router.py",               []),
    ("test_models_direct",      "scripts/test_models_direct.py",            []),
    ("test_retrieval_relevance","scripts/tests/test_retrieval_relevance.py",[]),
    ("test_conversation_turn",  "scripts/test_conversation_turn.py",        [], 120),
]

REPORT_PATH = os.path.join(ROOT, "metrics", "test_suite_report.json")
os.makedirs(os.path.join(ROOT, "metrics"), exist_ok=True)

results = []

print("\n" + "=" * 70)
print("     DUQUE IA — RODANDO TODOS OS TESTES")
print(f"     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

for entry in TESTS:
    label, script_rel, extra_args = entry[0], entry[1], entry[2]
    timeout_s = entry[3] if len(entry) > 3 else 120
    script_path = os.path.join(ROOT, script_rel)
    if not os.path.exists(script_path):
        print(f"\n[SKIP] {label}: arquivo não encontrado ({script_rel})")
        results.append({"test": label, "status": "SKIP", "reason": "arquivo não encontrado", "output": "", "duration_ms": 0})
        continue

    print(f"\n{'-'*70}")
    print(f"[RUN] {label}")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [PYTHON, script_path] + extra_args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        elapsed = (time.time() - t0) * 1000
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        rc = proc.returncode

        # Determina status
        combined = (stdout + stderr).lower()
        if rc == 0 and ("erro" not in combined or "pass" in combined or "✅" in combined):
            status = "PASS"
        elif rc != 0:
            status = "FAIL"
        else:
            # rc=0 mas pode ter warnings
            status = "PASS" if "❌" not in (stdout + stderr) else "WARN"

        print(f"  Status : {status}  |  Duração: {elapsed:.0f}ms  |  RC: {rc}")
        if stdout:
            for line in stdout.split("\n")[-20:]:  # últimas 20 linhas
                print(f"  | {line}")
        if stderr and status != "PASS":
            print(f"  STDERR: {stderr[:500]}")

        results.append({
            "test": label,
            "status": status,
            "return_code": rc,
            "duration_ms": round(elapsed),
            "output": stdout[-3000:] if len(stdout) > 3000 else stdout,
            "stderr": stderr[-1000:] if len(stderr) > 1000 else stderr,
        })

    except subprocess.TimeoutExpired:
        elapsed = (time.time() - t0) * 1000
        print(f"  ⏰ TIMEOUT após {elapsed:.0f}ms")
        results.append({"test": label, "status": "TIMEOUT", "duration_ms": round(elapsed), "output": "", "stderr": ""})
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  ❌ ERRO ao executar: {e}")
        results.append({"test": label, "status": "ERROR", "reason": str(e), "duration_ms": round(elapsed), "output": "", "stderr": ""})

# Salva JSON
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, ensure_ascii=False, indent=2)

# Resumo final
print("\n" + "=" * 70)
print("  RESUMO FINAL DA SUÍTE DE TESTES")
print("=" * 70)
totais = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0, "TIMEOUT": 0, "ERROR": 0}
for r in results:
    st = r["status"]
    totais[st] = totais.get(st, 0) + 1
    icon = "✅" if st == "PASS" else ("⚠️" if st == "WARN" else "❌")
    print(f"  {icon}  {r['test']:<35} {st}  ({r.get('duration_ms', 0)}ms)")

print(f"\n  PASS={totais['PASS']} | FAIL={totais['FAIL']} | WARN={totais['WARN']} | SKIP={totais['SKIP']} | TIMEOUT={totais['TIMEOUT']} | ERROR={totais['ERROR']}")
print(f"\n  Relatório JSON salvo em: {REPORT_PATH}")
print("=" * 70)
