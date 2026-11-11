"""
dashboard.py — DUQUE IA
========================
CLI para exibir as métricas de observabilidade.
Uso: python metrics/dashboard.py --last 100
"""

import os
import json
import argparse
from collections import Counter

METRICS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "requests.jsonl"))

def main():
    parser = argparse.ArgumentParser(description="Dashboard de Métricas Duque IA")
    parser.add_argument("--last", type=int, default=100, help="Número de últimas requisições a analisar")
    args = parser.parse_args()

    if not os.path.exists(METRICS_FILE):
        print(f"Arquivo de métricas não encontrado: {METRICS_FILE}")
        return

    records = []
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except:
                    pass

    if not records:
        print("Nenhuma métrica registrada ainda.")
        return

    # Pega os N últimos
    recent = records[-args.last:]
    n = len(recent)

    # Agregações
    cache_hits = sum(1 for r in recent if r.get("cache_hit"))
    cache_rate = (cache_hits / n) * 100 if n > 0 else 0

    total_times = [r.get("total_time_ms", 0) for r in recent]
    avg_time = sum(total_times) / n if n > 0 else 0
    p95_time = sorted(total_times)[int(n * 0.95)] if n > 0 else 0

    total_cost = sum(r.get("cost_usd", 0.0) for r in recent)
    avg_cost = total_cost / n if n > 0 else 0

    tokens = [r.get("tokens_used", 0) for r in recent]
    avg_tokens = sum(tokens) / n if n > 0 else 0

    providers = Counter(r.get("provider_used", "unknown") for r in recent)
    intents = Counter(r.get("intent", "UNKNOWN") for r in recent)

    print(f"\n=== DUQUE IA — Últimas {n} requisições ===")
    print(f"Cache Hit Rate    : {cache_rate:.1f}%")
    print(f"Latência Média    : {avg_time/1000:.2f}s   (p95: {p95_time/1000:.2f}s)")
    print(f"Custo Médio       : ${avg_cost:.6f}/req")
    print(f"Tokens Médios     : {avg_tokens:.0f}")
    
    print("\nProvedores Principais:")
    for p, count in providers.most_common(3):
        print(f"  - {p.ljust(15)} : {count/n*100:.1f}%")

    print("\nTop Intents:")
    for i, count in intents.most_common(5):
        print(f"  - {i.ljust(25)} : {count/n*100:.1f}%")
        
    print("==========================================\n")

if __name__ == "__main__":
    main()
