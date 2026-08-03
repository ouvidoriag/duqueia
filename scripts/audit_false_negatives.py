import os
import sys
import json
import re
import re

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(_PROJECT_ROOT, "metrics", "relatorio_30_perguntas.json")
REPORT_PATH = os.path.join(_PROJECT_ROOT, "metrics", "auditoria_falsos_negativos.md")

NOT_FOUND_PATTERNS = [
    r"não encontrei",
    r"não localizei",
    r"não possuo",
    r"não há dados",
    r"não consta",
    r"não estão disponíveis",
    r"não foram encontradas",
    r"não tenho informações"
]

def check_answer_says_not_found(answer: str) -> bool:
    ans_lower = answer.lower()
    for pat in NOT_FOUND_PATTERNS:
        if re.search(pat, ans_lower):
            return True
    return False

def audit():
    if not os.path.exists(JSON_PATH):
        print("Arquivo relatorio_30_perguntas.json não encontrado!")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultados = data.get("resultados", [])
    
    audit_table = []
    falsos_negativos = []
    respostas_corretas = []
    bloqueios_seguranca = []

    for r in resultados:
        pid = r["id"]
        cat = r["categoria"]
        q = r["pergunta"]
        ans = r.get("resposta", "")
        sources = r.get("fontes", [])
        intent = r.get("intent_detected", "")
        
        num_docs = len(sources)
        says_not_found = check_answer_says_not_found(ans)
        
        # Classificação de erro ou sucesso
        is_guardrail = intent in ["blocked_privacy", "out_of_competency", "human_escalation", "blocked_legal"]
        
        if is_guardrail:
            status = "🛡️ Bloqueio Legítimo"
            erro = "✅ OK"
            bloqueios_seguranca.append(r)
        elif says_not_found and num_docs > 0:
            status = "❌ FALSO NEGATIVO (IA recusou mas tinha docs)"
            erro = "❌ FALHA RAG/PROMPT"
            falsos_negativos.append(r)
        elif says_not_found and num_docs == 0:
            status = "⚠️ Sem dados na base"
            erro = "ℹ️ Lacuna Real"
        else:
            status = "✅ Resposta Informativa Gerada"
            erro = "✅ OK"
            respostas_corretas.append(r)

        fontes_short = ", ".join([os.path.basename(s) for s in sources]) if sources else "Nenhuma"
        audit_table.append([pid, cat, q[:50] + "...", num_docs, fontes_short[:30], "Sim" if says_not_found else "Não", erro])

    # Gera relatório em Markdown
    md_lines = [
        "# Auditoria de Falsos Negativos e Qualidade Factual das Respostas",
        f"**Data:** {data.get('timestamp', 'Hoje')}  ",
        f"**Total de Perguntas Auditadas:** {len(resultados)}  ",
        f"**Falsos Negativos Detectados:** {len(falsos_negativos)} ❌  ",
        f"**Respostas Informativas Úteis:** {len(respostas_corretas)} ✅  ",
        f"**Bloqueios Legítimos (LGPD/Competência):** {len(bloqueios_seguranca)} 🛡️  ",
        "",
        "---",
        "",
        "## Tabela Consolidada de Auditoria de Falsos Negativos",
        "",
        "| ID | Categoria | Pergunta | Docs Recuperados | Fontes Usadas | IA Respondeu 'Não Encontrei'? | Avaliação de Qualidade |",
        "|:---:|:---|:---|:---:|:---|:---:|:---:|"
    ]

    for row in audit_table:
        md_lines.append(f"| **{row[0]}** | {row[1]} | {row[2]} | {row[3]} | `{row[4]}` | {row[5]} | **{row[6]}** |")

    md_lines += [
        "",
        "---",
        "",
        "## Detalhamento dos Falsos Negativos Detectados (Ação de Correção Necessária)",
        ""
    ]

    if not falsos_negativos:
        md_lines.append("🎉 **Nenhum Falso Negativo Detectado!** A IA utilizou 100% dos documentos recuperados sem recusas indevidas.")
    else:
        for fn in falsos_negativos:
            md_lines += [
                f"### ❌ [{fn['id']}] {fn['categoria']}: \"{fn['pergunta']}\"",
                f"**Fontes que o banco encontrou ({len(fn['fontes'])}):** `{', '.join(fn['fontes'])}`  ",
                f"**Resposta gerada pela IA:**",
                f"> {fn['resposta']}",
                "",
                f"**Diagnóstico da Falha:** O banco de dados recuperou os documentos acima com score semântico relevante, mas o modelo/prompt considerou que as informações eram incompletas e acionou a recusa com direcionamento para a Ouvidoria.",
                "",
                "---",
                ""
            ]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"[Sucesso] Relatório de Auditoria salvo em: {REPORT_PATH}")

    print("\n" + "="*70)
    print(f"AUDITORIA CONCLUÍDA:")
    print(f"  Falsos Negativos (Docs > 0 e Resposta 'Não encontrei'): {len(falsos_negativos)}")
    print(f"  Respostas Informativas Úteis : {len(respostas_corretas)}")
    print(f"  Bloqueios Legítimos de Segurança: {len(bloqueios_seguranca)}")
    print("="*70)

if __name__ == "__main__":
    audit()
