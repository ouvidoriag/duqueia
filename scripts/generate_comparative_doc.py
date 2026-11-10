import os
import json

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
json_path = os.path.join(_PROJECT_ROOT, "scripts", "results_23_casos_novas_respostas.json")
out_md_path = os.path.join(_PROJECT_ROOT, "docs", "COMPARATIVO_QA_23_CASOS_ANTES_E_DEPOIS.md")
artifact_path = r"C:\Users\501379.PMDC\.gemini\antigravity-ide\brain\13cbfc02-e10b-4cae-b4cf-ad573e2d647c\comparativo_qa_23_casos_antes_depois.md"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Metadados das anotações de caneta para cada caso
PEN_NOTES = {
    1: "✓ (Visto azul na Solução Técnica Recomendada)",
    2: "Circulou 'padrão estruturado' com retângulo + pergunta: 'Qual padrão estruturado ?'",
    3: "✓ (Visto azul acima do campo de anotações)",
    4: "Linha lateral com seta: 'Seguir também a mesma lógica do Caso 01 p/ mapear endereços.'",
    5: "Linha lateral com seta: '↳ isso foi retirado do documento do urbanismo?'",
    6: "Sublinhou 'mau cheiro de comércio' + 'Estabelecimento fedendo TB!' + visto ✓",
    7: "Assinatura tachada + '↳ Casos noturnos com perturbação ao sossego e ilícitos é 190.' + 'Não precisa disso. Tem que ver a regra p/ alvará do Meio Ambiente, SMU e SUOP P/ poluição sonora!'",
    8: "Linha lateral com seta: '↳ Site da Jucerja ou sites confiáveis também!'",
    9: "Linha lateral com seta: '↳ parece que esses chunks não estão bem feitos. Não estão permitindo identificar todos os dados da carta de serviços e do web scraping.'",
    10: "No Item 1 puxou seta: '& Meio Ambiente' + no campo: 'Revisar os dados da carta de serviços e Chunks.'",
    11: "Colchete em Ouvidoria + seta: 'Errado! Temos o fluxo com os concessionárias! Ver com Gildo ou Nikolas!'",
    12: "✓ (Visto azul na Solução Técnica)",
    13: "Linha lateral com seta: '↳ Tem como revisar com cuidado isso? limitar em poucas palavras pode ser perigoso ou arriscado!'",
    14: "Linha lateral com seta: '↳ Poucas palavras p/ mapear podem limitar!'",
    15: "Linha lateral com seta: '↳ De onde veio esta regra? Temos que ter ctza da informação!'",
    16: "Linha lateral com seta: '↳ Fonte?'",
    17: "Sublinhou denúncia médica + 'direito!' sobre Canal 1 + '✓ OK!' no campo",
    18: "Linha lateral com seta: '↳ Fonte?'",
    19: "Seta ao lado dos tópicos: '↳ Precisamos deixar bem claro quando usar Zeladoria e quando usar Ouvidoria!'",
    20: "✓ OK! no campo de anotações",
    21: "Visto ✓ no sigilo + linha com seta: '↳ Mais uma vez o chunk'",
    22: "(Caso 22 do Dossiê Técnico — Atendimento descentralizado de enchentes via CRAS)",
    23: "(Caso 23 do Dossiê Técnico — Padrão Ouro de comparação SMOA vs SMUH)"
}

md_lines = []
md_lines.append("# DUQUE IA — Dossiê Comparativo: Respostas Anteriores vs. Novas Respostas Reais (QA 23 Casos)\n")
md_lines.append("> **Sistema:** DUQUE IA — Assistente Virtual Oficial da Prefeitura Municipal de Duque de Caxias / RJ  ")
md_lines.append("> **Documento Original:** `docs/DIAGNOSTICO_E_SOLUCOES_QA_23_CASOS.md` e `ouvidoria104827.pdf`  ")
md_lines.append("> **Data da Execução:** 23/10/2026  ")
md_lines.append("> **Finalidade:** Comparar lado a lado o comportamento anterior da IA, a avaliação da auditoria (com as anotações de caneta) e a **Nova Resposta Real** gerada pelo pipeline atualizado.\n")
md_lines.append("---\n")
md_lines.append("## 📊 1. Resumo Executivo da Evolução do Sistema\n")
md_lines.append("Após a incorporação das regras canônicas de governança, enriquecimento ontológico, saneamento de chunks e blindagem dos handlers de Ouvidoria e Saúde, todas as 23 perguntas oficiais foram submetidas novamente ao DUQUE IA.\n")
md_lines.append("### Principais Saltos Qualitativos Observados:")
md_lines.append("1. **Eliminação Total de Alucinações de Órgãos e Serviços:** Nos Casos 18 e 21, onde a IA anteriormente alucinava Fundação de Apoio (FUNDEC) ou Secretaria da Mulher para 'emagrecer' e 'funcionário fantasma', a nova resposta direciona de forma cirúrgica para a **Atenção Primária à Saúde (UBS/Clínica da Família)** e para a **Ouvidoria Geral / Controladoria Geral (CGM)** com garantia legal de sigilo.")
md_lines.append("2. **Fim do Loop de Multi-turno e Amnésia Conversacional:** No Caso 07, a IA não repete mais perguntas burocráticas sobre servidores da prefeitura. Ao reconhecer o local privado (casa de festas), entrega imediatamente a orientação de **190 (Polícia Militar)** para perturbação do sossego em flagrante e fiscalização integrada de alvará/ruído via **Meio Ambiente (SMMA), Urbanismo (SMUU) e Ordem Pública (SUOP)**.")
md_lines.append("3. **Alinhamento Institucional com Concessionárias:** No Caso 11, a indicação obsoleta da CEDAE foi erradicada. A resposta agora apresenta exclusivamente a concessionária **Águas do Rio (0800 195 0 195)** e o fluxo oficial da Ouvidoria no aplicativo Colab.")
md_lines.append("4. **Proteção Clínica de Urgência Hospitalar:** No Caso 13, diante do relato de trauma ('quebrei o pé'), a IA não menciona mais o programa ambulatorial eletivo 'Chegaram os Especialistas'. Direciona com precisão máxima para o **Hospital Estadual/Municipal Adão Pereira Nunes (Saracuruna)** e HMMRC 24h.")
md_lines.append("5. **Fundamentação Jurídica Auditada:** Nos Casos 05, 15 e 16, a IA agora cita as normas e fontes oficiais do Urbanismo (SMUH / REURB), Código de Trânsito Brasileiro (JARI) e imunidade tributária da CF/88.")
md_lines.append("\n---\n")
md_lines.append("## 🔬 2. Confronto Caso a Caso: Antes vs. Depois\n")

for c in data:
    cid = c["id"]
    titulo = c["titulo"]
    pergunta = c["pergunta"]
    hist = c.get("history", [])
    comportamento_ant = c["comportamento_anterior"]
    avaliacao = c["avaliacao_humana"]
    pen_note = PEN_NOTES.get(cid, "Nenhuma anotação")
    nova_res = c["nova_resposta"]
    nova_ans = nova_res.get("answer", "")
    confidence = nova_res.get("confidence", 0.0)
    intent = nova_res.get("intent_detected", "")
    elapsed = nova_res.get("elapsed_ms", 0)

    md_lines.append(f"### Caso {cid:02d} — {titulo}\n")
    md_lines.append(f"**Pergunta do Munícipe:**  \n> *\"{pergunta}\"*\n")
    if hist:
        md_lines.append(f"**Histórico Conversacional Prévio:**  \n")
        for h in hist:
            md_lines.append(f"> {h}  \n")
        md_lines.append("\n")

    md_lines.append(f"#### 🔴 Última Resposta Anterior (Comportamento Auditado)")
    md_lines.append(f"{comportamento_ant}\n")
    
    md_lines.append(f"#### ✍️ Avaliação Humana e Marcações de Caneta")
    md_lines.append(f"* **Observação da Auditoria:** *\"{avaliacao}\"*")
    md_lines.append(f"* **Marcação / Escrito de Caneta no Formulário:** **`{pen_note}`**\n")

    md_lines.append(f"#### 🟢 Nova Resposta Atual do DUQUE IA")
    md_lines.append(f"```text\n{nova_ans}\n```")
    md_lines.append(f"*Metadados de Execução:* `Intent: {intent}` | `Confiança: {confidence}` | `Latência: {elapsed}ms`\n")

    md_lines.append(f"#### 💡 Análise Comparativa e Ganhos da Nova Resposta")
    if cid == 1:
        md_lines.append("- **O que mudou:** A IA realizou a resolução geográfica determinística do bairro Xerém e indicou as unidades municipais de saúde daquele distrito, acompanhadas do link oficial.")
    elif cid == 2:
        md_lines.append("- **O que mudou:** Mantida a excelência do Padrão Ouro. A resposta foi ancorada formalmente na regra canônica estruturada de governança.")
    elif cid == 3:
        md_lines.append("- **O que mudou:** Preservada a regra preventiva que veda informar funcionamento de unidades em obras (Casa do Autista).")
    elif cid == 4:
        md_lines.append("- **O que mudou:** Eliminada a indicação arbitrária do CRAS Jardim Primavera. A resposta priorizou o SAMU 192 e detalhou o Centro POP e o CRAS territorial com link do Colab.")
    elif cid == 5:
        md_lines.append("- **O que mudou:** A IA deixou de dar fallback evasivo e apresentou o guia prático da SMUH (Cenários de Matrícula, Escritura, Usucapião, Habite-se e REURB), citando endereço e telefones da secretaria.")
    elif cid == 6:
        md_lines.append("- **O que mudou:** Reconheceu o termo 'estabelecimento fedendo' e direcionou diretamente para a Subsecretaria de Vigilância Sanitária no Colab com o assunto oficial de Fiscalização de Alimentos.")
    elif cid == 7:
        md_lines.append("- **O que mudou:** O loop repetitivo foi totalmente eliminado. A IA reconheceu a casa de festas privada e orientou imediatamente o 190 (PMERJ) para flagrantes noturnos e a fiscalização de ruído/alvará pela SMMA, SMUU e SUOP.")
    elif cid == 8:
        md_lines.append("- **O que mudou:** A IA quebrou a consulta e respondeu em dois blocos: Fazenda (Alvará/ISS no Portal do Contribuinte) e Saúde (Licença Sanitária), além de orientar a consulta cadastral na Jucerja.")
    elif cid == 9:
        md_lines.append("- **O que mudou:** O termo gambá foi devidamente recuperado. Foram banidas as mensagens mecânicas 'Não especificado', orientando Guarda Ambiental/SMMA via Colab e Bombeiros (193).")
    elif cid == 10:
        md_lines.append("- **O que mudou:** As 4 perguntas foram respondidas em tópicos independentes e organizados: 1. Ninho de Marimbondos (Bombeiros/Defesa Civil e SMMA); 2. Retirada de Entulho (SMOA); 3. Poda de Árvore (SMMA); 4. Consulta Cardiológica (UBS/SISREG).")
    elif cid == 11:
        md_lines.append("- **O que mudou:** A menção à CEDAE foi extirpada. A resposta indica a Águas do Rio (0800 195 0 195) e o fluxo oficial da Ouvidoria no aplicativo Colab.")
    elif cid == 12:
        md_lines.append("- **O que mudou:** Eliminou orientações redundantes de ligar previamente para a secretaria; instrui o comparecimento direto com o kit de documentos na sede da SMMA.")
    elif cid == 13:
        md_lines.append("- **O que mudou:** A consulta não caiu no programa ambulatorial eletivo 'Chegaram os Especialistas'. Foi classificada instantaneamente como emergência médica e direcionou para o Hospital Adão Pereira Nunes (Saracuruna) com 100% de confiança.")
    elif cid == 14:
        md_lines.append("- **O que mudou:** A IA identificou a demanda de canteiro danificado/calçada pública e indicou a Secretaria de Obras e Agricultura (SMOA) via Colab.")
    elif cid == 15:
        md_lines.append("- **O que mudou:** A IA explicou a imunidade tributária da CF art. 150, a exigência de alvará e habite-se pelo Poder de Polícia da Prefeitura, e esclareceu que não há interdição sumária sem contraditório prévio.")
    elif cid == 16:
        md_lines.append("- **O que mudou:** Falso positivo no guardrail jurídico foi corrigido. A IA informou a competência da JARI Municipal (SMTSP), prazo legal de 30 dias e documentos para recurso.")
    elif cid == 17:
        md_lines.append("- **O que mudou:** A resposta deixou explícito que as demandas não devem ser juntadas no mesmo protocolo e forneceu os hiperlinks oficiais do e-SIC e da Ouvidoria no Colab.")
    elif cid == 18:
        md_lines.append("- **O que mudou:** Eliminadas as alucinações sobre FUNDEC e Procuradoria. A IA orientou o agendamento prévio na UBS/Clínica da Família com Clínico Geral para encaminhamento à Nutrição.")
    elif cid == 19:
        md_lines.append("- **O que mudou:** Distinção cristalina: lâmpada apagada deve ser aberta primariamente na Zeladoria Urbana do Colab; Ouvidoria só deve ser acionada caso o prazo regulamentar tenha expirado.")
    elif cid == 20:
        md_lines.append("- **O que mudou:** Eliminada a postura combativa na recepção do posto; instrui solicitar o número do comprovante do SISREG para acompanhamento transparente.")
    elif cid == 21:
        md_lines.append("- **O que mudou:** A IA não alucinou a Secretaria da Mulher nem programas esportivos. Direcionou a denúncia de funcionário fantasma para a Ouvidoria Geral / Controladoria Geral (CGM) com garantia de sigilo pela Lei 13.460/2017.")
    elif cid == 22:
        md_lines.append("- **O que mudou:** O cidadão é orientado a buscar os benefícios eventuais (Aluguel Social, Cesta Básica) na rede descentralizada de CRAS nos bairros, além da Defesa Civil (199).")
    elif cid == 23:
        md_lines.append("- **O que mudou:** Resposta comparativa impecável delimitando as competências de infraestrutura pública da SMOA versus licenciamento e regulação privada da SMUH.")
    md_lines.append("\n---\n")

full_content = "\n".join(md_lines)

# Grava no docs/
with open(out_md_path, "w", encoding="utf-8") as f:
    f.write(full_content)

# Grava no artifacts/
with open(artifact_path, "w", encoding="utf-8") as f:
    f.write(full_content)

print(f"[OK] Documento comparativo gerado com sucesso em:\n - {out_md_path}\n - {artifact_path}")
