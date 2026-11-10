import os
import sys
import json
import re
import subprocess

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
json_path = os.path.join(_PROJECT_ROOT, "scripts", "results_23_casos_novas_respostas.json")
html_path = os.path.join(_PROJECT_ROOT, "docs", "relatorio_avaliacao_novas_respostas_a4.html")
pdf_dest_1 = os.path.join(_PROJECT_ROOT, "DUQUE_IA_AVALIACAO_NOVAS_RESPOSTAS_23_CASOS.pdf")
pdf_dest_2 = os.path.join(_PROJECT_ROOT, "docs", "DUQUE_IA_AVALIACAO_NOVAS_RESPOSTAS_23_CASOS.pdf")

with open(json_path, "r", encoding="utf-8") as f:
    cases_data = json.load(f)

def md_to_html(text: str) -> str:
    """Converte markdown simples para HTML limpo para impressão A4."""
    if not text:
        return ""
    # Converte negritos **texto**
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Converte itálicos *texto*
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    lines = text.strip().split("\n")
    html_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
            
        # Detecta marcadores de lista (*, -, •)
        if stripped.startswith("* ") or stripped.startswith("- ") or stripped.startswith("• "):
            if not in_list:
                html_lines.append('<ul style="margin: 2px 0 3px 14px; padding-left: 0;">')
                in_list = True
            item_text = stripped[2:].strip()
            html_lines.append(f'<li style="margin-bottom: 2px;">{item_text}</li>')
        # Detecta numerações tipo 1. 2.
        elif re.match(r'^\d+\.\s+', stripped):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<div style="margin-top: 3px; margin-bottom: 2px;">{stripped}</div>')
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<p style="margin-bottom: 3px;">{stripped}</p>')
            
    if in_list:
        html_lines.append("</ul>")
        
    return "\n".join(html_lines)

html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DUQUE IA — Relatório de Avaliação e Auditoria das Novas Respostas (A4)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 8pt;
      line-height: 1.35;
      color: #0f172a;
      background-color: #334155;
      padding: 15px 0;
    }

    .no-print-bar {
      position: sticky;
      top: 10px;
      z-index: 9999;
      background: #0f172a;
      color: #ffffff;
      padding: 10px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      border-radius: 6px;
      width: 210mm;
      margin: 0 auto 15px auto;
    }

    .no-print-bar h3 {
      font-family: 'Outfit', sans-serif;
      font-size: 11pt;
      font-weight: 700;
    }

    .print-btn {
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
      color: white;
      border: none;
      padding: 7px 18px;
      font-size: 9pt;
      font-weight: 600;
      border-radius: 5px;
      cursor: pointer;
    }

    .document-container {
      width: 210mm;
      margin: 0 auto;
      background: #ffffff;
      padding: 10mm 12mm 12mm 12mm;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
      border-radius: 2px;
    }

    /* HEADER DO DOCUMENTO */
    .doc-header {
      border-bottom: 2px solid #0284c7;
      padding-bottom: 8px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }

    .doc-header-left h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 13pt;
      font-weight: 800;
      color: #0284c7;
      letter-spacing: -0.3px;
    }

    .doc-header-left p {
      font-size: 7.8pt;
      color: #475569;
      margin-top: 2px;
    }

    .doc-header-right {
      text-align: right;
      font-size: 7pt;
      color: #64748b;
    }

    /* CARD DE CADA CASO */
    .case-card {
      background: #ffffff;
      border: 1px solid #94a3b8;
      border-radius: 5px;
      margin-bottom: 11px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      break-inside: avoid;
      page-break-inside: avoid;
    }

    .case-header {
      background: #f8fafc;
      border-bottom: 1px solid #cbd5e1;
      padding: 5px 9px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .case-title {
      font-family: 'Outfit', sans-serif;
      font-size: 9pt;
      font-weight: 700;
      color: #0f172a;
    }

    .status-badge {
      font-size: 6.8pt;
      font-weight: 700;
      text-transform: uppercase;
      padding: 2px 7px;
      border-radius: 3px;
      letter-spacing: 0.3px;
    }

    .badge-revisado {
      background: #e0f2fe;
      color: #0369a1;
      border: 1px solid #7dd3fc;
    }

    .badge-ouro {
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #86efac;
    }

    .case-body {
      padding: 6px 9px;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .block-section {
      display: flex;
      flex-direction: column;
      line-height: 1.32;
    }

    .block-section .label {
      font-size: 6.6pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      margin-bottom: 1.5px;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .label-query { color: #1e40af; }
    .label-new-ans { color: #166534; }
    .label-old-ans { color: #991b1b; }
    .label-notes { color: #475569; }

    .query-text {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-left: 3px solid #3b82f6;
      padding: 4px 7px;
      border-radius: 3px;
      font-size: 7.8pt;
      font-style: italic;
      color: #1e3a8a;
    }

    .new-answer-box {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-left: 3px solid #16a34a;
      padding: 5px 8px;
      border-radius: 3px;
      font-size: 7.8pt;
      color: #14532d;
    }

    .old-answer-box {
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-left: 3px solid #dc2626;
      padding: 3px 6px;
      border-radius: 3px;
      font-size: 7.2pt;
      color: #7f1d1d;
    }

    .handwritten-box {
      margin-top: 3px;
      padding-top: 4px;
      border-top: 1px dashed #cbd5e1;
    }

    .handwritten-lines {
      display: flex;
      flex-direction: column;
      gap: 7px;
      padding: 2px 0;
    }

    .handwritten-lines .line {
      border-bottom: 1px dotted #94a3b8;
      height: 4px;
      width: 100%;
    }

    @media print {
      body {
        background: #ffffff !important;
        padding: 0 !important;
        margin: 0 !important;
      }
      .no-print-bar {
        display: none !important;
      }
      @page {
        size: A4 portrait;
        margin: 8mm 10mm 8mm 10mm;
      }
      .document-container {
        width: 100% !important;
        padding: 0 !important;
        box-shadow: none !important;
      }
    }
  </style>
</head>
<body>

  <div class="no-print-bar">
    <div>
      <h3>DUQUE IA — Formulário Oficial de Avaliação e Auditoria A4 (23 Casos)</h3>
      <span style="font-size: 8pt; opacity: 0.85;">Versão com Perguntas, Novas Respostas Reais da IA e Espaço para Caneta</span>
    </div>
    <button class="print-btn" onclick="window.print()">🖨️ Imprimir / Salvar em PDF</button>
  </div>

  <div class="document-container">

    <div class="doc-header">
      <div class="doc-header-left">
        <h1>DUQUE IA — Formulário de Avaliação das Novas Respostas</h1>
        <p>Sistema de Informações Municipais e Ouvidoria de Duque de Caxias / RJ — Auditoria Prática (Casos 01 a 23)</p>
      </div>
      <div class="doc-header-right">
        <strong>Data:</strong> 23/10/2026<br>
        <strong>Ambiente:</strong> Produção / Regras Atualizadas
      </div>
    </div>
"""

for c in cases_data:
    cid = c["id"]
    titulo = c["titulo"]
    pergunta = c["pergunta"]
    hist = c.get("history", [])
    comportamento_ant = c.get("comportamento_anterior", "")
    nova_res = c.get("nova_resposta", {})
    nova_ans = nova_res.get("answer", "")
    nova_ans_html = md_to_html(nova_ans)
    
    badge_cls = "badge-ouro" if cid in [2, 3, 23] else "badge-revisado"
    badge_label = "PADRÃO OURO" if cid in [2, 3, 23] else "RESPOSTA ATUALIZADA"

    hist_html = ""
    if hist:
        hist_html = f'<div style="font-size: 7.2pt; color: #64748b; margin-top: 2px;"><em>Histórico recente: {" | ".join(hist)}</em></div>'

    html_content += f"""
    <!-- CASO {cid:02d} -->
    <div class="case-card">
      <div class="case-header">
        <div class="case-title">Caso {cid:02d} — {titulo}</div>
        <div class="status-badge {badge_cls}">{badge_label}</div>
      </div>
      <div class="case-body">

        <!-- PERGUNTA DO MUNÍCIPE -->
        <div class="block-section">
          <div class="label label-query">🗣️ PERGUNTA DO MUNÍCIPE</div>
          <div class="query-text">"{pergunta}"{hist_html}</div>
        </div>

        <!-- NOVA RESPOSTA DA IA -->
        <div class="block-section">
          <div class="label label-new-ans">🤖 NOVA RESPOSTA ATUAL DO DUQUE IA (PARA SUA AVALIAÇÃO)</div>
          <div class="new-answer-box">
            {nova_ans_html}
          </div>
        </div>

        <!-- RESPOSTA ANTERIOR PARA CONFRONTO -->
        <div class="block-section">
          <div class="label label-old-ans">⚠️ COMPORTAMENTO ANTERIOR AUDITADO (FALHA CORRIGIDA)</div>
          <div class="old-answer-box">
            {comportamento_ant}
          </div>
        </div>

        <!-- CAMPO PARA CANETA DO AVALIADOR -->
        <div class="handwritten-box">
          <span class="label label-notes">✍️ SUAS ANOTAÇÕES / OBSERVAÇÕES MANUAIS (AVALIAÇÃO):</span>
          <div class="handwritten-lines">
            <div class="line"></div>
            <div class="line"></div>
          </div>
        </div>

      </div>
    </div>
    """

html_content += """
  </div>
</body>
</html>
"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"[OK] HTML A4 gerado com sucesso em: {html_path}")

# Conversão headless para PDF via Chrome
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if os.path.exists(chrome_path):
    print(f"Gerando PDF de alta resolução com Chrome Headless...")
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_dest_1}",
        html_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_dest_1):
        # Cria cópia em docs/ também
        import shutil
        shutil.copyfile(pdf_dest_1, pdf_dest_2)
        print(f"[SUCESSO] PDF gerado perfeitamente:")
        print(f" -> {pdf_dest_1} ({os.path.getsize(pdf_dest_1)} bytes)")
        print(f" -> {pdf_dest_2}")
    else:
        print(f"[ERRO] Falha ao criar PDF: {res.stderr}")
else:
    print(f"Chrome não encontrado no caminho padrão: {chrome_path}")
