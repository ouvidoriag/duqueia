"""
Script para gerar o documento Word (.docx) de Orçamento de Tokens e Comparativo de Custos do DUQUE IA.
Versão direta com consumo diário, mensal e anual de tokens e valores detalhados por modelo.
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
    """Define a cor de fundo de uma célula da tabela."""
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
    """Aplica bordas sutis à tabela."""
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

def add_heading_styled(doc, text):
    h = doc.add_heading(level=2)
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    r = h.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    return h

def format_table(table, headers, rows_data, widths, align_right_cols=None, align_center_cols=None):
    if align_right_cols is None:
        align_right_cols = []
    if align_center_cols is None:
        align_center_cols = []
    
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)

    # Cabeçalho
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.width = widths[col_idx]
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=70, bottom=70, left=80, right=80)
        p = cell.paragraphs[0]
        if col_idx in align_right_cols:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif col_idx in align_center_cols:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Linhas de Dados
    for row_idx, row in enumerate(rows_data, start=1):
        bg = "F7FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.width = widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            if col_idx in align_right_cols:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif col_idx in align_center_cols:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(val)
            run.font.name = 'Calibri'
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

def build_dossier():
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.6)
        section.right_margin = Inches(0.6)

    # 1. PARÂMETROS DA CONSULTA
    add_heading_styled(doc, "1. Parâmetros da Consulta (Base: 1.700 Tokens)")
    headers_1 = ["Componente", "Volume", "Detalhamento"]
    widths_1 = [Inches(2.2), Inches(1.5), Inches(3.6)]
    rows_1 = [
        ["Tokens de Entrada (Input)", "1.400 tokens", "Instruções de atendimento + Contexto RAG + Pergunta do cidadão"],
        ["Tokens de Saída (Output)", "300 tokens", "Resposta formatada com dados de contato, endereço e links"],
        ["Total por Consulta", "1.700 tokens", "Carga padrão faturada por atendimento"]
    ]
    table_1 = doc.add_table(rows=len(rows_1) + 1, cols=len(headers_1))
    format_table(table_1, headers_1, rows_1, widths_1)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 2. VOLUME DE TOKENS POR PERÍODO
    add_heading_styled(doc, "2. Volume de Tokens por Período (Dia, Mês e Ano)")
    headers_2 = ["Cenário de Uso", "Atendimentos / Dia", "Tokens / Dia", "Tokens / Mês (30 dias)", "Tokens / Ano (365 dias)"]
    widths_2 = [Inches(1.8), Inches(1.3), Inches(1.4), Inches(1.4), Inches(1.4)]
    rows_2 = [
        ["Piloto Inicial", "100 chamadas", "170.000 (170 mil)", "5.100.000 (5,1 milhões)", "62.050.000 (62,05 milhões)"],
        ["Ouvidoria Geral", "500 chamadas", "850.000 (850 mil)", "25.500.000 (25,5 milhões)", "310.250.000 (310,25 milhões)"],
        ["Produção Plena", "1.000 chamadas", "1.700.000 (1,7 milhão)", "51.000.000 (51,0 milhões)", "620.500.000 (620,50 milhões)"],
        ["Pico / Período IPTU", "5.000 chamadas", "8.500.000 (8,5 milhões)", "255.000.000 (255,0 milhões)", "3.102.500.000 (3,10 bilhões)"]
    ]
    table_2 = doc.add_table(rows=len(rows_2) + 1, cols=len(headers_2))
    format_table(table_2, headers_2, rows_2, widths_2, align_center_cols=[1], align_right_cols=[2, 3, 4])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 3. COMPARATIVO DE CUSTOS POR MODELO
    add_heading_styled(doc, "3. Comparativo de Custos por Modelo (Dia, Mês e Ano)")
    
    p_note = doc.add_paragraph()
    p_note.paragraph_format.space_after = Pt(3)
    r_n = p_note.add_run("Cenário Produção Padrão: 1.000 chamadas/dia • 30.000 chamadas/mês • 1.700 tokens/chamada • Cotação: US$ 1,00 = R$ 5,50")
    r_n.font.name = 'Calibri'
    r_n.font.size = Pt(8.5)
    r_n.font.italic = True
    r_n.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    headers_3 = ["Modelo", "Provedor", "Custo/Chamada", "Custo / Dia (R$)", "Custo / Mês (R$)", "Custo / Ano (R$)"]
    widths_3 = [Inches(1.7), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.2)]
    rows_3 = [
        ["GPT OSS 20B", "Groq", "US$ 0,000195", "R$ 1,07 / dia", "R$ 32,18 / mês", "R$ 386,10 / ano"],
        ["GPT OSS 120B", "Groq", "US$ 0,000390", "R$ 2,15 / dia", "R$ 64,35 / mês", "R$ 772,20 / ano"],
        ["GPT-5.6 Luna", "OpenAI", "US$ 0,000640", "R$ 3,52 / dia", "R$ 105,60 / mês", "R$ 1.267,20 / ano"],
        ["Gemini 3.5 Flash-Lite", "Google", "US$ 0,001170", "R$ 6,44 / dia", "R$ 193,05 / mês", "R$ 2.316,60 / ano"],
        ["Gemini 3.8 Flash", "Google", "US$ 0,002175", "R$ 11,96 / dia", "R$ 358,88 / mês", "R$ 4.306,50 / ano"],
        ["Claude Haiku 4.5", "Anthropic", "US$ 0,002900", "R$ 15,95 / dia", "R$ 478,50 / mês", "R$ 5.742,00 / ano"],
        ["Gemini 3.5 Flash", "Google", "US$ 0,004800", "R$ 26,40 / dia", "R$ 792,00 / mês", "R$ 9.504,00 / ano"],
        ["Claude Sonnet 5", "Anthropic", "US$ 0,005800", "R$ 31,90 / dia", "R$ 957,00 / mês", "R$ 11.484,00 / ano"],
        ["GPT-5.6 Terra", "OpenAI", "US$ 0,006400", "R$ 35,20 / dia", "R$ 1.056,00 / mês", "R$ 12.672,00 / ano"],
        ["GPT-5.6 Sol", "OpenAI", "US$ 0,011600", "R$ 63,80 / dia", "R$ 1.914,00 / mês", "R$ 22.968,00 / ano"],
        ["Claude Opus 5", "Anthropic", "US$ 0,014500", "R$ 79,75 / dia", "R$ 2.392,50 / mês", "R$ 28.710,00 / ano"],
        ["GPT-6 Astra", "OpenAI", "US$ 0,029000", "R$ 159,50 / dia", "R$ 4.785,00 / mês", "R$ 57.420,00 / ano"],
        ["Claude Fable 5.1", "Anthropic", "US$ 0,029000", "R$ 159,50 / dia", "R$ 4.785,00 / mês", "R$ 57.420,00 / ano"]
    ]
    table_3 = doc.add_table(rows=len(rows_3) + 1, cols=len(headers_3))
    format_table(table_3, headers_3, rows_3, widths_3, align_right_cols=[2, 3, 4, 5])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 4. CUSTOS POR TIPO DE MENSAGEM (MULTIMODAL)
    add_heading_styled(doc, "4. Custos por Tipo de Mensagem (Multimodal)")
    headers_4 = ["Modalidade", "Base de Cálculo", "Média de Tokens", "Custo Unitário (Gemini 3.8 Flash)*"]
    widths_4 = [Inches(1.8), Inches(2.3), Inches(1.3), Inches(1.9)]
    rows_4 = [
        ["Texto (Portal / Chat)", "1.400 in / 300 out", "1.700 tokens", "~R$ 0,0119 (RAG) / R$ 0,00 (Cache)"],
        ["Áudio (WhatsApp)", "32 tokens / segundo (áudio 20s)", "640 tokens", "~R$ 0,0050"],
        ["Foto / Imagem (Colab)", "258 a 1.032 tokens / imagem", "1.032 tokens", "~R$ 0,0080"],
        ["Vídeo (Vistoria Urbana)", "100 tokens / segundo (vídeo 10s)", "1.000 tokens", "~R$ 0,0080"]
    ]
    table_4 = doc.add_table(rows=len(rows_4) + 1, cols=len(headers_4))
    format_table(table_4, headers_4, rows_4, widths_4, align_right_cols=[3])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 5. PROJEÇÃO ORÇAMENTÁRIA POR VOLUME (GEMINI 3.8 FLASH)
    add_heading_styled(doc, "5. Projeção Orçamentária por Volume de Atendimentos (Gemini 3.8 Flash)")
    headers_5 = ["Nível de Demanda", "Volume Mensal", "Volume de Tokens", "Custo Diário (R$)", "Custo Mensal (R$)", "Custo Anual (R$)"]
    widths_5 = [Inches(1.7), Inches(1.1), Inches(1.2), Inches(1.1), Inches(1.1), Inches(1.1)]
    rows_5 = [
        ["Piloto (100 msgs/dia)", "3.000 msgs", "5,1 Milhões", "R$ 1,20 / dia", "R$ 35,88 / mês", "R$ 430,56 / ano"],
        ["Ouvidoria (500 msgs/dia)", "15.000 msgs", "25,5 Milhões", "R$ 5,98 / dia", "R$ 179,44 / mês", "R$ 2.153,28 / ano"],
        ["Produção Plena (1.000 msgs/dia)", "30.000 msgs", "51,0 Milhões", "R$ 11,96 / dia", "R$ 358,88 / mês", "R$ 4.306,56 / ano"],
        ["Pico / IPTU (5.000 msgs/dia)", "150.000 msgs", "255,0 Milhões", "R$ 59,81 / dia", "R$ 1.794,40 / mês", "R$ 21.532,80 / ano"]
    ]
    table_5 = doc.add_table(rows=len(rows_5) + 1, cols=len(headers_5))
    format_table(table_5, headers_5, rows_5, widths_5, align_right_cols=[3, 4, 5])

    # Salva nos arquivos docx de docs
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    os.makedirs(output_dir, exist_ok=True)
    
    target_path = os.path.join(output_dir, "GUIA_COMPLETO_MULTIMODAL_E_CUSTOS_DUQUE_IA.docx")
    try:
        doc.save(target_path)
        print(f"[OK] Documento gerado em: {target_path}")
    except PermissionError:
        alt_path = os.path.join(output_dir, "GUIA_COMPLETO_MULTIMODAL_E_CUSTOS_DUQUE_IA_NOVO.docx")
        doc.save(alt_path)
        print(f"[OK] Documento salvo como: {alt_path}")

if __name__ == "__main__":
    build_dossier()
