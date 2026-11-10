"""
Script para gerar o Relatório Executivo Oficial de Comparativo de Custos dos Modelos de IA
para o DUQUE IA (Prefeitura Municipal de Duque de Caxias).
Focado exclusivamente na auditoria de custos, benchmarks oficiais dos 13 modelos dos principais
ecossistemas (Google Gemini, OpenAI, Anthropic Claude e Groq) e projeções financeiras.
"""

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Aplica cor de fundo em uma célula da tabela."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    """Define margens internas (padding) de uma célula."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="4"):
    """Aplica bordas refinadas e sutis à tabela."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_callout(doc, text, title="NOTA EXECUTIVA DE CUSTOS", border_color="1A365D", bg_color="EDF2F7"):
    """Adiciona caixa de destaque executiva."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=160)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
            <w:top w:val="none"/>
            <w:right w:val="none"/>
            <w:bottom w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(f"📌 {title}\n")
    run_t.bold = True
    run_t.font.name = 'Calibri'
    run_t.font.size = Pt(10)
    run_t.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    
    run_b = p.add_run(text)
    run_b.font.name = 'Calibri'
    run_b.font.size = Pt(9.5)
    run_b.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_after = Pt(4)

def build_cost_report():
    doc = Document()
    
    # Configuração de Margens
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # Cabeçalho
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("DUQUE IA • Relatório Oficial de Comparativo de Custos por Modelo de IA (2026)")
        hrun.font.name = 'Calibri'
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x71, 0x80, 0x96)
        
        # Rodapé
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Prefeitura Municipal de Duque de Caxias • Ouvidoria Geral & Gabinete de Tecnologia • Gestão Orçamentária")
        frun.font.name = 'Calibri'
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    # ── TÍTULO PRINCIPAL ──
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    run_title = title_p.add_run("RELATÓRIO COMPARATIVO DE CUSTOS POR MODELO DE IA")
    run_title.bold = True
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(18)
    run_title.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(12)
    run_sub = sub_p.add_run("Auditoria de Preços de Mercado, Simulação de Consumo por Token e Dimensionamento Financeiro do DUQUE IA")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    # Metadados
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(14)
    meta_run = meta_p.add_run("Órgão Responsável: Ouvidoria Geral & Gabinete de Tecnologia | Base de Cotação: US$ 1,00 = R$ 5,50 | Data: 2026")
    meta_run.font.name = 'Calibri'
    meta_run.font.size = Pt(9)
    meta_run.font.italic = True
    meta_run.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    # ── SEÇÃO 1: PARÂMETROS DO DUQUE IA ──
    h1 = doc.add_heading("1. Parâmetros da Consulta Padrão do Cidadão", level=1)
    h1.paragraph_format.space_before = Pt(10)
    h1.paragraph_format.space_after = Pt(6)

    p1 = doc.add_paragraph()
    p1.paragraph_format.space_after = Pt(8)
    p1.add_run(
        "A volumetria de tokens foi aferida nos testes do DUQUE IA utilizando a arquitetura RAG (Retrieval-Augmented Generation). "
        "Uma consulta típica completa para orientar o munícipe (com regras de negócio, documentos oficiais e resposta cidadã) consome:"
    )

    # Tabela de parâmetros
    t_params = doc.add_table(rows=5, cols=3)
    t_params.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_params)
    widths_p = [Inches(2.2), Inches(1.5), Inches(3.1)]

    headers_p = ["Componente do Fluxo", "Tokens Médios", "Descrição / Conteúdo Injetado"]
    for j, h in enumerate(headers_p):
        cell = t_params.cell(0, j)
        cell.width = widths_p[j]
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    rows_p = [
        ["Tokens de Entrada (Input)", "1.400 tokens", "POP da Ouvidoria (~400 tok) + Documentos RAG (~800 tok) + Dúvida (~20 tok)"],
        ["Tokens de Saída (Output)", "300 tokens", "Resposta formatada, objetiva, com contatos e links do Colab em negrito"],
        ["Total por Atendimento", "1.700 tokens", "Volume exato processado pela IA por resposta individual"],
        ["Demanda Base (30 dias)", "30.000 msgs", "1.000 atendimentos/dia = 51.000.000 tokens processados por mês"]
    ]

    for i, row in enumerate(rows_p, start=1):
        bg = "F7FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(row):
            cell = t_params.cell(i, j)
            cell.width = widths_p[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            run = p.add_run(val)
            run.font.name = 'Calibri'
            run.font.size = Pt(9)
            if j == 1:
                run.bold = True
                run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
            else:
                run.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_callout(
        doc,
        "Por que a Entrada é Maior que a Saída? No RAG público, a entrada armazena todo o contexto factual oficial "
        "(leis, decretos e endereços de postos) para blindar contra alucinações. A saída é enxuta (~300 tokens) para entregar "
        "uma resposta rápida (<1,5s no WhatsApp) e maximizar a economia de dinheiro público.",
        title="ARQUITETURA DE RETRIEVAL RAG"
    )

    # ── SEÇÃO 2: RANKING COMPARATIVO DOS 13 MODELOS ──
    h2 = doc.add_heading("2. Tabela Comparativa de Custos: 13 Modelos Auditados", level=1)
    h2.paragraph_format.space_before = Pt(12)
    h2.paragraph_format.space_after = Pt(6)

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(8)
    p2.add_run(
        "Abaixo está o comparativo oficial de preços de mercado obtido nos simuladores dos grandes provedores "
        "(Google Gemini, Anthropic Claude, OpenAI e Groq). Todos os custos foram calculados para a mesma carga de "
        "1.700 tokens por chamada e 30.000 atendimentos mensais (1.000 chamadas/dia):"
    )

    # Tabela dos 13 modelos
    models_data = [
        ("1º", "GPT OSS 20B", "Groq", "0.000195", "5.85", "32,18", "386,10", "Ultra-Econômico"),
        ("2º", "GPT OSS 120B", "Groq", "0.000390", "11.70", "64,35", "772,20", "Ultra-Econômico"),
        ("3º", "GPT-5.6 Luna", "OpenAI", "0.000640", "19.20", "105,60", "1.267,20", "Econômico"),
        ("4º", "Gemini 3.5 Flash-Lite", "Google", "0.001170", "35.10", "193,05", "2.316,60", "Eficiência Multimodal"),
        ("5º", "Gemini 3.8 Flash ★", "Google", "0.002175", "65.25", "358,88", "4.306,50", "Padrão Oficial DUQUE IA"),
        ("6º", "Claude Haiku 4.5", "Anthropic", "0.002900", "87.00", "478,50", "5.742,00", "Eficiência Rápida"),
        ("7º", "Gemini 3.5 Flash", "Google", "0.004800", "144.00", "792,00", "9.504,00", "Intermediário"),
        ("8º", "Claude Sonnet 5", "Anthropic", "0.005800", "174.00", "957,00", "11.484,00", "Avançado"),
        ("9º", "GPT-5.6 Terra", "OpenAI", "0.006400", "192.00", "1.056,00", "12.672,00", "Avançado"),
        ("10º", "GPT-5.6 Sol", "OpenAI", "0.011600", "348.00", "1.914,00", "22.968,00", "Frontier Raciocínio"),
        ("11º", "Claude Opus 5", "Anthropic", "0.014500", "435.00", "2.392,50", "28.710,00", "Frontier Raciocínio"),
        ("12º", "GPT-6 Astra", "OpenAI", "0.029000", "870.00", "4.785,00", "57.420,00", "Ultra Frontier"),
        ("13º", "Claude Fable 5.1", "Anthropic", "0.029000", "870.00", "4.785,00", "57.420,00", "Ultra Frontier")
    ]

    t_models = doc.add_table(rows=len(models_data) + 1, cols=7)
    t_models.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_models)
    widths_m = [Inches(0.4), Inches(1.7), Inches(0.9), Inches(1.0), Inches(0.9), Inches(1.0), Inches(0.9)]

    headers_m = ["Pos.", "Modelo", "Provedor", "Por Chamada", "30 Dias ($)", "30 Dias (R$)", "Anual (R$)"]
    for j, h in enumerate(headers_m):
        cell = t_models.cell(0, j)
        cell.width = widths_m[j]
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for i, m in enumerate(models_data, start=1):
        is_highlight = "Gemini 3.8 Flash" in m[1]
        if is_highlight:
            bg = "FEF3C7"  # Destaque dourado/amarelo suave
        elif i % 2 == 1:
            bg = "F7FAFC"
        else:
            bg = "FFFFFF"

        for j in range(7):
            cell = t_models.cell(i, j)
            cell.width = widths_m[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=50, right=50)
            p = cell.paragraphs[0]
            run = p.add_run(m[j])
            run.font.name = 'Calibri'
            run.font.size = Pt(8)
            if is_highlight:
                run.bold = True
                run.font.color.rgb = RGBColor(0x92, 0x40, 0x0E)
            elif j in (1, 5):
                run.bold = True
                run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
            else:
                run.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ── SEÇÃO 3: ANÁLISE POR CATEGORIA / TIER ──
    h3 = doc.add_heading("3. Análise Financeira por Categorias de Modelos", level=1)
    h3.paragraph_format.space_before = Pt(12)
    h3.paragraph_format.space_after = Pt(6)

    p3 = doc.add_paragraph()
    p3.paragraph_format.space_after = Pt(6)
    p3.add_run("Os 13 modelos avaliados se dividem em 4 tiers operacionais com grandes impactos orçamentários:")

    tiers_info = [
        ("Tier 1: Ultra-Econômicos / Open Source (Groq & Luna)", 
         "Custo Mensal: R$ 32,18 a R$ 105,60 | Indicado para: Triagem rápida de texto puro. Não possui multimodalidade nativa para áudio do WhatsApp ou visão computacional do Colab."),
        ("Tier 2: Eficiência Multimodal & Produção (Gemini 3.8 Flash & Haiku)", 
         "Custo Mensal: R$ 193,05 a R$ 478,50 | Indicado para: Produção do DUQUE IA. Processa texto, áudios e fotos em 1 única requisição com latência <1,5s e custo de centavos."),
        ("Tier 3: Intermediários e Análise Técnica (Claude Sonnet & GPT-5.6 Terra)", 
         "Custo Mensal: R$ 792,00 a R$ 1.056,00 | Indicado para: Análise de relatórios internos e cruzamento de dados estatísticos municipais."),
        ("Tier 4: Frontier e Raciocínio Pesado (GPT-6 Astra, Claude Opus & Fable)", 
         "Custo Mensal: R$ 1.914,00 a R$ 4.785,00 | Indicado para: Pareceres jurídicos complexos da Procuradoria. É 148x mais caro que o Tier 1 para a mesma resposta.")
    ]

    for title_tier, desc_tier in tiers_info:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_before = Pt(4)
        p_t.paragraph_format.space_after = Pt(2)
        r_t1 = p_t.add_run(f"• {title_tier}\n")
        r_t1.bold = True
        r_t1.font.name = 'Calibri'
        r_t1.font.size = Pt(9.5)
        r_t1.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
        
        r_t2 = p_t.add_run(f"  {desc_tier}")
        r_t2.font.name = 'Calibri'
        r_t2.font.size = Pt(9)
        r_t2.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    # ── SEÇÃO 4: SIMULAÇÃO DE ESCALA MUNICIPAL ──
    h4 = doc.add_heading("4. Projeção Orçamentária por Nível de Demanda do Município", level=1)
    h4.paragraph_format.space_before = Pt(12)
    h4.paragraph_format.space_after = Pt(6)

    p4 = doc.add_paragraph()
    p4.paragraph_format.space_after = Pt(6)
    p4.add_run("Simulação considerando o modelo oficial homologado (**Gemini 3.8 Flash**) em diferentes volumes de atendimento:")

    t_scale = doc.add_table(rows=5, cols=5)
    t_scale.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_scale)
    widths_s = [Inches(1.8), Inches(1.3), Inches(1.2), Inches(1.2), Inches(1.3)]

    headers_s = ["Fase do Projeto", "Atendimentos/Mês", "Tokens/Mês", "Custo Mensal (R$)", "Custo Anual (R$)"]
    for j, h in enumerate(headers_s):
        cell = t_scale.cell(0, j)
        cell.width = widths_s[j]
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    scale_data = [
        ["Piloto Inicial (100 msgs/dia)", "3.000 msgs", "5,1 Milhões", "R$ 35,88 / mês", "R$ 430,56 / ano"],
        ["Ouvidoria Geral (500 msgs/dia)", "15.000 msgs", "25,5 Milhões", "R$ 179,44 / mês", "R$ 2.153,28 / ano"],
        ["Produção Plena (1.000 msgs/dia)", "30.000 msgs", "51,0 Milhões", "R$ 358,88 / mês", "R$ 4.306,56 / ano"],
        ["Pico / IPTU (5.000 msgs/dia)", "150.000 msgs", "255,0 Milhões", "R$ 1.794,40 / mês", "R$ 21.532,80 / ano"]
    ]

    for i, row in enumerate(scale_data, start=1):
        bg = "F7FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(row):
            cell = t_scale.cell(i, j)
            cell.width = widths_s[j]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            p = cell.paragraphs[0]
            run = p.add_run(val)
            run.font.name = 'Calibri'
            run.font.size = Pt(8.5)
            if j == 3:
                run.bold = True
                run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
            else:
                run.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ── SEÇÃO 5: CONCLUSÃO E RECOMENDAÇÃO TÉCNICA ──
    h5 = doc.add_heading("5. Conclusão e Recomendação Técnica Oficial", level=1)
    h5.paragraph_format.space_before = Pt(12)
    h5.paragraph_format.space_after = Pt(6)

    p5 = doc.add_paragraph()
    p5.paragraph_format.space_after = Pt(6)
    p5.add_run(
        "1. **Modelo Primário Homologado:** O **Gemini 3.8 Flash** é a escolha técnica perfeita para o DUQUE IA. "
        "Com um custo de apenas **R$ 358,88/mês para 30 mil atendimentos**, ele unifica texto, áudio e fotos no mesmo pipeline.\n"
        "2. **Economia em Relação ao Atendimento Humano:** Uma central telefônica de call center para atender 30.000 chamadas "
        "mensais custaria entre **R$ 60.000,00 e R$ 80.000,00 por mês**. O DUQUE IA gera uma economia pública superior a **99,5%**.\n"
        "3. **Evitar Modelos Frontier em Atendimento Básico:** O uso de GPT-6 Astra ou Claude Fable geraria uma despesa desnecessária "
        "de R$ 4.785,00/mês sem ganho perceptível para o munícipe que deseja saber onde tomar vacina ou como tirar o IPTU."
    )

    p_close = doc.add_paragraph()
    p_close.paragraph_format.space_before = Pt(14)
    r_close = p_close.add_run(
        "Duque de Caxias, RJ — 2026.\n"
        "Documento emitido para instrução orçamentária e governança tecnológica da Ouvidoria Geral do Município."
    )
    r_close.font.name = 'Calibri'
    r_close.font.size = Pt(9)
    r_close.font.italic = True
    r_close.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    # Salvar
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    os.makedirs(output_dir, exist_ok=True)
    
    target_files = [
        os.path.join(output_dir, "RELATORIO_COMPARATIVO_CUSTOS_MODELOS_IA.docx"),
        os.path.join(output_dir, "RELATORIO_GASTOS_DE_TOKENS_DUQUE_IA_OFICIAL.docx")
    ]
    
    for fpath in target_files:
        try:
            doc.save(fpath)
            print(f"[OK] Documento gerado com sucesso em: {fpath}")
        except PermissionError:
            print(f"[Aviso] Arquivo {os.path.basename(fpath)} estava em uso, ignorando.")

if __name__ == "__main__":
    build_cost_report()
