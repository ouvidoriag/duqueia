import os
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(ROOT, "metrics", "audit_benchmark_etapa2.json")

def print_failures():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("detailed_results", [])
    
    print("=" * 70)
    print("      LISTA DE FALHAS IDENTIFICADAS NA AUDITORIA (9 FALHAS)")
    print("=" * 70)
    
    count = 0
    for idx, r in enumerate(results, 1):
        diag = r.get("root_cause_diagnosis", {})
        code = diag.get("code", "")
        if code not in ["NO_FAILURE_DETECTED", "SECURITY_PRIVACY_BLOCKED"]:
            count += 1
            q = r.get("question", "")
            details = diag.get("details", "")
            print(f"\n[{count}] Item #{idx:02d} — {code}")
            print(f"    Pergunta: \"{q}\"")
            print(f"    Motivo: {details}")

if __name__ == "__main__":
    print_failures()
