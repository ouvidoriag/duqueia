import os
import json
import sys

# Set console to utf-8
sys.stdout.reconfigure(encoding='utf-8')

patterns = [
    'neste momento',
    'base de dados',
    'não consta',
    'não constam',
    'não temos',
    'não possuo',
    'não tenho',
    'não pode ser respondida',
    'não disponho',
    'não encontrei',
    'não há registro',
    'não há informações'
]

files = [
    'scripts/results_expanded_quality_audit.json',
    'scripts/results_23_casos_novas_respostas.json'
]

for fpath in files:
    if not os.path.exists(fpath):
        continue
    raw_data = json.load(open(fpath, encoding='utf-8'))
    cases = raw_data.get('cases', []) if isinstance(raw_data, dict) else raw_data
    print(f"\n================================================================================")
    print(f" ARQUIVO: {fpath} (Total de casos: {len(cases)})")
    print(f"================================================================================")
    found = 0
    for c in cases:
        cid = c.get('id', '')
        tit = c.get('titulo', '')
        q = c.get('pergunta', '')
        ans = c.get('resultado', {}).get('answer', '') or c.get('nova_resposta', '') or c.get('answer', '')
        
        matches = [p for p in patterns if p in ans.lower()]
        if matches:
            found += 1
            print(f"\n[{cid}] {tit}")
            print(f"Pergunta: \"{q}\"")
            print(f"Gatilhos identificados: {matches}")
            print("Trecho da resposta:")
            for p in matches:
                idx = ans.lower().find(p)
                start = max(0, idx - 40)
                end = min(len(ans), idx + 160)
                print(f"  • ...{ans[start:end].replace(chr(10), ' ')}...")
            print("-" * 80)
    print(f"\nTotal com admissão de ausência de dados em {fpath}: {found}")
