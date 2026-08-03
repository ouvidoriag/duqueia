import os
import sys
import sqlite3
import openpyxl
import re
import json

# Setup root path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from config.settings import DATABASE_MAIN, DATABASE_VECTOR
from utils.gemini_client import GeminiClient

XLSX_PATH = os.path.join(ROOT, "Carta_Servicos_Secretaria_Municipal_de_Governo (5).xlsx")

def clean_str(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in ("none", "null", "nan", "não informado", "não cadastrado") else s

def generate_sec_code(name: str) -> str:
    name_upper = name.upper()
    mappings = {
        "SAÚDE": "SMS", "FAZENDA": "SMF", "EDUCAÇÃO": "SME", "TRANSPORTES": "SMT",
        "OBRAS": "SMO", "ADMINISTRAÇÃO": "SMA", "MEIO AMBIENTE": "SMMA",
        "ASSISTÊNCIA SOCIAL": "SMASDH", "CULTURA": "SMC", "URBANISMO": "SMU",
        "PROCURADORIA": "PGM", "PREVIDÊNCIA": "IPMDC", "FUNDAÇÃO DE APOIO": "FUNDEC",
        "FUNDEC": "FUNDEC"
    }
    for key, val in mappings.items():
        if key in name_upper:
            return val
    words = [w for w in name_upper.split() if w not in ["DE", "E", "DO", "DA", "PARA", "MUNICIPAL"]]
    if len(words) >= 2:
        return "".join(w[0] for w in words)[:5]
    return name_upper[:4]

def extract_phones(text: str) -> list[str]:
    if not text:
        return []
    pattern = r'(?:\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}|\b0800\s?\d{3}\s?\d{4}\b'
    matches = re.findall(pattern, text)
    return list(set([m.strip() for m in matches if len(m.strip()) >= 8]))

def extract_emails(text: str) -> list[str]:
    if not text:
        return []
    pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    return list(set(re.findall(pattern, text)))

def extract_links(text: str) -> list[str]:
    if not text:
        return []
    pattern = r'https?://[^\s,\)\"\']+'
    return list(set(re.findall(pattern, text)))

def split_steps(text: str) -> list[str]:
    if not text:
        return []
    lines = re.split(r'\n|(?:\d+[\.\-\)\s]+)|[•\-\*]\s+', text)
    steps = [l.strip() for l in lines if l.strip() and len(l.strip()) > 5]
    return steps if steps else [text.strip()]

def split_documents(text: str) -> list[str]:
    if not text:
        return []
    lines = re.split(r'\n|;|\,', text)
    docs = [l.strip() for l in lines if l.strip() and len(l.strip()) > 3]
    return docs if docs else [text.strip()]

def extract_keywords_heuristics(text: str) -> list:
    stopwords = {
        "como", "onde", "quando", "quem", "qual", "quais", "para", "com", "uma", "um", 
        "mais", "sobre", "esta", "este", "seus", "suas", "pelo", "pela", "pelos", "pelas", 
        "seja", "eram", "seria", "teria", "esse", "essa", "isso", "aquilo", "tudo", "nada",
        "fazer", "posso", "quero", "saber", "entre", "algum", "deve", "devem", "esta",
        "está", "estão", "pelos", "pelas", "sem", "sob", "sobre", "por", "para", "com", 
        "dos", "das", "aos", "aas", "nas", "nos", "num", "numa", "sua", "seu", "pode", "podem",
        "prefeitura", "município", "municipal", "duque", "caxias"
    }
    words = re.findall(r'\b[a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]{3,15}\b', text.lower())
    filtered_words = [w for w in words if w not in stopwords]
    freq = {}
    for w in filtered_words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)
    return sorted_words[:12]

def run_sync():
    print(f"=== INICIANDO SINCRONIZAÇÃO E VETORIZAÇÃO DA CARTA DE SERVIÇOS ===")
    print(f"Planilha de entrada: {XLSX_PATH}")

    if not os.path.exists(XLSX_PATH):
        print(f"[ERRO] Planilha {XLSX_PATH} não encontrada.")
        return

    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    sheet = wb.active

    # Carrega cabeçalhos da linha 3
    headers = [clean_str(cell.value) for cell in sheet[3]]
    print("Cabeçalhos detectados:", headers)

    # Conecta ao banco principal
    conn_main = sqlite3.connect(DATABASE_MAIN)
    cur_main = conn_main.cursor()

    # Habilita chaves estrangeiras
    cur_main.execute("PRAGMA foreign_keys = ON;")

    # Limpa dados antigos das tabelas de serviços
    print("[1/4] Limpando registros antigos em main.db...")
    cur_main.execute("DELETE FROM service_documents;")
    cur_main.execute("DELETE FROM service_steps;")
    cur_main.execute("DELETE FROM service_links;")
    cur_main.execute("DELETE FROM service_emails;")
    cur_main.execute("DELETE FROM service_phones;")
    cur_main.execute("DELETE FROM services;")
    cur_main.execute("DELETE FROM categories;")
    cur_main.execute("DELETE FROM secretarias;")
    conn_main.commit()

    sec_cache = {}
    cat_cache = {}

    count_sec = 0
    count_cat = 0
    count_services = 0

    services_data = []

    # Iterar a partir da linha 4
    for row_idx in range(4, sheet.max_row + 1):
        row_cells = [cell.value for cell in sheet[row_idx]]
        if not any(row_cells):
            continue

        row_dict = {}
        for h, val in zip(headers, row_cells):
            if h:
                row_dict[h] = clean_str(val)

        servico_nome = row_dict.get("Serviço") or row_dict.get("Servico")
        if not servico_nome:
            continue

        sec_nome = row_dict.get("Órgão") or row_dict.get("Orgao") or "Fundação de Apoio à Escola Técnica (FUNDEC)"
        cat_nome = row_dict.get("Categoria") or "Geral"

        # 1. Secretaria
        if sec_nome not in sec_cache:
            cur_main.execute("SELECT id FROM secretarias WHERE name = ?", (sec_nome,))
            row_sec = cur_main.fetchone()
            if row_sec:
                sec_id = row_sec[0]
            else:
                sec_code = generate_sec_code(sec_nome)
                cur_main.execute("INSERT INTO secretarias (code, name) VALUES (?, ?)", (sec_code, sec_nome))
                sec_id = cur_main.lastrowid
                count_sec += 1
            sec_cache[sec_nome] = sec_id
        else:
            sec_id = sec_cache[sec_nome]

        # 2. Categoria
        cat_key = (cat_nome, sec_id)
        if cat_key not in cat_cache:
            cur_main.execute("SELECT id FROM categories WHERE name = ? AND secretaria_id = ?", (cat_nome, sec_id))
            row_cat = cur_main.fetchone()
            if row_cat:
                cat_id = row_cat[0]
            else:
                cur_main.execute("INSERT INTO categories (name, secretaria_id) VALUES (?, ?)", (cat_nome, sec_id))
                cat_id = cur_main.lastrowid
                count_cat += 1
            cat_cache[cat_key] = cat_id
        else:
            cat_id = cat_cache[cat_key]

        # 3. Inserção do Serviço
        desc = row_dict.get("O que é o serviço") or row_dict.get("O que e o servico", "")
        how = row_dict.get("Como acessar", "")
        addr = row_dict.get("Endereço") or row_dict.get("Endereco", "")
        who = row_dict.get("Quem pode solicitar", "Cidadão")
        deadline = row_dict.get("Prazo máximo") or row_dict.get("Prazo maximo", "Não especificado")
        cost = row_dict.get("Quanto custa", "Gratuito")
        waiting_time = row_dict.get("Tempo de espera", "")
        regulation_norm = row_dict.get("Norma que regulamenta", "")

        cur_main.execute("""
            INSERT INTO services (
                secretaria_id, category_id, name, description, how_to_access,
                address, who_can_request, max_deadline, cost, status, waiting_time, regulation_norm
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'published', ?, ?)
        """, (sec_id, cat_id, servico_nome, desc, how, addr, who, deadline, cost, waiting_time, regulation_norm))

        service_id = cur_main.lastrowid
        count_services += 1

        # Contatos
        col_tel = row_dict.get("Telefone", "")
        col_eml = row_dict.get("E-mail(s)") or row_dict.get("E-mail", "")
        col_lnk = row_dict.get("Link(s)") or row_dict.get("Link", "")
        ctx_text = f"{col_tel} {col_eml} {col_lnk} {how} {addr} {desc}"

        phones = extract_phones(ctx_text)
        if col_tel:
            phones.append(col_tel)
        for ph in set(phones):
            if len(ph) >= 5:
                cur_main.execute("INSERT INTO service_phones (service_id, phone) VALUES (?, ?)", (service_id, ph))

        emails = extract_emails(ctx_text)
        if col_eml:
            emails.append(col_eml)
        for em in set(emails):
            if "@" in em:
                cur_main.execute("INSERT INTO service_emails (service_id, email) VALUES (?, ?)", (service_id, em))

        links = extract_links(ctx_text)
        if col_lnk:
            links.append(col_lnk)
        for lk in set(links):
            if len(lk) >= 5:
                cur_main.execute("INSERT INTO service_links (service_id, link) VALUES (?, ?)", (service_id, lk))

        # Passos
        passo_a_passo = row_dict.get("Passo a passo", "")
        steps = split_steps(passo_a_passo if passo_a_passo else how)
        for idx_step, step_desc in enumerate(steps, 1):
            cur_main.execute("INSERT INTO service_steps (service_id, step_number, description) VALUES (?, ?, ?)",
                           (service_id, idx_step, step_desc))

        # Documentos
        docs_raw = row_dict.get("Documentação necessária") or row_dict.get("Documentacao necessaria", "")
        docs = split_documents(docs_raw)
        for doc_name in docs:
            if len(doc_name) >= 3:
                cur_main.execute("INSERT INTO service_documents (service_id, document_name) VALUES (?, ?)",
                               (service_id, doc_name))

        services_data.append({
            "service_id": service_id,
            "name": servico_nome,
            "secretaria": sec_nome,
            "categoria": cat_nome,
            "description": desc,
            "how": how,
            "address": addr,
            "who": who,
            "deadline": deadline,
            "cost": cost,
            "phones": ", ".join(set(phones)),
            "emails": ", ".join(set(emails)),
            "links": ", ".join(set(links)),
            "steps": " | ".join(steps[:5]),
            "docs": ", ".join(docs)
        })

    conn_main.commit()

    # Re-criação / Garantia da View vw_ia_servicos
    print("[2/4] Recriando a View Cognitiva 'vw_ia_servicos'...")
    cur_main.execute("DROP VIEW IF EXISTS vw_ia_servicos;")
    cur_main.execute("""
    CREATE VIEW vw_ia_servicos AS
    SELECT 
        s.id AS servico_id,
        sec.name AS secretaria_nome,
        sec.code AS secretaria_sigla,
        sec.code AS secretaria_codigo,
        sec.code AS secretaria_code,
        cat.name AS categoria_nome,
        cat.name AS categoria,
        s.name AS servico_nome,
        s.description AS descricao,
        s.how_to_access AS como_solicitar,
        s.how_to_access AS como_acessar,
        s.address AS endereco,
        s.who_can_request AS publico_alvo,
        s.who_can_request AS quem_pode_solicitar,
        s.max_deadline AS prazo_atendimento,
        s.max_deadline AS prazo_maximo,
        s.cost AS custo,
        s.waiting_time AS tempo_espera,
        s.regulation_norm AS norma_regulamentadora,
        s.regulation_norm AS norma_reguladora,
        (SELECT GROUP_CONCAT(phone, ', ') FROM service_phones WHERE service_id = s.id) AS telefones,
        (SELECT GROUP_CONCAT(email, ', ') FROM service_emails WHERE service_id = s.id) AS emails,
        (SELECT GROUP_CONCAT(link, ', ') FROM service_links WHERE service_id = s.id) AS links,
        (SELECT GROUP_CONCAT(document_name, '; ') FROM service_documents WHERE service_id = s.id) AS documentos,
        (SELECT GROUP_CONCAT(step_number || '. ' || description, '\n') FROM service_steps WHERE service_id = s.id) AS passo_a_passo
    FROM services s
    JOIN secretarias sec ON s.secretaria_id = sec.id
    LEFT JOIN categories cat ON s.category_id = cat.id
    WHERE s.status = 'published';
    """)
    conn_main.commit()
    conn_main.close()

    print(f"  [main.db OK] Secretarias: {count_sec} | Categorias: {count_cat} | Serviços: {count_services}")

    # 3. Vetorização e Atualização do vector.db
    print("[3/4] Atualizando o banco de dados vetorial (vector.db)...")
    conn_vector = sqlite3.connect(DATABASE_VECTOR)
    cur_vector = conn_vector.cursor()

    # Remove chunks antigos de carta_servicos
    cur_vector.execute("DELETE FROM duque_ia_chunks WHERE category = 'carta_servicos' OR source LIKE 'vw_ia_servicos%';")
    conn_vector.commit()

    gemini_client = GeminiClient()

    print(f"Vetorizando {len(services_data)} serviços com gemini-embedding-2...")

    embedded_count = 0
    for s_item in services_data:
        s_id = s_item["service_id"]
        s_name = s_item["name"]
        s_sec = s_item["secretaria"]
        s_cat = s_item["categoria"]

        # Conteúdo estruturado otimizado para o RAG
        content_text = (
            f"SERVIÇO MUNICIPAL: {s_name}\n"
            f"ÓRGÃO RESPONSÁVEL: {s_sec}\n"
            f"CATEGORIA: {s_cat}\n"
            f"DESCRIÇÃO: {s_item['description']}\n"
            f"COMO SOLICITAR / ACESSO: {s_item['how']}\n"
            f"ENDEREÇO: {s_item['address']}\n"
            f"QUEM PODE SOLICITAR: {s_item['who']}\n"
            f"PRAZO MÁXIMO: {s_item['deadline']}\n"
            f"CUSTO: {s_item['cost']}\n"
            f"CONTATOS: Telefone(s): {s_item['phones']} | E-mail(s): {s_item['emails']} | Link(s): {s_item['links']}\n"
            f"DOCUMENTOS NECESSÁRIOS: {s_item['docs']}\n"
            f"PASSO A PASSO: {s_item['steps']}"
        )

        source = f"vw_ia_servicos (ID: {s_id})"
        category = "carta_servicos"
        keywords = extract_keywords_heuristics(f"{s_name} {s_sec} {s_cat} {s_item['description']}")

        # Gera embedding real via Gemini
        emb = gemini_client.get_embedding(content_text)
        metadata = {
            "servico_id": s_id,
            "servico_nome": s_name,
            "secretaria": s_sec,
            "categoria": s_cat
        }

        cur_vector.execute("""
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            source,
            category,
            content_text,
            json.dumps(emb),
            json.dumps(metadata, ensure_ascii=False),
            json.dumps(keywords, ensure_ascii=False)
        ))

        embedded_count += 1
        if embedded_count % 50 == 0 or embedded_count == len(services_data):
            conn_vector.commit()
            print(f"  - Vetorizados {embedded_count}/{len(services_data)} serviços...")

    conn_vector.commit()
    conn_vector.close()

    print(f"\n[4/4] Processo concluído com sucesso!")
    print(f"  Serviços cadastrados em main.db   : {count_services}")
    print(f"  Chunks vetorizados em vector.db   : {embedded_count}")
    print("==========================================================")

if __name__ == "__main__":
    run_sync()
