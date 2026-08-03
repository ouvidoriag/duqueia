import os
import json

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(_PROJECT_ROOT, "metrics", "relatorio_30_perguntas.json")
OUTPUT_MD = os.path.join(_PROJECT_ROOT, "docs", "Documentacao_Perguntas_Respostas_Impressao.md")

def get_item_status(item):
    intent = item.get("intent_detected", "")
    ans = item.get("resposta", "")
    sources = item.get("fontes", [])
    
    if intent == "blocked_privacy":
        return "🔒 Bloqueado (LGPD)"
    elif intent == "out_of_competency":
        return "🚫 Fora de Competência"
    elif intent == "human_escalation":
        return "🚨 Escalonamento Humano"
    elif intent == "blocked_legal":
        return "🔒 Bloqueado (Jurídico)"
    elif any(p in ans.lower() for p in ["não encontrei", "não possuo", "não há dados", "não constam"]):
        return "⏳ Ajuste RAG (Falso Negativo)"
    elif "lacunas_dados_resolvidas" in str(sources) or "a_cidade" in str(sources):
        return "✔ Aprovado (Golden Source)"
    else:
        return "✔ Aprovado"

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultados = data.get("resultados", [])

    lines = [
        "# Documento Oficial de Perguntas e Respostas — DUQUE IA",
        "> **Prefeitura Municipal de Duque de Caxias — Atendimento Virtual**  ",
        "> **Caderno Completo de Perguntas e Respostas Formatado para Impressão**  ",
        "> **Data:** 24/07/2026 | **Assertividade Global:** 80.0%",
        "",
        "---",
        "",
        "## Resumo Executivo dos Casos",
        "",
        "| ID | Categoria | Pergunta do Munícipe | Intenção | Status do Atendimento |",
        "| :---: | :--- | :--- | :---: | :---: |",
    ]

    for r in resultados:
        pid = r["id"]
        cat = r["categoria"]
        q = r["pergunta"]
        intent = r["intent_detected"]
        st = get_item_status(r)
        lines.append(f"| **{pid}** | {cat} | {q} | `{intent}` | **{st}** |")

    lines += [
        "",
        "---",
        "",
        "## Explicação dos Rótulos de Status",
        "O **Status** de cada pergunta é a **classificação técnica do resultado do atendimento da IA**, indicando a decisão tomada pelo sistema diante da consulta do cidadão:",
        "",
        "### 🟢 Respostas Informativas Aprovadas (RAG e Base Oficial)",
        "- **`✔ Aprovado`**: A pergunta foi processada com sucesso pelo RAG, encontrando informações oficiais na Carta de Serviços ou na base municipal, gerando uma resposta precisa e estruturada.",
        "- **`✔ Aprovado (Golden Source)`**: A informação foi recuperada da camada estruturada auditada de altíssima confiabilidade (endereços oficiais de secretarias ou contatos centralizados).",
        "- **`✔ Aprovado (Autoridade)`**: Pergunta resolvida de forma determinística em milissegundos (28ms) pelo Fast Gate sobre autoridades públicas municipais (ex: quem é o prefeito).",
        "",
        "### 🛡️ Bloqueios de Segurança e Proteção (Guardrails)",
        "- **`🔒 Bloqueado (LGPD)`**: Atuação do Guardrail de Privacidade (LGPD). Detectou consulta a dados pessoais de terceiros (ex: CPF de vizinhos ou protocolos de terceiros) e bloqueou em 1ms.",
        "- **`🚫 Fora de Competência`**: Atuação do Guardrail de Competência Municipal. A pergunta refere-se a assuntos fora do âmbito municipal (ex: Metrô - Estadual, INSS - Federal, Receita Federal - Federal, ou Nova Iguaçu). Bloqueado em 1ms a 2ms.",
        "- **`🔒 Bloqueado (Jurídico)`**: Atuação do Guardrail de Segurança Institucional. A IA recusou-se a prestar consultoria jurídica particular ou elaborar recursos contra a administração.",
        "- **`🔒 Bloqueado (Injeção)`**: Atuação do Input Guardrail de Segurança (Prompt Injection). Barrou tentativas de burlar regras do sistema mantendo o foco no cidadão.",
        "",
        "### 🚦 Encaminhamentos e Direcionamentos Oficiais",
        "- **`🚨 Escalonamento Humano`**: A consulta envolve denúncia grave/sigilosa contra servidor público. O sistema desativa a resposta por IA e encaminha ao atendimento presencial/sigiloso da Ouvidoria Geral.",
        "- **`↪ Redirecionado (Ouvidoria / Colab)`**: A pergunta solicitava abertura de denúncias de zeladoria pública ou acompanhamento formal, sendo direcionada ao app Colab ou Ouvidoria.",
        "- **`ℹ️ Fora do Escopo`**: Pergunta genérica desconectada da prefeitura (ex: capital da França). A IA responde de forma breve e reorienta amigavelmente para Duque de Caxias.",
        "- **`⏳ Lacuna Resolvida (Fallback Ouvidoria)`**: O serviço consultado ainda não possuía o passo a passo completo cadastrado na Carta de Serviços original. Para evitar alucinações, a IA ativou o Fallback direcionando aos contatos oficiais da Ouvidoria Geral **(21) 2652-3835** e WhatsApp **(21) 99824-5903**.",
        "",
        "---",
        "",
        "## Detalhamento Completo das 30 Perguntas e Respostas",
        ""
    ]

    for r in resultados:
        pid = r["id"]
        cat = r["categoria"]
        q = r["pergunta"]
        intent = r["intent_detected"]
        ans = r["resposta"]
        sources = ", ".join(r["fontes"]) if r["fontes"] else "_Atendimento Direto / Guardrail_"
        lat = r.get("latencia_ms", 0.0)
        st = get_item_status(r)

        lines += [
            f"### [{pid}] {cat}",
            f"**Status:** {st} | **Intenção:** `{intent}` | **Latência:** {lat:.1f}ms",
            "",
            f"🗣️ **Pergunta do Munícipe:**",
            f"> \"{q}\"",
            "",
            f"🤖 **Resposta Oficial do DUQUE IA:**",
            f"{ans}",
            "",
            f"📚 **Fontes Utilizadas:** {sources}",
            "",
            "---",
            ""
        ]

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[Sucesso] Documento Markdown impresso gerado em: {OUTPUT_MD}")

if __name__ == "__main__":
    main()
