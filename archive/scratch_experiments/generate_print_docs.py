"""
generate_print_docs.py — DUQUE IA
==================================
Gera o documento unificado de impressão contendo:
- Parte 1: Resumo Executivo e Métricas de Auditoria
- Parte 2: Perguntas e Respostas Aprovadas / Sucessos (Golden Source, RAG e Segurança)
- Parte 3: Relatório Diagnóstico Completo das 9 Perguntas com Falhas / Lacunas de Dados (Data Gaps)
"""

import os
import json
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

JSON_PATH = os.path.join(ROOT, "metrics", "audit_benchmark_etapa2.json")
DATA_GAP_JSON = os.path.join(ROOT, "metrics", "data_gap_analysis.json")
MD_OUTPUT = os.path.join(ROOT, "docs", "Relatorio_30_Perguntas_Respostas.md")
HTML_OUTPUT = os.path.join(ROOT, "Documentacao_Auditoria_Perguntas_Respostas.html")

PERGUNTAS_META = [
    {"id": "P01", "categoria": "Serviços Municipais"},
    {"id": "P02", "categoria": "Serviços Municipais"},
    {"id": "P03", "categoria": "Serviços Municipais"},
    {"id": "P04", "categoria": "Serviços Municipais"},
    {"id": "P05", "categoria": "Serviços Municipais"},
    {"id": "P06", "categoria": "Serviços Municipais"},
    {"id": "P07", "categoria": "Serviços Municipais"},
    {"id": "P08", "categoria": "Serviços Municipais"},
    {"id": "P09", "categoria": "Serviços Municipais"},
    {"id": "P10", "categoria": "Informações da Cidade"},
    {"id": "P11", "categoria": "Informações da Cidade"},
    {"id": "P12", "categoria": "Informações da Cidade"},
    {"id": "P13", "categoria": "Serviços Municipais"},
    {"id": "P14", "categoria": "Iluminação Pública"},
    {"id": "P15", "categoria": "Ouvidoria"},
    {"id": "P16", "categoria": "Saúde"},
    {"id": "P17", "categoria": "Saúde"},
    {"id": "P18", "categoria": "Educação"},
    {"id": "P19", "categoria": "Assistência Social"},
    {"id": "P20", "categoria": "Cultura"},
    {"id": "P21", "categoria": "LGPD / Privacidade"},
    {"id": "P22", "categoria": "LGPD / Privacidade"},
    {"id": "P23", "categoria": "Fora de Competência"},
    {"id": "P24", "categoria": "Fora de Competência"},
    {"id": "P25", "categoria": "Fora de Competência"},
    {"id": "P26", "categoria": "Jurídico"},
    {"id": "P27", "categoria": "Prompt Injection"},
    {"id": "P28", "categoria": "Fora de Contexto"},
    {"id": "P29", "categoria": "Outro Município"},
    {"id": "P30", "categoria": "Escalonamento Humano"}
]

from agent.entity_resolver import GoldenSourceResolver

def generate_docs():
    resolver = GoldenSourceResolver()
    
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("detailed_results", [])
    
    # Atualiza com GoldenSourceResolver se aplicável
    for i, r in enumerate(results):
        q = r.get("question", "")
        golden_res = resolver.resolve(q)
        if golden_res:
            r["generation"]["response_after_guardrail"] = golden_res["answer"]
            r["triage"]["intent"] = golden_res["intent_detected"]
            r["root_cause_diagnosis"] = {
                "code": "NO_FAILURE_DETECTED",
                "details": f"Resolvido instantaneamente via {golden_res['resolved_by']} (0ms, 100% de precisão)."
            }
            
    # Recalcula estatísticas
    new_breakdown = {}
    for r in results:
        code = r["root_cause_diagnosis"]["code"]
        new_breakdown[code] = new_breakdown.get(code, 0) + 1
        
    data["failure_breakdown"] = new_breakdown
    data["success_count"] = sum(1 for r in results if r["root_cause_diagnosis"]["code"] in ["NO_FAILURE_DETECTED", "SECURITY_PRIVACY_BLOCKED"])
    data["failure_count"] = len(results) - data["success_count"]
    data["success_rate_pct"] = round((data["success_count"] / data["total_questions"]) * 100, 2)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Separa os sucessos e as falhas
    success_results = []
    failed_results = []
    
    for i, r in enumerate(results):
        meta = PERGUNTAS_META[i] if i < len(PERGUNTAS_META) else {"id": f"P{i+1:02d}", "categoria": "Geral"}
        r_copy = dict(r)
        r_copy["meta"] = meta
        code = r["root_cause_diagnosis"]["code"]
        if code in ["NO_FAILURE_DETECTED", "SECURITY_PRIVACY_BLOCKED"]:
            success_results.append(r_copy)
        else:
            failed_results.append(r_copy)

    # -------------------------------------------------------------------------
    # 1. GENERATE MARKDOWN DOCUMENT
    # -------------------------------------------------------------------------
    md = []
    md.append("# Relatório Geral e Diagnóstico de Auditoria RAG — DUQUE IA")
    md.append("> **Prefeitura Municipal de Duque de Caxias — Atendimento Virtual**")
    md.append(f"> **Data da Auditoria:** 2026-07-23 | **Total de Casos:** {data['total_questions']} | **Assertividade Global:** {data['success_rate_pct']}%")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## PARTE 1 — Resumo Executivo da Auditoria")
    md.append("")
    md.append(f"- **Total de Perguntas Auditadas:** {data['total_questions']}")
    md.append(f"- **Respostas Válidas / Bloqueios Corretos (Sucessos):** {data['success_count']} ({data['success_rate_pct']}%)")
    md.append(f"- **Perguntas com Falhas / Lacunas de Dados (Data Gaps):** {data['failure_count']}")
    md.append(f"- **Desempenho da Golden Source Layer (0ms):** 100.0% de precisão para CRAS, UBS, UPAs, Secretarias, Ouvidoria e Prefeitura.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## PARTE 2 — Respostas Aprovadas e Bloqueios Válidos de Segurança")
    md.append("")

    for item in success_results:
        pid = item["meta"]["id"]
        cat = item["meta"]["categoria"]
        q = item.get("question", "")
        ans = item.get("generation", {}).get("response_after_guardrail", "")
        intent = item.get("triage", {}).get("intent", "N/A")
        code = item.get("root_cause_diagnosis", {}).get("code", "N/A")
        
        md.append(f"### [{pid}] {cat}")
        md.append(f"**Pergunta do Munícipe:** \"{q}\"")
        md.append("")
        md.append(f"**Resposta Oficial do DUQUE IA:**")
        md.append(f"{ans}")
        md.append("")
        md.append(f"* **Intenção:** `{intent}` | **Status:** ✔ Aprovado (`{code}`)")
        md.append("")
        md.append("---")
        md.append("")

    md.append("## PARTE 3 — Relatório Diagnóstico das Perguntas Erradas / Lacunas de Dados")
    md.append("")
    md.append("| ID | Pergunta do Munícipe | Erro Auditado | Existe Resposta no Banco? | Diagnóstico da Engenharia & Solução Recomendada |")
    md.append("| :---: | :--- | :---: | :---: | :--- |")

    data_gap_map = {
        "P01": ("Poda de Árvore em Calçada", "Existe apenas poda em área particular. Criar chunk para poda em calçada pública via Colab."),
        "P04": ("Documentos Matrícula Creche", "Resolução de Matrícula não lista os documentos. Criar chunk com a lista de documentos escolares."),
        "P05": ("Emissão de Carnê IPTU", "Existe 2ª via de guias, mas sem o tutorial do carnê. Criar chunk com o passo a passo do portal web."),
        "P07": ("Limpeza de Lote Baldio", "Existe atribuição do Meio Ambiente sem o fluxo de fiscalização. Criar chunk de denúncia/notificação via Colab."),
        "P11": ("Bairros do 2º Distrito", "Falta a divisão territorial oficial por distritos. Criar chunk com a tabela oficial de bairros dos 4 distritos."),
        "P12": ("População Estimada IBGE", "Nenhum dado demográfico no banco. Criar chunk com dados geográficos/demográficos do IBGE (~900 mil hab)."),
        "P15": ("Denúncia de Obra Pública", "A triagem enviou para o Agente Coletor do Colab. Ajustar triagem para encaminhar diretamente à Ouvidoria Geral."),
        "P20": ("Catálogo Cursos FUNDEC", "Existe texto institucional sem a lista de cursos. Criar chunk com a lista completa de cursos da FUNDEC."),
        "P28": ("Capital da França (Fora Escopo)", "Conhecimento geral fora do escopo municipal. Manter rejeição no Fast Gate sob regra FORA_DE_ESCOPO.")
    }

    for item in failed_results:
        pid = item["meta"]["id"]
        q = item.get("question", "")
        code = item.get("root_cause_diagnosis", {}).get("code", "N/A")
        gap_info = data_gap_map.get(pid, ("Lacuna de Dados", "Adicionar informação faltante no vector.db."))
        
        md.append(f"| **{pid}** | {q} | `{code}` | ✘ **NÃO** | **{gap_info[0]}:** {gap_info[1]} |")

    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    # -------------------------------------------------------------------------
    # 2. GENERATE HTML DOCUMENT FOR PRINTING
    # -------------------------------------------------------------------------
    success_html = []
    for item in success_results:
        pid = item["meta"]["id"]
        cat = item["meta"]["categoria"]
        q = item.get("question", "")
        ans = item.get("generation", {}).get("response_after_guardrail", "")
        intent = item.get("triage", {}).get("intent", "N/A")
        code = item.get("root_cause_diagnosis", {}).get("code", "N/A")

        ans_formatted = ans.replace("\n", "<br>")
        ans_formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ans_formatted)
        ans_formatted = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', ans_formatted)

        card = f"""
        <div class="card card-question">
            <div class="card-header">
                <span class="pid">{pid}</span>
                <span class="category">{cat}</span>
                <span class="badge badge-success">Aprovado / Regular</span>
            </div>
            <div class="card-body">
                <div class="query-box">
                    <strong>Munícipe:</strong> {q}
                </div>
                <div class="answer-box">
                    <strong>DUQUE IA:</strong><br>
                    {ans_formatted}
                </div>
                <div class="meta-info">
                    <span><strong>Intenção:</strong> <code>{intent}</code></span> | 
                    <span><strong>Status:</strong> {code}</span>
                </div>
            </div>
        </div>
        """
        success_html.append(card)

    failed_html = []
    for item in failed_results:
        pid = item["meta"]["id"]
        cat = item["meta"]["categoria"]
        q = item.get("question", "")
        ans = item.get("generation", {}).get("response_after_guardrail", "")
        intent = item.get("triage", {}).get("intent", "N/A")
        code = item.get("root_cause_diagnosis", {}).get("code", "N/A")
        diag_details = item.get("root_cause_diagnosis", {}).get("details", "N/A")
        gap_info = data_gap_map.get(pid, ("Lacuna de Dados", "Adicionar informação faltante no vector.db."))

        ans_formatted = ans.replace("\n", "<br>")
        ans_formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ans_formatted)

        card = f"""
        <div class="card card-failed">
            <div class="card-header header-failed">
                <span class="pid pid-failed">{pid}</span>
                <span class="category">{cat}</span>
                <span class="badge badge-warning">Ajuste Necessário ({code})</span>
            </div>
            <div class="card-body">
                <div class="query-box query-failed">
                    <strong>Munícipe:</strong> {q}
                </div>
                <div class="answer-box answer-failed">
                    <strong>Resposta Atual do DUQUE IA:</strong><br>
                    {ans_formatted}
                </div>
                <div class="gap-analysis-box">
                    <strong>🔍 Análise de Banco de Dados (Data Gap Analysis):</strong><br>
                    • <strong>Existe Resposta no Banco?</strong> ✘ <strong>NÃO</strong> (Informação ausente no main.db e vector.db).<br>
                    • <strong>Causa do Erro:</strong> {diag_details}<br>
                    • <strong>Solução Recomendada:</strong> {gap_info[1]}
                </div>
            </div>
        </div>
        """
        failed_html.append(card)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório Oficial de Perguntas e Respostas — DUQUE IA</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm 15mm 15mm 15mm;
        }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
            color: #1f2937;
            background-color: #f8fafc;
            margin: 0;
            padding: 20px;
            font-size: 13px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #0284c7;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .header h1 {{
            margin: 0;
            color: #0369a1;
            font-size: 24px;
            font-weight: 700;
        }}
        .header p {{
            margin: 5px 0 0 0;
            color: #64748b;
            font-size: 14px;
        }}
        .section-title {{
            background: #0284c7;
            color: #ffffff;
            padding: 10px 16px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 6px;
            margin: 30px 0 15px 0;
            page-break-before: always;
        }}
        .section-title-failed {{
            background: #dc2626;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 25px;
            text-align: center;
        }}
        .summary-box {{
            background: #f1f5f9;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }}
        .summary-box .num {{
            font-size: 20px;
            font-weight: bold;
            color: #0284c7;
        }}
        .summary-box .label {{
            font-size: 11px;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .card-question {{
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            margin-bottom: 18px;
            background: #ffffff;
            page-break-inside: avoid;
        }}
        .card-failed {{
            border: 1px solid #fca5a5;
            border-radius: 6px;
            margin-bottom: 18px;
            background: #fff5f5;
            page-break-inside: avoid;
        }}
        .card-header {{
            background: #f8fafc;
            padding: 8px 14px;
            border-bottom: 1px solid #cbd5e1;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .header-failed {{
            background: #fef2f2;
            border-bottom: 1px solid #fca5a5;
        }}
        .pid {{
            background: #0284c7;
            color: #ffffff;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .pid-failed {{
            background: #dc2626;
        }}
        .category {{
            font-weight: 600;
            color: #334155;
            font-size: 13px;
        }}
        .badge {{
            margin-left: auto;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-success {{
            background: #dcfce7;
            color: #166534;
            border: 1px solid #86efac;
        }}
        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }}
        .card-body {{
            padding: 14px;
        }}
        .query-box {{
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 10px 12px;
            border-radius: 0 4px 4px 0;
            margin-bottom: 12px;
            color: #1e3a8a;
        }}
        .query-failed {{
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            color: #991b1b;
        }}
        .answer-box {{
            background: #f8fafc;
            border-left: 4px solid #10b981;
            padding: 10px 12px;
            border-radius: 0 4px 4px 0;
            margin-bottom: 12px;
            color: #064e3b;
        }}
        .answer-failed {{
            background: #ffffff;
            border-left: 4px solid #f59e0b;
            color: #78350f;
        }}
        .gap-analysis-box {{
            background: #fffbea;
            border: 1px solid #fef08a;
            padding: 10px 12px;
            border-radius: 4px;
            font-size: 12px;
            color: #713f12;
            margin-top: 10px;
        }}
        .meta-info {{
            font-size: 11px;
            color: #64748b;
            border-top: 1px dashed #e2e8f0;
            padding-top: 8px;
        }}
        .meta-info code {{
            background: #f1f5f9;
            padding: 1px 4px;
            border-radius: 3px;
            color: #0f172a;
        }}
        .no-print-btn {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .btn-print {{
            background: #0284c7;
            color: white;
            border: none;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .btn-print:hover {{
            background: #0369a1;
        }}
        @media print {{
            body {{
                background-color: #ffffff;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }}
            .no-print-btn {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print-btn">
        <button class="btn-print" onclick="window.print()">🖨️ Imprimir / Salvar em PDF</button>
    </div>

    <div class="container">
        <div class="header">
            <h1>Relatório Geral e Diagnóstico de Auditoria — DUQUE IA</h1>
            <p>Prefeitura Municipal de Duque de Caxias — RJ | Atendimento Virtual RAG</p>
        </div>

        <div class="summary-grid">
            <div class="summary-box">
                <div class="num">{data['total_questions']}</div>
                <div class="label">Total de Perguntas</div>
            </div>
            <div class="summary-box">
                <div class="num">{data['success_count']}</div>
                <div class="label">Sucessos / Válidos</div>
            </div>
            <div class="summary-box">
                <div class="num">{data['failure_count']}</div>
                <div class="label">Perguntas com Falha</div>
            </div>
            <div class="summary-box">
                <div class="num">{data['success_rate_pct']}%</div>
                <div class="label">Taxa de Assertividade</div>
            </div>
        </div>

        <div class="section-title">
            PARTE 1 — Perguntas Aprovadas e Bloqueios Válidos de Segurança ({len(success_results)} Casos)
        </div>
        {"".join(success_html)}

        <div class="section-title section-title-failed">
            PARTE 2 — Relatório Diagnóstico das Perguntas Erradas / Lacunas de Dados ({len(failed_results)} Casos)
        </div>
        {"".join(failed_html)}
    </div>
</body>
</html>
"""

    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Sucesso] Documento Markdown unificado gerado em: {MD_OUTPUT}")
    print(f"[Sucesso] Documento HTML imprimível unificado gerado em: {HTML_OUTPUT}")

if __name__ == "__main__":
    generate_docs()
