# -*- coding: utf-8 -*-
"""
build_dossier_documents.py — DUQUE IA
======================================
Compila todas as 102 perguntas e respostas geradas pelo DUQUE IA em:
1. docs/DOSSIE_COMPLETO_TODAS_AS_PERGUNTAS_E_RESPOSTAS.md
2. docs/relatorio_todas_as_perguntas_a4.html
3. docs/DUQUE_IA_DOSSIE_COMPLETO_PERGUNTAS_E_RESPOSTAS.pdf (e cópia na raiz)

Inclui métricas executivas, tempo de resposta, grau de confiança,
modelo Gemini utilizado e formatação visual padrão A4 de alta qualidade.
"""

import os
import sys
import json
import re
import html
import shutil
import subprocess

# Configurar stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_JSON = os.path.join(ROOT, "data", "resultados_todas_as_perguntas.json")
OUTPUT_MD = os.path.join(ROOT, "docs", "DOSSIE_COMPLETO_TODAS_AS_PERGUNTAS_E_RESPOSTAS.md")
OUTPUT_HTML = os.path.join(ROOT, "docs", "relatorio_todas_as_perguntas_a4.html")
OUTPUT_PDF = os.path.join(ROOT, "docs", "DUQUE_IA_DOSSIE_COMPLETO_PERGUNTAS_E_RESPOSTAS.pdf")
ROOT_PDF = os.path.join(ROOT, "DUQUE_IA_DOSSIE_COMPLETO_PERGUNTAS_E_RESPOSTAS.pdf")


def markdown_to_html_simple(text: str) -> str:
    """Converte markdown básico em HTML seguro para renderização no A4."""
    if not text:
        return ""
    
    # Escapar caracteres HTML básicos
    t = html.escape(text)
    
    # Cabeçalhos
    t = re.sub(r"^### (.*)$", r"<h4 class='ans-h4'>\1</h4>", t, flags=re.MULTILINE)
    t = re.sub(r"^## (.*)$", r"<h3 class='ans-h3'>\1</h3>", t, flags=re.MULTILINE)
    t = re.sub(r"^# (.*)$", r"<h2 class='ans-h2'>\1</h2>", t, flags=re.MULTILINE)
    
    # Negrito e Itálico
    t = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.*?)\*", r"<em>\1</em>", t)
    
    # Links
    t = re.sub(r"\[(.*?)\]\((.*?)\)", r"<a href='\2' target='_blank'>\1</a>", t)
    
    # Listas
    lines = t.split("\n")
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("* ") or stripped.startswith("- "):
            if not in_list:
                new_lines.append("<ul class='ans-ul'>")
                in_list = True
            item_text = stripped[2:]
            new_lines.append(f"<li>{item_text}</li>")
        else:
            if in_list:
                new_lines.append("</ul>")
                in_list = False
            if stripped == "---":
                new_lines.append("<hr class='ans-hr'/>")
            elif stripped:
                new_lines.append(f"<p class='ans-p'>{stripped}</p>")
            else:
                new_lines.append("<div class='ans-spacing'></div>")
    if in_list:
        new_lines.append("</ul>")
        
    return "\n".join(new_lines)


def generate_markdown(items):
    total = len(items)
    ok_count = sum(1 for x in items if x.get("status") == "OK")
    avg_latency = sum(x.get("elapsed_seconds", 0) for x in items) / total if total else 0
    avg_conf = sum(x.get("confidence", 0) for x in items) / total if total else 0

    lines = [
        "# DUQUE IA — DOSSIÊ COMPLETO DE PERGUNTAS E RESPOSTAS DO MUNICÍPIO",
        "## Avaliação Holística do Pipeline RAG com Gemini 3.8 Flash e Guardrails Oficiais",
        "",
        "> **Prefeitura Municipal de Duque de Caxias — Estado do Rio de Janeiro**  ",
        f"> **Total de Casos Consolidados:** {total} Perguntas  ",
        f"> **Taxa de Conclusão / Sucesso:** {ok_count}/{total} ({ok_count/total*100:.1f}%)  ",
        f"> **Latência Média Global:** {avg_latency:.2f}s  ",
        f"> **Confiança Média:** {avg_conf:.2f} / 1.00  ",
        f"> **Modelo Principal de Geração:** `gemini-3.8-flash` (Interactions API / REST v1beta)  ",
        f"> **Modelo de Triagem Rápida:** `gemini-3.1-flash-lite`  ",
        f"> **Modelo de Embeddings:** `gemini-embedding-2` (3.072 dimensões)  ",
        "",
        "---",
        "",
        "## 1. Sumário Executivo e Metodologia",
        "",
        "Este documento consolida a totalidade das avaliações do **DUQUE IA**, unificando:",
        "1. **23 Casos Canônicos da Ouvidoria Geral:** Casos oficiais de atendimento direto ao munícipe (saúde, fazendinha do autista, alvarás, animais, barulho, zeladoria, etc.).",
        "2. **20 Casos da Bateria de Estresse e Segurança:** Perguntas ambíguas, informais com gírias e erros de digitação, tentativas de quebra de competência (estadual/federal) e violação de privacidade (LGPD).",
        "3. **30 Casos do FAQ Oficial do Cidadão:** Serviços de rotina (tapa-buraco, iluminação pública, limpeza de rios, aplicativo Colab, IPTU, taxa de lixo, matrículas).",
        "4. **10 Casos de Órgãos Externos e Concessionárias:** Direcionamento preciso para Enel, Águas do Rio, Detran, INSS, IPMDC e feiras livres.",
        "5. **19 Casos de Benchmark RAG e GIS:** Consultas institucionais, secretarias, bairros, distritos e legislação municipal.",
        "",
        "---",
        "",
        "## 2. Índice Rápido de Perguntas",
        "",
        "| ID | Origem / Subgrupo | Título do Caso | Latência | Confiança | Status |",
        "| :--- | :--- | :--- | :---: | :---: | :---: |"
    ]

    for item in items:
        q_id = item.get("id", "")
        origem = item.get("origem", "")
        titulo = item.get("titulo", "")
        lat = item.get("elapsed_seconds", 0)
        conf = item.get("confidence", 0)
        st = item.get("status", "OK")
        lines.append(f"| [{q_id}](#{q_id.lower()}) | {origem} | {titulo} | {lat:.2f}s | {conf:.2f} | `{st}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Respostas Detalhadas Caso a Caso",
        ""
    ])

    # Agrupa por subgrupo para melhor navegação
    subgrupos = {}
    for item in items:
        sg = item.get("subgrupo", "Geral")
        if sg not in subgrupos:
            subgrupos[sg] = []
        subgrupos[sg].append(item)

    for sg, sg_items in subgrupos.items():
        lines.append(f"\n### 📁 Subgrupo: {sg} ({len(sg_items)} casos)\n")
        for it in sg_items:
            q_id = it.get("id", "")
            titulo = it.get("titulo", "")
            query = it.get("query", "")
            criterio = it.get("criterio", "")
            answer = it.get("answer", "")
            conf = it.get("confidence", 0.0)
            intent = it.get("intent_detected", "unknown")
            lat = it.get("elapsed_seconds", 0)
            sources = it.get("sources", [])

            lines.append(f"#### <a id='{q_id.lower()}'></a>[{q_id}] {titulo}")
            lines.append(f"- **Origem:** {it.get('origem', '')} | **Subgrupo:** {sg}")
            lines.append(f"- **Pergunta do Cidadão:** `{query}`")
            if criterio:
                lines.append(f"- **Critério Esperado:** *{criterio}*")
            lines.append(f"- **Metadados de Execução:** Latência: `{lat:.2f}s` | Confiança: `{conf:.2f}` | Intenção: `{intent}` | Fontes: `{len(sources)}`")
            lines.append("")
            lines.append("**Resposta Oficial do DUQUE IA:**")
            lines.append("")
            lines.append(answer)
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def generate_html(items):
    total = len(items)
    ok_count = sum(1 for x in items if x.get("status") == "OK")
    avg_latency = sum(x.get("elapsed_seconds", 0) for x in items) / total if total else 0
    avg_conf = sum(x.get("confidence", 0) for x in items) / total if total else 0

    cards_html = []
    for idx, it in enumerate(items, 1):
        q_id = it.get("id", "")
        origem = it.get("origem", "")
        subgrupo = it.get("subgrupo", "")
        titulo = it.get("titulo", "")
        query = it.get("query", "")
        criterio = it.get("criterio", "")
        answer = it.get("answer", "")
        conf = it.get("confidence", 0.0)
        intent = it.get("intent_detected", "unknown")
        lat = it.get("elapsed_seconds", 0)
        sources_cnt = it.get("sources_count", 0)

        badge_class = "badge-success" if it.get("status") == "OK" else "badge-error"
        conf_badge = "conf-high" if conf >= 0.8 else ("conf-med" if conf >= 0.5 else "conf-low")
        answer_rendered = markdown_to_html_simple(answer)

        card = f"""
        <div class="case-card" id="case-{q_id}">
          <div class="card-header">
            <div class="card-title-group">
              <span class="case-id">#{q_id}</span>
              <span class="case-title">{html.escape(titulo)}</span>
            </div>
            <div class="card-badges">
              <span class="badge {badge_class}">STATUS: {it.get('status', 'OK')}</span>
              <span class="badge {conf_badge}">CONFIANÇA: {conf:.2f}</span>
              <span class="badge badge-neutral">{lat:.2f}s</span>
            </div>
          </div>
          
          <div class="meta-strip">
            <span><strong>Origem:</strong> {html.escape(origem)}</span>
            <span><strong>Subgrupo:</strong> {html.escape(subgrupo)}</span>
            <span><strong>Intenção:</strong> <code>{html.escape(intent)}</code></span>
            <span><strong>Fontes:</strong> {sources_cnt}</span>
          </div>

          <div class="query-box">
            <div class="box-label"><span class="icon">💬</span> Pergunta do Munícipe:</div>
            <div class="query-text">"{html.escape(query)}"</div>
          </div>

          {f'<div class="crit-box"><span class="box-label">🎯 Critério Avaliado:</span> {html.escape(criterio)}</div>' if criterio else ''}

          <div class="answer-box">
            <div class="box-label"><span class="icon">🤖</span> Resposta Gerada pelo DUQUE IA (Gemini 3.8 Flash):</div>
            <div class="answer-content">
              {answer_rendered}
            </div>
          </div>
        </div>
        """
        cards_html.append(card)

    cards_joined = "\n".join(cards_html)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>DUQUE IA — Dossiê Completo de Perguntas e Respostas</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 10mm 12mm 12mm 12mm;
    }}
    * {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}
    body {{
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
      color: #0f172a;
      background-color: #f8fafc;
      margin: 0;
      padding: 0;
      font-size: 8.5pt;
      line-height: 1.4;
    }}
    .page-container {{
      width: 100%;
      max-width: 186mm;
      margin: 0 auto;
      background: #ffffff;
      padding: 8mm 10mm;
    }}
    
    /* Header Institucional */
    .header-table {{
      width: 100%;
      border-bottom: 2px solid #1e3a8a;
      padding-bottom: 10px;
      margin-bottom: 14px;
    }}
    .inst-title {{
      font-size: 13pt;
      font-weight: 800;
      color: #1e3a8a;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin: 0;
    }}
    .inst-sub {{
      font-size: 8.5pt;
      color: #475569;
      font-weight: 600;
      margin: 2px 0 0 0;
    }}
    .doc-badge {{
      display: inline-block;
      background: #eff6ff;
      color: #1d4ed8;
      border: 1px solid #bfdbfe;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 7.5pt;
      font-weight: 700;
    }}
    
    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 14px;
    }}
    .kpi-card {{
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 8px;
      text-align: center;
    }}
    .kpi-val {{
      font-size: 14pt;
      font-weight: 800;
      color: #1e3a8a;
      margin-bottom: 2px;
    }}
    .kpi-lbl {{
      font-size: 7pt;
      color: #64748b;
      font-weight: 600;
      text-transform: uppercase;
    }}

    /* Specs Banner */
    .specs-banner {{
      background: #0f172a;
      color: #f8fafc;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 8pt;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .specs-item {{
      display: inline-block;
      margin-right: 14px;
    }}
    .specs-item strong {{
      color: #38bdf8;
    }}

    /* Case Card */
    .case-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px 12px;
      margin-bottom: 12px;
      page-break-inside: avoid;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 6px;
      margin-bottom: 6px;
    }}
    .card-title-group {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .case-id {{
      background: #1e3a8a;
      color: #ffffff;
      padding: 2px 6px;
      border-radius: 3px;
      font-weight: 800;
      font-size: 8pt;
    }}
    .case-title {{
      font-weight: 700;
      font-size: 9pt;
      color: #0f172a;
    }}
    .card-badges {{
      display: flex;
      gap: 4px;
    }}
    .badge {{
      font-size: 7pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 3px;
    }}
    .badge-success {{ background: #dcfce7; color: #15803d; }}
    .badge-error {{ background: #fee2e2; color: #b91c1c; }}
    .badge-neutral {{ background: #f1f5f9; color: #475569; }}
    .conf-high {{ background: #dbeafe; color: #1e40af; }}
    .conf-med {{ background: #fef3c7; color: #92400e; }}
    .conf-low {{ background: #fee2e2; color: #991b1b; }}

    .meta-strip {{
      font-size: 7pt;
      color: #64748b;
      margin-bottom: 8px;
      display: flex;
      gap: 12px;
      background: #f8fafc;
      padding: 3px 6px;
      border-radius: 4px;
    }}
    .meta-strip code {{
      background: #e2e8f0;
      padding: 1px 3px;
      border-radius: 2px;
      color: #334155;
    }}

    .query-box {{
      background: #f8fafc;
      border-left: 3px solid #0284c7;
      padding: 6px 10px;
      margin-bottom: 6px;
      border-radius: 0 4px 4px 0;
    }}
    .crit-box {{
      font-size: 7.5pt;
      color: #475569;
      background: #fefce8;
      border: 1px dashed #fef08a;
      padding: 4px 8px;
      margin-bottom: 6px;
      border-radius: 4px;
    }}
    .box-label {{
      font-size: 7pt;
      font-weight: 700;
      text-transform: uppercase;
      color: #64748b;
      margin-bottom: 2px;
    }}
    .query-text {{
      font-size: 8.5pt;
      font-weight: 600;
      color: #0369a1;
      font-style: italic;
    }}

    .answer-box {{
      background: #ffffff;
      border-left: 3px solid #16a34a;
      padding: 6px 10px;
      border-radius: 0 4px 4px 0;
    }}
    .answer-content {{
      font-size: 8.5pt;
      color: #1e293b;
      line-height: 1.45;
    }}
    .ans-p {{
      margin: 3px 0;
    }}
    .ans-ul {{
      margin: 3px 0 3px 16px;
      padding: 0;
    }}
    .ans-ul li {{
      margin-bottom: 2px;
    }}
    .ans-h2, .ans-h3, .ans-h4 {{
      color: #1e3a8a;
      font-weight: 700;
      margin: 6px 0 2px 0;
      font-size: 8.5pt;
    }}
    .ans-hr {{
      border: 0;
      border-top: 1px solid #e2e8f0;
      margin: 6px 0;
    }}
    .ans-spacing {{
      height: 4px;
    }}

    /* Footer */
    .doc-footer {{
      border-top: 1px solid #cbd5e1;
      padding-top: 8px;
      margin-top: 16px;
      font-size: 7.5pt;
      color: #64748b;
      display: flex;
      justify-content: space-between;
    }}
  </style>
</head>
<body>
  <div class="page-container">
    
    <!-- Cabeçalho -->
    <table class="header-table">
      <tr>
        <td style="vertical-align: middle;">
          <h1 class="inst-title">Prefeitura Municipal de Duque de Caxias</h1>
          <p class="inst-sub">DUQUE IA — Dossiê Holístico de Avaliação e Desempenho (102 Perguntas)</p>
        </td>
        <td style="text-align: right; vertical-align: middle;">
          <span class="doc-badge">RELATÓRIO OFICIAL DE HOMOLOGAÇÃO</span><br>
          <span style="font-size: 7.5pt; color: #64748b;">Novembro / 2026</span>
        </td>
      </tr>
    </table>

    <!-- Specs Banner -->
    <div class="specs-banner">
      <div class="specs-item">Modelo de Geração: <strong>gemini-3.8-flash</strong></div>
      <div class="specs-item">Triagem Contextual: <strong>gemini-3.1-flash-lite</strong></div>
      <div class="specs-item">Espaço Vetorial: <strong>gemini-embedding-2 (3.072d)</strong></div>
      <div class="specs-item">Modo: <strong>Produção Multi-Tenant Híbrido</strong></div>
    </div>

    <!-- KPI Grid -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-val">{total}</div>
        <div class="kpi-lbl">Perguntas Avaliadas</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{ok_count/total*100:.1f}%</div>
        <div class="kpi-lbl">Taxa de Sucesso ({ok_count}/{total})</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{avg_latency:.2f}s</div>
        <div class="kpi-lbl">Latência Média</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{avg_conf:.2f}</div>
        <div class="kpi-lbl">Confiança Média</div>
      </div>
    </div>

    <!-- Lista de Casos e Respostas -->
    {cards_joined}

    <!-- Rodapé -->
    <div class="doc-footer">
      <span>Sistema de Atendimento Cidadão — DUQUE IA • Prefeitura de Duque de Caxias / RJ</span>
      <span>Documento gerado automaticamente pelo pipeline de auditoria e conformidade RAG</span>
    </div>

  </div>
</body>
</html>
"""
    return html_content


def compile_dossier():
    print("=" * 70)
    print("DUQUE IA - COMPILAÇÃO DE DOCUMENTOS DO DOSSIÊ (MD, HTML, PDF)")
    print("=" * 70)

    if not os.path.exists(INPUT_JSON):
        print(f"ERRO: Arquivo {INPUT_JSON} não encontrado!")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        items = json.load(f)

    total = len(items)
    print(f"Total de itens carregados do JSON: {total}")

    # 1. Gerar Markdown
    print("[1/3] Gerando Dossiê Markdown...")
    md_content = generate_markdown(items)
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  -> Salvo em: {OUTPUT_MD} ({os.path.getsize(OUTPUT_MD)} bytes)")

    # 2. Gerar HTML
    print("[2/3] Gerando Relatório A4 HTML...")
    html_content = generate_html(items)
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  -> Salvo em: {OUTPUT_HTML} ({os.path.getsize(OUTPUT_HTML)} bytes)")

    # 3. Gerar PDF via Headless Browser
    print("[3/3] Compilando Dossiê em PDF de Alta Resolução...")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    browser = chrome_path if os.path.exists(chrome_path) else edge_path

    if not os.path.exists(browser):
        print(f"[AVISO] Nenhum navegador headless encontrado. PDF não pôde ser gerado.")
        return

    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUTPUT_PDF}",
        OUTPUT_HTML
    ]
    subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(OUTPUT_PDF) and os.path.getsize(OUTPUT_PDF) > 0:
        shutil.copyfile(OUTPUT_PDF, ROOT_PDF)
        print(f"  -> PDF Oficial Gerado: {OUTPUT_PDF} ({os.path.getsize(OUTPUT_PDF)} bytes)")
        print(f"  -> Cópia na Raiz: {ROOT_PDF}")
    else:
        print("[ERRO] Falha ao compilar PDF.")

    print("=" * 70)
    print("PROCESSO DE COMPILAÇÃO CONCLUÍDO COM SUCESSO!")
    print("=" * 70)


if __name__ == "__main__":
    compile_dossier()

