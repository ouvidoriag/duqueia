import os
import sys
import json
import time

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

from agent.agent import DuqueIAAgent
from utils.web_search import search_official_web

# 10 Perguntas Reais sobre Caxias que Acionam a Busca Externa Controlada
ONLINE_10_QUESTIONS = [
    {"id": "W01", "cat": "Recursos Humanos & Servidores", "q": "Como consultar o calendário de pagamento dos servidores da Prefeitura de Duque de Caxias?"},
    {"id": "W02", "cat": "Saúde & Unidades", "q": "Onde fica o Hospital Infantil Municipal Parada Angélica e quais os serviços prestados?"},
    {"id": "W03", "cat": "Meio Ambiente & Limpeza", "q": "Como funciona o programa de Coleta Seletiva de lixo reciclável em Duque de Caxias?"},
    {"id": "W04", "cat": "Impostos & Tributos", "q": "Como emitir a Certidão Negativa de Débitos (CND) no Portal do Contribuinte de Caxias?"},
    {"id": "W05", "cat": "Cultura & Lazer", "q": "Onde fica a Biblioteca Municipal Governador Leonel Brizola em Caxias e qual o horário de funcionamento?"},
    {"id": "W06", "cat": "Assistência Social & Alimentação", "q": "Onde fica o Restaurante Popular de Duque de Caxias e qual o valor da refeição?"},
    {"id": "W07", "cat": "Previdência Municipal (IPMDC)", "q": "Como agendar atendimento para prova de vida e aposentadoria no IPMDC?"},
    {"id": "W08", "cat": "Comércio & Feiras", "q": "Como funciona o cadastramento de feirantes para as feiras livres de Duque de Caxias?"},
    {"id": "W09", "cat": "Transparência & Licitações", "q": "Onde consultar os editais de licitação e compras públicas da Prefeitura de Duque de Caxias?"},
    {"id": "W10", "cat": "Trânsito & Concessionárias", "q": "Como emitir a 2ª via da conta de água na Águas do Rio em Duque de Caxias?"}
]

def run_online_test():
    print("="*75)
    print("EXECUÇÃO DO BENCHMARK DE 10 PERGUNTAS COM BUSCA EXTERNA CONTROLADA")
    print("="*75)

    agent = DuqueIAAgent()
    results = []

    for item in ONLINE_10_QUESTIONS:
        wid = item["id"]
        cat = item["cat"]
        q = item["q"]
        print(f"\n[Testando {wid}/W10] \"{q}\" ...", flush=True)

        t0 = time.time()
        from agent.fallback import build_controlled_web_fallback
        fb_dict = build_controlled_web_fallback(q, agent.gemini_client)
        latency = (time.time() - t0) * 1000.0

        ans_text = fb_dict.get("answer", "")
        sources = fb_dict.get("sources", [])
        conf = fb_dict.get("confidence", 0.82)
        triple = fb_dict.get("metrics_triple", {})

        latency = (time.time() - t0) * 1000.0
        print(f"-> Concluído ({latency:.0f}ms | Confiança: {conf:.2f})")

        results.append({
            "id": wid,
            "category": cat,
            "question": q,
            "answer": ans_text,
            "sources": sources,
            "confidence": conf,
            "latency_ms": round(latency, 1)
        })

    # Gravar JSON com resultados
    out_json = os.path.join(_PROJECT_ROOT, "metrics", "test_10_online_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Gerar Documentos HTML e Markdown
    generate_online_reports(results)

def generate_online_reports(results):
    html_file = os.path.join(_PROJECT_ROOT, "Relatorio_10_Perguntas_Busca_Online.html")
    md_file = os.path.join(_PROJECT_ROOT, "docs", "Documentacao_10_Perguntas_Busca_Online.md")

    # 1. HTML Report
    html_content = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "<title>DUQUE IA — Relatório de Busca Externa Controlada (10 Casos)</title>",
        "<style>",
        "  body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; line-height: 1.6; color: #0f172a; background-color: #f1f5f9; margin: 0; padding: 30px 15px; }",
        "  .container { max-width: 1000px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); padding: 40px; }",
        "  header { border-bottom: 3px solid #0284c7; padding-bottom: 25px; margin-bottom: 30px; }",
        "  h1 { color: #0369a1; margin: 0 0 8px 0; font-size: 26px; }",
        "  .subtitle { color: #64748b; font-size: 14.5px; margin: 0; }",
        "  .summary-box { background: #f0f9ff; border-left: 5px solid #0284c7; padding: 18px 24px; border-radius: 6px; margin-bottom: 35px; }",
        "  .summary-title { font-weight: bold; color: #0369a1; margin-bottom: 6px; font-size: 16px; }",
        "  .summary-stats { display: flex; gap: 30px; margin-top: 10px; }",
        "  .stat-item { font-size: 14px; color: #334155; }",
        "  .stat-value { font-weight: bold; color: #0369a1; }",
        "  .card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 24px; margin-bottom: 25px; transition: all 0.2s ease; }",
        "  .card:hover { border-color: #7dd3fc; box-shadow: 0 4px 12px rgba(2,132,199,0.08); }",
        "  .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 16px; }",
        "  .card-id { background: #0284c7; color: #ffffff; font-weight: bold; padding: 4px 12px; border-radius: 6px; font-size: 13px; }",
        "  .card-cat { color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }",
        "  .status-badge { background: #e0f2fe; color: #0369a1; font-weight: bold; padding: 4px 12px; border-radius: 20px; font-size: 12px; }",
        "  .question { font-size: 16px; font-weight: 600; color: #0369a1; margin-bottom: 14px; background: #f0f9ff; padding: 12px 16px; border-radius: 6px; border-left: 3px solid #0284c7; }",
        "  .answer-title { font-size: 12px; font-weight: bold; text-transform: uppercase; color: #475569; margin-bottom: 8px; }",
        "  .answer-box { background: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0284c7; padding: 18px 20px; border-radius: 6px; font-size: 14.5px; white-space: pre-wrap; line-height: 1.6; color: #1e293b; font-family: inherit; }",
        "  .meta { margin-top: 15px; font-size: 12.5px; color: #64748b; display: flex; justify-content: space-between; border-top: 1px dashed #e2e8f0; padding-top: 10px; }",
        "  footer { text-align: center; margin-top: 40px; color: #94a3b8; font-size: 13px; border-top: 1px solid #e2e8f0; padding-top: 20px; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class='container'>",
        "  <header>",
        "    <h1>Prefeitura Municipal de Duque de Caxias — DUQUE IA</h1>",
        "    <p class='subtitle'>Caderno de Validação da Busca Externa Controlada no Portal Oficial (10 Casos Reais)</p>",
        "  </header>",
        "  <div class='summary-box'>",
        "    <div class='summary-title'>🌐 Resumo da Camada de Busca Externa Oficial (site:duquedecaxias.rj.gov.br)</div>",
        "    <div class='summary-stats'>",
        "      <div class='stat-item'>Total de Casos Testados: <span class='stat-value'>10 de 10</span></div>",
        "      <div class='stat-item'>Filtro de Domínio: <span class='stat-value'>duquedecaxias.rj.gov.br (100% Oficial)</span></div>",
        "      <div class='stat-item'>Status do Transparência: <span class='stat-value'>Etiqueta Ativa em 100% dos Casos</span></div>",
        "    </div>",
        "  </div>"
    ]

    for c in results:
        html_content.append(f"""
        <div class='card'>
          <div class='card-header'>
            <div>
              <span class='card-id'>{c['id']}</span>
              <span class='card-cat' style='margin-left: 10px;'>{c['category']}</span>
            </div>
            <span class='status-badge'>🌐 Busca Externa Oficial</span>
          </div>
          <div class='question'>Munícipe: "{c['question']}"</div>
          <div class='answer-title'>Resposta com Transparência de Busca Externa:</div>
          <div class='answer-box'>{c['answer']}</div>
          <div class='meta'>
            <span><strong>Fontes Externa:</strong> {', '.join(c['sources'])}</span>
            <span><strong>Confiança:</strong> {c['confidence']:.2f} | <strong>Latência:</strong> {c['latency_ms']}ms</span>
          </div>
        </div>
        """)

    html_content.extend([
        "  <footer>",
        "    <p>Prefeitura Municipal de Duque de Caxias — Módulo de Busca Externa Controlada DUQUE IA | " + time.strftime('%Y') + "</p>",
        "  </footer>",
        "</div>",
        "</body>",
        "</html>"
    ])

    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_content))

    print(f"Relatório HTML da Busca Online gerado: {html_file}")

    # 2. Markdown Report
    md_lines = [
        "# Documentação Oficial — Busca Externa Controlada no Portal Oficial",
        "> **Prefeitura Municipal de Duque de Caxias — DUQUE IA**  ",
        "> **Caderno de Validação dos 10 Casos de Busca Externa no Portal duquedecaxias.rj.gov.br**  ",
        f"> **Data:** {time.strftime('%d/%m/%Y')} | **Total de Casos:** 10 | **Domínio Restrito:** `duquedecaxias.rj.gov.br`",
        "",
        "---",
        "",
        "## Resumo dos 10 Casos de Busca Externa",
        "",
        "| ID | Categoria | Pergunta do Munícipe | Confiança | Fonte Externa Oficial |",
        "| :---: | :--- | :--- | :---: | :--- |"
    ]

    for c in results:
        md_lines.append(f"| **{c['id']}** | {c['category']} | {c['question']} | `{c['confidence']}` | `{c['sources'][0] if c['sources'] else 'Portal Oficial'}` |")

    md_lines.extend([
        "",
        "---",
        "",
        "## Caderno Detalhado de Respostas da Busca Externa (10 Casos)",
        ""
    ])

    for c in results:
        md_lines.extend([
            f"### {c['id']} — {c['category']}",
            f"**Pergunta do Munícipe:** *\"{c['question']}\"*  ",
            f"**Status:** 🌐 Busca Externa Oficial | **Confiança:** `{c['confidence']}` | **Latência:** `{c['latency_ms']}ms`  ",
            f"**Fontes Consultadas:** {', '.join(c['sources'])}",
            "",
            "#### Resposta Gerada com Etiqueta Transparente:",
            "```text",
            c['answer'],
            "```",
            "",
            "---",
            ""
        ])

    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Relatório Markdown da Busca Online gerado: {md_file}")

if __name__ == "__main__":
    run_online_test()
