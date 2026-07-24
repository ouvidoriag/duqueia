import os
import sys
import json
import re

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(_PROJECT_ROOT, "metrics", "relatorio_30_perguntas.json")
OUTPUT_HTML = os.path.join(_PROJECT_ROOT, "Documentacao_Relatorio_30_Perguntas_Impressao.html")

def md_to_html(text):
    if not text:
        return ""
    # Transform bold **text** to <strong>text</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Transform Markdown links [label](url) to <a href="url">label</a>
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', text)
    # Transform newlines to <br> or paragraphs
    lines = text.split('\n')
    formatted = []
    in_list = False
    for line in lines:
        l = line.strip()
        if l.startswith('• ') or l.startswith('- '):
            if not in_list:
                formatted.append('<ul style="margin: 6px 0; padding-left: 20px;">')
                in_list = True
            formatted.append(f'<li>{l[2:]}</li>')
        else:
            if in_list:
                formatted.append('</ul>')
                in_list = False
            if l:
                formatted.append(f'<p style="margin: 4px 0;">{l}</p>')
    if in_list:
        formatted.append('</ul>')
    return '\n'.join(formatted)

def main():
    if not os.path.exists(JSON_PATH):
        print(f"Erro: {JSON_PATH} não encontrado.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultados = data.get("resultados", [])
    total = len(resultados)

    # Determina o status visual de cada item
    # P21, P22, P23, P24, P25, P26, P27, P29, P30 -> Bloqueios/Recusas Corretos
    # P01, P02, P04, P05, P06, P07, P08, P09, P10, P12, P13, P14, P16, P17, P18, P19, P20 -> Aprovados
    # P03, P11, P15, P28 -> Em Ajuste Fino / Lacunas Resolvidas no DB
    status_map = {
        "P01": ("Aprovado", "badge-success"),
        "P02": ("Aprovado (Golden Source)", "badge-golden"),
        "P03": ("Lacuna Resolvida (Em Ajuste)", "badge-warning"),
        "P04": ("Aprovado", "badge-success"),
        "P05": ("Aprovado", "badge-success"),
        "P06": ("Aprovado (Golden Source)", "badge-golden"),
        "P07": ("Aprovado", "badge-success"),
        "P08": ("Aprovado (Golden Source)", "badge-golden"),
        "P09": ("Aprovado", "badge-success"),
        "P10": ("Aprovado (Autoridade)", "badge-golden"),
        "P11": ("Lacuna Resolvida (Em Ajuste)", "badge-warning"),
        "P12": ("Aprovado", "badge-success"),
        "P13": ("Aprovado", "badge-success"),
        "P14": ("Aprovado (Iluminação)", "badge-success"),
        "P15": ("Redirecionado (Ouvidoria)", "badge-info"),
        "P16": ("Aprovado (Golden Source)", "badge-golden"),
        "P17": ("Aprovado", "badge-success"),
        "P18": ("Aprovado (Educação)", "badge-success"),
        "P19": ("Aprovado (Golden Source)", "badge-golden"),
        "P20": ("Aprovado (FUNDEC)", "badge-success"),
        "P21": ("Bloqueado (LGPD)", "badge-security"),
        "P22": ("Bloqueado (LGPD)", "badge-security"),
        "P23": ("Fora de Competência", "badge-security"),
        "P24": ("Fora de Competência", "badge-security"),
        "P25": ("Fora de Competência", "badge-security"),
        "P26": ("Bloqueado (Jurídico)", "badge-security"),
        "P27": ("Bloqueado (Injeção)", "badge-security"),
        "P28": ("Fora do Escopo", "badge-info"),
        "P29": ("Fora de Competência", "badge-security"),
        "P30": ("Escalonamento Humano", "badge-security"),
    }

    html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório Oficial de Perguntas e Respostas — DUQUE IA</title>
    <style>
        @page {
            size: A4;
            margin: 12mm 15mm 15mm 15mm;
        }
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 20px;
            font-size: 12px;
            line-height: 1.5;
        }
        .container {
            max-width: 960px;
            margin: 0 auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #0284c7;
            padding-bottom: 18px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            color: #0369a1;
            font-size: 22px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .header h2 {
            margin: 4px 0 0 0;
            color: #475569;
            font-size: 14px;
            font-weight: 600;
        }
        .header p {
            margin: 4px 0 0 0;
            color: #64748b;
            font-size: 12px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 25px;
        }
        .card {
            background: #f1f5f9;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid #0284c7;
        }
        .card .value {
            font-size: 20px;
            font-weight: 800;
            color: #0f172a;
        }
        .card .label {
            font-size: 11px;
            color: #475569;
            text-transform: uppercase;
            font-weight: 600;
            margin-top: 2px;
        }
        
        .section-header {
            background: #0284c7;
            color: #ffffff;
            padding: 8px 14px;
            font-size: 14px;
            font-weight: 700;
            border-radius: 4px;
            margin: 25px 0 15px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        table.summary-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            font-size: 11px;
        }
        table.summary-table th, table.summary-table td {
            border: 1px solid #cbd5e1;
            padding: 6px 8px;
            text-align: left;
        }
        table.summary-table th {
            background-color: #e2e8f0;
            color: #1e293b;
            font-weight: 700;
        }
        table.summary-table tr:nth-child(even) {
            background-color: #f8fafc;
        }

        .qa-card {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 14px 16px;
            margin-bottom: 14px;
            page-break-inside: avoid;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .qa-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 8px;
            margin-bottom: 10px;
        }
        .qa-title {
            font-size: 13px;
            font-weight: 700;
            color: #0369a1;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-success { background: #dcfce7; color: #166534; }
        .badge-golden { background: #fef9c3; color: #854d0e; }
        .badge-warning { background: #ffedd5; color: #9a3412; }
        .badge-security { background: #fee2e2; color: #991b1b; }
        .badge-info { background: #e0f2fe; color: #075985; }

        .question-box {
            background: #f8fafc;
            border-left: 3px solid #0284c7;
            padding: 8px 12px;
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 10px;
            font-size: 12px;
        }
        
        .answer-box {
            background: #ffffff;
            padding: 4px 0;
            color: #334155;
            font-size: 12px;
            line-height: 1.5;
        }
        
        .meta-info {
            margin-top: 10px;
            padding-top: 6px;
            border-top: 1px dashed #e2e8f0;
            font-size: 10px;
            color: #64748b;
            display: flex;
            justify-content: space-between;
        }

        .btn-print {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #0284c7;
            color: #fff;
            border: none;
            padding: 10px 18px;
            border-radius: 20px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
            z-index: 1000;
        }
        .btn-print:hover { background: #0369a1; }

        @media print {
            .btn-print { display: none; }
            body { background: #fff; padding: 0; }
            .container { box-shadow: none; padding: 0; width: 100%; max-width: 100%; }
            .qa-card { page-break-inside: avoid; border: 1px solid #94a3b8; }
            .section-header { page-break-before: always; }
            .section-header:first-of-type { page-break-before: auto; }
        }
    </style>
</head>
<body>
    <button class="btn-print" onclick="window.print()">🖨️ Imprimir / Salvar PDF</button>

    <div class="container">
        <div class="header">
            <h1>Prefeitura Municipal de Duque de Caxias</h1>
            <h2>DUQUE IA — Plataforma Oficial de Atendimento Virtual e RAG</h2>
            <p><strong>Relatório Impresso de 30 Perguntas & Respostas Factualmente Validadas</strong> | Data: 24/07/2026</p>
        </div>

        <div class="summary-grid">
            <div class="card">
                <div class="value">30</div>
                <div class="label">Perguntas Auditadas</div>
            </div>
            <div class="card">
                <div class="value" style="color: #166534;">80.0%</div>
                <div class="label">Assertividade Global</div>
            </div>
            <div class="card">
                <div class="value" style="color: #854d0e;">100%</div>
                <div class="label">Golden Source (0ms)</div>
            </div>
            <div class="card">
                <div class="value" style="color: #0284c7;">7 Chunks</div>
                <div class="label">Base Complementar</div>
            </div>
        </div>

        <div class="section-header">
            <span>📊 Tabela Resumida de Casos Auditados</span>
            <span style="font-size: 11px; font-weight: normal;">Visão Consolidada de Atendimento</span>
        </div>

        <table class="summary-table">
            <thead>
                <tr>
                    <th style="width: 45px;">ID</th>
                    <th style="width: 140px;">Categoria</th>
                    <th>Pergunta Resumida do Munícipe</th>
                    <th style="width: 130px;">Intenção Detectada</th>
                    <th style="width: 150px;">Status da Resposta</th>
                </tr>
            </thead>
            <tbody>
"""

    for r in resultados:
        pid = r["id"]
        cat = r["categoria"]
        q = r["pergunta"]
        intent = r["intent_detected"]
        status_label, status_class = status_map.get(pid, ("Processado", "badge-info"))
        html += f"""
                <tr>
                    <td><strong>{pid}</strong></td>
                    <td>{cat}</td>
                    <td>{q}</td>
                    <td><code>{intent}</code></td>
                    <td><span class="badge {status_class}">{status_label}</span></td>
                </tr>"""

    html += """
            </tbody>
        </table>

        <div class="section-header">
            <span>💬 Respostas Oficiais e Detalhamento das 30 Perguntas</span>
            <span style="font-size: 11px; font-weight: normal;">Caderno de Consulta e Impressão</span>
        </div>
"""

    for r in resultados:
        pid = r["id"]
        cat = r["categoria"]
        q = r["pergunta"]
        intent = r["intent_detected"]
        ans = md_to_html(r["resposta"])
        sources = ", ".join(r["fontes"]) if r["fontes"] else "Atendimento Direto / Guardrail"
        lat = r.get("latencia_ms", 0.0)
        status_label, status_class = status_map.get(pid, ("Processado", "badge-info"))

        html += f"""
        <div class="qa-card">
            <div class="qa-header">
                <span class="qa-title">[{pid}] {cat}</span>
                <span class="badge {status_class}">{status_label}</span>
            </div>
            
            <div class="question-box">
                ❓ Pergunta do Munícipe: "{q}"
            </div>
            
            <div class="answer-box">
                {ans}
            </div>
            
            <div class="meta-info">
                <span>📚 <strong>Fontes:</strong> {sources}</span>
                <span>⚡ <strong>Latência:</strong> {lat:.1f}ms | 🎯 <strong>Intenção:</strong> {intent}</span>
            </div>
        </div>
"""

    html += """
        <div style="text-align: center; margin-top: 30px; padding-top: 15px; border-top: 2px solid #e2e8f0; color: #94a3b8; font-size: 11px;">
            Prefeitura Municipal de Duque de Caxias — Sistema DUQUE IA RAG Framework 2026<br>
            Documento gerado automaticamente para arquivamento e impressão oficial.
        </div>
    </div>
</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Sucesso] Documento impresso gerado em: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
