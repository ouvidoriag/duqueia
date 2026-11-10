# -*- coding: utf-8 -*-
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

all_items = []

# 1. 43 Casos de Auditoria Expandida (23 Oficiais da Ouvidoria + 20 de Estresse)
p_expanded = os.path.join(ROOT, "scripts", "results_expanded_quality_audit.json")
if os.path.exists(p_expanded):
    with open(p_expanded, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data.get("cases", []):
        all_items.append({
            "id": c.get("id"),
            "origem": "Auditoria de Homologação (Ouvidoria & Estresse)",
            "subgrupo": "Casos Oficiais de Homologação" if c.get("id", "").startswith("H") else "Bateria de Estresse Expandida",
            "titulo": c.get("titulo", ""),
            "query": c.get("pergunta", "").strip(),
            "criterio": c.get("criterio_sucesso", "")
        })

# 2. 30 Perguntas Frequentes Oficiais (docs/Perguntas_Frequentes_Oficiais.md)
p_faq = os.path.join(ROOT, "docs", "Perguntas_Frequentes_Oficiais.md")
if os.path.exists(p_faq):
    with open(p_faq, "r", encoding="utf-8") as f:
        lines = f.readlines()
    curr_cat = "Geral"
    for line in lines:
        if line.startswith("## "):
            curr_cat = line.replace("## ", "").strip()
        elif re.match(r"^###\s+\d+\.\s+", line):
            q_text = re.sub(r"^###\s+\d+\.\s+", "", line).strip()
            all_items.append({
                "id": f"FAQ_{len(all_items)+1:03d}",
                "origem": "FAQ Oficial do Cidadão",
                "subgrupo": curr_cat,
                "titulo": q_text[:60],
                "query": q_text,
                "criterio": "Orientação cidadã factual com links, contatos e prazos"
            })

# 3. 10 Perguntas Busca Externa / Web (docs/audits/Documentacao_10_Perguntas_Busca_Online.md)
p_online = os.path.join(ROOT, "docs", "audits", "Documentacao_10_Perguntas_Busca_Online.md")
if os.path.exists(p_online):
    with open(p_online, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for l in lines:
        m = re.search(r"\|\s*\*\*(W\d+)\*\*\s*\|\s*([^\|]+)\|\s*([^\|]+)\|", l)
        if m:
            wid = m.group(1).strip()
            cat = m.group(2).strip()
            q_text = m.group(3).strip()
            all_items.append({
                "id": wid,
                "origem": "Busca Externa e Concessionárias",
                "subgrupo": cat,
                "titulo": f"Consulta Web {wid}",
                "query": q_text,
                "criterio": "Verificação oficial de notícias e serviços online"
            })

# 4. Perguntas do Benchmark de Relevância e Avaliação RAG
p_retrieval = os.path.join(ROOT, "scripts", "tests", "test_retrieval_relevance.py")
if os.path.exists(p_retrieval):
    with open(p_retrieval, "r", encoding="utf-8") as f:
        content = f.read()
    ret_matches = re.findall(r'\"query\":\s*\"([^\"]+)\"', content)
    for idx, q_text in enumerate(ret_matches, 1):
        all_items.append({
            "id": f"RET_{idx:02d}",
            "origem": "Benchmark de Recuperação Semântica",
            "subgrupo": "Recuperação Institucional / GIS",
            "titulo": f"Benchmark Relevância #{idx}",
            "query": q_text.strip(),
            "criterio": "Recuperação exata de secretaria ou equipamento municipal"
        })

# Deduplicação inteligente
seen = {}
unique_items = []
for item in all_items:
    norm = re.sub(r"[^\w\s]", "", item["query"].lower()).strip()
    norm = re.sub(r"\s+", " ", norm)
    if norm not in seen:
        seen[norm] = item
        unique_items.append(item)

print(f"Total bruto de perguntas encontradas: {len(all_items)}")
print(f"Total de perguntas unificadas (sem duplicidade): {len(unique_items)}")

# Contagem por origem
by_origem = {}
for u in unique_items:
    o = u["origem"]
    by_origem[o] = by_origem.get(o, 0) + 1

for o, count in by_origem.items():
    print(f"  • {o}: {count} perguntas")

dest_json = os.path.join(ROOT, "data", "todas_as_perguntas_consolidadas.json")
with open(dest_json, "w", encoding="utf-8") as f:
    json.dump(unique_items, f, ensure_ascii=False, indent=2)

print(f"\nSalvo lista consolidada de {len(unique_items)} perguntas em:\n  -> {dest_json}")
