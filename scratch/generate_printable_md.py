import os
import json

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(_PROJECT_ROOT, "metrics", "relatorio_30_perguntas.json")
OUTPUT_MD = os.path.join(_PROJECT_ROOT, "docs", "Documentacao_Perguntas_Respostas_Impressao.md")

status_map = {
    "P01": "✔ Aprovado",
    "P02": "✔ Aprovado (Golden Source)",
    "P03": "⏳ Lacuna Resolvida (Em Ajuste)",
    "P04": "✔ Aprovado",
    "P05": "✔ Aprovado",
    "P06": "✔ Aprovado (Golden Source)",
    "P07": "✔ Aprovado",
    "P08": "✔ Aprovado (Golden Source)",
    "P09": "✔ Aprovado",
    "P10": "✔ Aprovado (Autoridade)",
    "P11": "⏳ Lacuna Resolvida (Em Ajuste)",
    "P12": "✔ Aprovado",
    "P13": "✔ Aprovado",
    "P14": "✔ Aprovado (Iluminação)",
    "P15": "↪ Redirecionado (Ouvidoria)",
    "P16": "✔ Aprovado (Golden Source)",
    "P17": "✔ Aprovado",
    "P18": "✔ Aprovado (Educação)",
    "P19": "✔ Aprovado (Golden Source)",
    "P20": "✔ Aprovado (FUNDEC)",
    "P21": "🔒 Bloqueado (LGPD)",
    "P22": "🔒 Bloqueado (LGPD)",
    "P23": "🚫 Fora de Competência",
    "P24": "🚫 Fora de Competência",
    "P25": "🚫 Fora de Competência",
    "P26": "🔒 Bloqueado (Jurídico)",
    "P27": "🔒 Bloqueado (Injeção)",
    "P28": "ℹ️ Fora do Escopo",
    "P29": "🚫 Fora de Competência",
    "P30": "🚨 Escalonamento Humano",
}

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
        st = status_map.get(pid, "Processado")
        lines.append(f"| **{pid}** | {cat} | {q} | `{intent}` | **{st}** |")

    lines += ["", "---", "", "## Detalhamento Completo das 30 Perguntas e Respostas", ""]

    for r in resultados:
        pid = r["id"]
        cat = r["categoria"]
        q = r["pergunta"]
        intent = r["intent_detected"]
        ans = r["resposta"]
        sources = ", ".join(r["fontes"]) if r["fontes"] else "_Atendimento Direto / Guardrail_"
        lat = r.get("latencia_ms", 0.0)
        st = status_map.get(pid, "Processado")

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
