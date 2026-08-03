"""
generate_faq_print_doc.py — DUQUE IA
=====================================
Executa a suíte oficial de 28 Perguntas Frequentes (Zeladoria, Iluminação, Limpeza, Colab, Ouvidoria, IPTU, Educação/Fazendinha do Autista)
no motor do DUQUE IA (Golden Source Layer + RAG) e gera o documento impresso unificado em HTML e Markdown.
"""

import os
import sys
import json
import re
import time

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

sys.stdout.reconfigure(encoding='utf-8')

from agent.agent import DuqueIAAgent
from agent.entity_resolver import GoldenSourceResolver

FAQ_CATEGORIES = [
    {
        "categoria": "Zeladoria e Tapa-Buraco",
        "perguntas": [
            "Como faço para solicitar uma operação tapa-buraco na minha rua?",
            "Quanto tempo demora para consertarem um buraco depois da solicitação?",
            "Posso enviar fotos do buraco pelo aplicativo Colab?",
            "Como acompanhar o andamento da minha solicitação de tapa-buraco?",
            "Minha rua está sem asfalto. Como solicito pavimentação?",
            "Posso denunciar uma rua com risco de acidente por causa de buracos?"
        ]
    },
    {
        "categoria": "Iluminação Pública",
        "perguntas": [
            "Como solicitar a troca de uma lâmpada queimada?",
            "Um poste está apagado há vários dias. O que devo fazer?",
            "Como informar um poste com risco de queda?"
        ]
    },
    {
        "categoria": "Limpeza Urbana",
        "perguntas": [
            "Como solicitar limpeza de um terreno abandonado?",
            "Como pedir a retirada de entulho da minha rua?",
            "Como denunciar descarte irregular de lixo?",
            "Como solicitar poda de árvores que estão encostando na rede elétrica?"
        ]
    },
    {
        "categoria": "Aplicativo Colab",
        "perguntas": [
            "Como faço meu cadastro no aplicativo Colab?",
            "Esqueci minha senha do Colab. Como recuperar?",
            "Como acompanhar uma solicitação feita pelo Colab?",
            "Posso fazer uma reclamação de forma anônima pelo Colab?",
            "Quais serviços da Prefeitura estão disponíveis no Colab?"
        ]
    },
    {
        "categoria": "Ouvidoria e Manifestações",
        "perguntas": [
            "Qual a diferença entre reclamação, denúncia, solicitação, sugestão e elogio?",
            "Como registrar uma manifestação na Ouvidoria?",
            "Como consultar o protocolo da minha manifestação?",
            "Posso fazer uma denúncia sem informar meu nome?",
            "Quanto tempo a Prefeitura tem para responder minha manifestação?"
        ]
    },
    {
        "categoria": "IPTU e Tributos",
        "perguntas": [
            "Como emitir a segunda via do IPTU?",
            "Como consultar se tenho débitos de IPTU?",
            "Como solicitar a alteração do nome do proprietário no cadastro do IPTU?",
            "Como parcelar minha dívida de IPTU?"
        ]
    },
    {
        "categoria": "Educação e Inclusão",
        "perguntas": [
            "Como matricular meu filho na Fazendinha do Autista?",
            "Como conseguir uma vaga em uma creche municipal?",
            "Como solicitar transferência de um aluno para outra escola municipal?"
        ]
    }
]

def run_faq_generation():
    print("=" * 70)
    print("   GERANDO RESPOSTAS OFICIAIS DAS 28 PERGUNTAS FREQUENTES (DUQUE IA)")
    print("=" * 70)
    
    agent = DuqueIAAgent()
    resolver = GoldenSourceResolver()
    
    all_results = []
    
    q_count = 0
    total_q = sum(len(c["perguntas"]) for c in FAQ_CATEGORIES)
    
    for cat_item in FAQ_CATEGORIES:
        cat_name = cat_item["categoria"]
        print(f"\n--- Categoria: {cat_name} ---")
        
        cat_results = []
        for q in cat_item["perguntas"]:
            q_count += 1
            print(f"[{q_count:02d}/{total_q}] Processando: '{q}'...")
            
            t0 = time.time()
            
            # 1. Tenta Golden Source primeiro
            golden_res = resolver.resolve(q)
            if golden_res:
                ans = golden_res["answer"]
                source_type = "Golden Source Layer (0ms)"
                intent = golden_res["intent_detected"]
            else:
                # 2. Executa via DuqueIAAgent (Graph pipeline)
                from agent.graph import run_graph
                graph_res = run_graph(query=q, conversation_id=f"faq_{q_count}", history=[], agent=agent)
                ans = graph_res.get("answer", "Não foi possível obter a resposta.")
                source_type = "RAG Híbrido + Gemini"
                intent = graph_res.get("intent", "RAG_GERAL")
                
            elapsed = round((time.time() - t0) * 1000, 2)
            
            cat_results.append({
                "pergunta": q,
                "resposta": ans,
                "origem": source_type,
                "intencao": intent,
                "tempo_ms": elapsed
            })
            
            time.sleep(0.3)
            
        all_results.append({
            "categoria": cat_name,
            "itens": cat_results
        })

    # -------------------------------------------------------------------------
    # GENERATE MARKDOWN DOCUMENT
    # -------------------------------------------------------------------------
    md_output_path = os.path.join(_PROJECT_ROOT, "docs", "Perguntas_Frequentes_Oficiais.md")
    os.makedirs(os.path.dirname(md_output_path), exist_ok=True)
    
    md = []
    md.append("# Guia Oficial de Perguntas Frequentes (FAQ) — DUQUE IA")
    md.append("> **Prefeitura Municipal de Duque de Caxias — RJ**")
    md.append(f"> **Respostas Geradas pelo Agente Virtual Duque IA** | **Total:** {total_q} Perguntas")
    md.append("")
    md.append("---")
    md.append("")

    for c_res in all_results:
        cat_title = c_res["categoria"]
        md.append(f"## 📌 {cat_title}")
        md.append("")
        for idx, item in enumerate(c_res["itens"], 1):
            q = item["pergunta"]
            ans = item["resposta"]
            src = item["origem"]
            
            md.append(f"### {idx}. {q}")
            md.append(f"{ans}")
            md.append("")
            md.append(f"*Fonte: `{src}`*")
            md.append("")
        md.append("---")
        md.append("")

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    # -------------------------------------------------------------------------
    # GENERATE HTML PRINTABLE DOCUMENT
    # -------------------------------------------------------------------------
    html_output_path = os.path.join(_PROJECT_ROOT, "Documentacao_Perguntas_Frequentes_Impressao.html")
    
    html_sections = []
    
    for c_res in all_results:
        cat_title = c_res["categoria"]
        cards = []
        for idx, item in enumerate(c_res["itens"], 1):
            q = item["pergunta"]
            ans = item["resposta"]
            src = item["origem"]
            
            ans_formatted = ans.replace("\n", "<br>")
            ans_formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ans_formatted)
            ans_formatted = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', ans_formatted)

            card_html = f"""
            <div class="faq-card">
                <div class="faq-question">
                    <span class="faq-num">Q{idx:02d}</span> {q}
                </div>
                <div class="faq-answer">
                    {ans_formatted}
                </div>
                <div class="faq-meta">
                    Origem da Informação: <code>{src}</code>
                </div>
            </div>
            """
            cards.append(card_html)
            
        sec_html = f"""
        <div class="cat-section">
            <h2 class="cat-header">{cat_title}</h2>
            {"".join(cards)}
        </div>
        """
        html_sections.append(sec_html)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Guia Oficial de Perguntas Frequentes (FAQ) — DUQUE IA</title>
    <style>
        @page {{
            size: A4;
            margin: 12mm 15mm 12mm 15mm;
        }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
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
        .main-header {{
            text-align: center;
            border-bottom: 3px solid #0284c7;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .main-header h1 {{
            margin: 0;
            color: #0369a1;
            font-size: 24px;
            font-weight: bold;
        }}
        .main-header p {{
            margin: 4px 0 0 0;
            color: #64748b;
            font-size: 14px;
        }}
        .cat-section {{
            margin-bottom: 30px;
            page-break-inside: avoid;
        }}
        .cat-header {{
            background: #0284c7;
            color: #ffffff;
            padding: 8px 14px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 6px;
            margin-bottom: 14px;
            margin-top: 25px;
            page-break-after: avoid;
        }}
        .faq-card {{
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            margin-bottom: 14px;
            background: #ffffff;
            page-break-inside: avoid;
        }}
        .faq-question {{
            background: #eff6ff;
            color: #1e3a8a;
            font-weight: 600;
            padding: 10px 14px;
            border-bottom: 1px solid #bfdbfe;
            border-radius: 6px 6px 0 0;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .faq-num {{
            background: #0284c7;
            color: #ffffff;
            font-size: 11px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .faq-answer {{
            padding: 14px;
            color: #334155;
            background: #ffffff;
        }}
        .faq-meta {{
            padding: 6px 14px;
            background: #f8fafc;
            border-top: 1px dashed #e2e8f0;
            font-size: 11px;
            color: #64748b;
            border-radius: 0 0 6px 6px;
        }}
        .faq-meta code {{
            background: #e2e8f0;
            padding: 1px 5px;
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
        <div class="main-header">
            <h1>Guia Oficial de Perguntas Frequentes (FAQ) — DUQUE IA</h1>
            <p>Prefeitura Municipal de Duque de Caxias — RJ | {total_q} Respostas Oficiais</p>
        </div>

        {"".join(html_sections)}
    </div>
</body>
</html>
"""

    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("\n" + "=" * 70)
    print(f"[Sucesso] Guia Markdown gerado em: {md_output_path}")
    print(f"[Sucesso] Guia HTML imprimível gerado em: {html_output_path}")
    print("=" * 70)

if __name__ == "__main__":
    run_faq_generation()
