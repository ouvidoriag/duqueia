# -*- coding: utf-8 -*-
"""
Script de Ingestão Incremental dos Dados Mestres do BANCODUQUEIA para main.db.
Importa:
1. Secretarias (19 secretarias oficiais auditadas)
2. Equipamentos Públicos (442 equipamentos com endereços, GPS e contatos)
3. Serviços Públicos Municipais (656 serviços, passos, documentos e canais)
4. Regras Canônicas de Negócio (57 regras com pesos de boost)
5. Leis e Atos Normativos Municipais (29 leis municipais)
6. Linhas Tarifa Zero (transporte gratuito)
7. Bairros e Distritos Oficiais
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Assegura caminhos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_MAIN = os.path.join(BASE_DIR, "data", "db", "main.db")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "data", "knowledge", "bancoduqueia", "dados_mestres")

def get_conn():
    conn = sqlite3.connect(DB_MAIN)
    conn.execute("PRAGMA foreign_keys = OFF;") # Modo de carga incremental
    return conn

def setup_additional_tables(conn):
    cur = conn.cursor()
    
    # 1. Regras Canônicas de Negócio
    cur.execute("""
    CREATE TABLE IF NOT EXISTS regras_negocio (
        id TEXT PRIMARY KEY,
        tipo TEXT,
        tipo_label TEXT,
        tema TEXT,
        assunto TEXT,
        conteudo TEXT,
        tags TEXT,
        prioridade TEXT,
        boost_weight REAL DEFAULT 1.0,
        autor TEXT,
        data_homologacao TEXT,
        links_oficiais TEXT,
        homologado_por TEXT
    );
    """)
    
    # 2. Leis e Atos Normativos Municipais
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leis_municipais (
        id TEXT PRIMARY KEY,
        numero TEXT,
        ano INTEGER,
        tipo TEXT,
        ementa TEXT,
        orgao_emissor TEXT,
        data_publicacao TEXT,
        situacao TEXT,
        assuntos TEXT,
        fonte_url TEXT
    );
    """)
    
    # 3. Linhas Tarifa Zero
    cur.execute("""
    CREATE TABLE IF NOT EXISTS linhas_tarifa_zero (
        id TEXT PRIMARY KEY,
        numero_linha TEXT,
        nome_linha TEXT,
        itinerario TEXT,
        horario TEXT,
        tarifa REAL DEFAULT 0.0,
        secretarias_gestoras TEXT,
        base_legal TEXT
    );
    """)
    
    # 4. Bairros e Distritos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bairros_distritos (
        id TEXT PRIMARY KEY,
        nome TEXT,
        distrito INTEGER,
        distrito_nome TEXT,
        regiao TEXT,
        aliases TEXT
    );
    """)
    
    conn.commit()
    print("[OK] Tabelas institucionais verificadas/criadas em main.db.")

def ingest_secretarias(conn):
    sec_file = os.path.join(KNOWLEDGE_DIR, "secretarias.json")
    if not os.path.exists(sec_file):
        print(f"[AVISO] Arquivo {sec_file} nao encontrado.")
        return {}

    with open(sec_file, "r", encoding="utf-8") as f:
        secretarias = json.load(f)

    cur = conn.cursor()
    sec_map = {} # sigla -> id em main.db

    for s in secretarias:
        sigla = s.get("sigla", "").strip()
        nome = s.get("nome_oficial", "").strip()
        endereco = s.get("endereco") or s.get("endereco_oficial")
        telefone = s.get("telefone")
        email = s.get("email")
        horario = s.get("horario_atendimento", "Segunda a sexta-feira, das 9h as 17h")

        # Verifica se ja existe por codigo/sigla
        cur.execute("SELECT id FROM secretarias WHERE code = ? OR name = ?", (sigla, nome))
        row = cur.fetchone()

        if row:
            sec_id = row[0]
            cur.execute("""
                UPDATE secretarias 
                SET name = ?, code = ?, address = COALESCE(?, address), 
                    phone = COALESCE(?, phone), email = COALESCE(?, email), 
                    working_hours = COALESCE(?, working_hours)
                WHERE id = ?
            """, (nome, sigla, endereco, telefone, email, horario, sec_id))
        else:
            cur.execute("""
                INSERT INTO secretarias (name, code, address, phone, email, working_hours)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nome, sigla, endereco, telefone, email, horario))
            sec_id = cur.lastrowid

        sec_map[sigla] = sec_id
        sec_map[s.get("id")] = sec_id

    conn.commit()
    print(f"[OK] {len(secretarias)} secretarias ingeridas/atualizadas em main.db.")
    return sec_map

def ingest_equipamentos(conn, sec_map):
    eq_file = os.path.join(KNOWLEDGE_DIR, "equipamentos.json")
    if not os.path.exists(eq_file):
        print(f"[AVISO] Arquivo {eq_file} nao encontrado.")
        return

    with open(eq_file, "r", encoding="utf-8") as f:
        equipamentos = json.load(f)

    cur = conn.cursor()
    inseridos = 0
    atualizados = 0

    for eq in equipamentos:
        nome = eq.get("nome_oficial", "").strip()
        endereco = eq.get("endereco_completo") or eq.get("logradouro", "")
        telefone = eq.get("telefone")
        horario = eq.get("horario", "Segunda a sexta-feira, das 8h as 17h")
        
        # Encontra secretaria_id associada
        sec_sigla = eq.get("secretaria_sigla", "").strip()
        sec_resp_id = eq.get("secretaria_responsavel_id", "").strip()
        sec_id = sec_map.get(sec_sigla) or sec_map.get(sec_resp_id) or 65 # fallback

        # Verifica existencia por nome exato
        cur.execute("SELECT id FROM secretaria_unidades WHERE name = ?", (nome,))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE secretaria_unidades
                SET secretaria_id = ?, address = COALESCE(?, address),
                    phone = COALESCE(?, phone), working_hours = COALESCE(?, working_hours)
                WHERE id = ?
            """, (sec_id, endereco, telefone, horario, row[0]))
            atualizados += 1
        else:
            cur.execute("""
                INSERT INTO secretaria_unidades (secretaria_id, name, address, phone, working_hours)
                VALUES (?, ?, ?, ?, ?)
            """, (sec_id, nome, endereco, telefone, horario))
            inseridos += 1

    conn.commit()
    print(f"[OK] Equipamentos em secretaria_unidades: {inseridos} novos inseridos, {atualizados} atualizados (Total: {inseridos + atualizados}).")

def ingest_servicos(conn, sec_map):
    srv_file = os.path.join(KNOWLEDGE_DIR, "servicos.json")
    if not os.path.exists(srv_file):
        print(f"[AVISO] Arquivo {srv_file} nao encontrado.")
        return

    with open(srv_file, "r", encoding="utf-8") as f:
        servicos = json.load(f)

    cur = conn.cursor()
    # Cache de categorias existentes
    cur.execute("SELECT id, name FROM categories")
    cat_map = {row[1].lower(): row[0] for row in cur.fetchall()}

    inseridos = 0
    atualizados = 0

    for s in servicos:
        nome = s.get("servico", "").strip()
        if not nome:
            continue

        sec_id_cand = s.get("orgao_id", "")
        sec_nome = s.get("orgao", "")
        # Resolve secretaria
        sec_id = sec_map.get(sec_id_cand)
        if not sec_id:
            for sigla, sid in sec_map.items():
                if sigla.lower() in sec_nome.lower():
                    sec_id = sid
                    break
        if not sec_id:
            sec_id = 65

        # Categoria
        cat_nome = s.get("categoria", "Geral").strip()
        cat_id = cat_map.get(cat_nome.lower())
        if not cat_id:
            cur.execute("INSERT INTO categories (name) VALUES (?)", (cat_nome,))
            cat_id = cur.lastrowid
            cat_map[cat_nome.lower()] = cat_id

        desc = s.get("descricao")
        como = s.get("como_acessar")
        endereco = s.get("endereco")
        quem = s.get("publico_alvo")
        espera = s.get("tempo_espera")
        prazo = s.get("prazo_estimado")
        custo = s.get("custo", "Gratuito")
        norma = s.get("normas")

        # Verifica se o servico ja existe por nome exato
        cur.execute("SELECT id FROM services WHERE name = ?", (nome,))
        row = cur.fetchone()

        if row:
            s_id = row[0]
            cur.execute("""
                UPDATE services
                SET secretaria_id = ?, category_id = ?, description = COALESCE(?, description),
                    how_to_access = COALESCE(?, how_to_access), address = COALESCE(?, address),
                    who_can_request = COALESCE(?, who_can_request), waiting_time = COALESCE(?, waiting_time),
                    max_deadline = COALESCE(?, max_deadline), cost = COALESCE(?, cost),
                    regulation_norm = COALESCE(?, regulation_norm), status = 'published',
                    updated_at = datetime('now')
                WHERE id = ?
            """, (sec_id, cat_id, desc, como, endereco, quem, espera, prazo, custo, norma, s_id))
            atualizados += 1
        else:
            cur.execute("""
                INSERT INTO services (
                    secretaria_id, category_id, name, description, how_to_access,
                    address, who_can_request, waiting_time, max_deadline, cost,
                    regulation_norm, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published', datetime('now'), datetime('now'))
            """, (sec_id, cat_id, nome, desc, como, endereco, quem, espera, prazo, custo, norma))
            s_id = cur.lastrowid
            inseridos += 1

        # Limpa dados detalhados antigos para reinsercao limpa deste servico
        cur.execute("DELETE FROM service_steps WHERE service_id = ?", (s_id,))
        cur.execute("DELETE FROM service_documents WHERE service_id = ?", (s_id,))
        cur.execute("DELETE FROM service_phones WHERE service_id = ?", (s_id,))
        cur.execute("DELETE FROM service_emails WHERE service_id = ?", (s_id,))
        cur.execute("DELETE FROM service_links WHERE service_id = ?", (s_id,))

        # Passos
        passos = s.get("passo_a_passo") or []
        for p_idx, p_text in enumerate(passos, 1):
            if p_text and str(p_text).strip():
                cur.execute("INSERT INTO service_steps (service_id, step_number, description) VALUES (?, ?, ?)", (s_id, p_idx, str(p_text).strip()))

        # Documentos
        docs = s.get("documentos_detalhados") or s.get("documentos_necessarios") or []
        if isinstance(docs, str):
            docs = [d.strip() for d in docs.split("\n") if d.strip()]
        for d_text in docs:
            if d_text and str(d_text).strip():
                cur.execute("INSERT INTO service_documents (service_id, document_name) VALUES (?, ?)", (s_id, str(d_text).strip()))

        # Telefones
        phones = s.get("telefones") or []
        if isinstance(phones, str): phones = [phones]
        for ph in phones:
            if ph and str(ph).strip():
                cur.execute("INSERT INTO service_phones (service_id, phone) VALUES (?, ?)", (s_id, str(ph).strip()))

        # E-mails
        emails = s.get("emails") or []
        if isinstance(emails, str): emails = [emails]
        for em in emails:
            if em and str(em).strip():
                cur.execute("INSERT INTO service_emails (service_id, email) VALUES (?, ?)", (s_id, str(em).strip()))

        # Links
        links = s.get("links") or []
        if isinstance(links, str): links = [links]
        for lk in links:
            if lk and str(lk).strip():
                cur.execute("INSERT INTO service_links (service_id, link) VALUES (?, ?)", (s_id, str(lk).strip()))

    conn.commit()
    print(f"[OK] Servicos publicos: {inseridos} novos inseridos, {atualizados} atualizados (Total processado: {inseridos + atualizados}).")

def ingest_regras_negocio(conn):
    regras_file = os.path.join(KNOWLEDGE_DIR, "regras_negocio.json")
    if not os.path.exists(regras_file):
        return

    with open(regras_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    regras = data.get("regras", [])
    cur = conn.cursor()

    for r in regras:
        rid = r.get("id")
        tipo = r.get("tipo")
        tipo_lbl = r.get("tipo_label")
        tema = r.get("tema")
        assunto = r.get("assunto")
        conteudo = r.get("conteudo")
        tags = json.dumps(r.get("tags", []), ensure_ascii=False)
        prio = r.get("prioridade", "MEDIA")
        boost = float(r.get("boost_weight", 1.0))
        autor = r.get("autor")
        data_h = r.get("data_homologacao")
        links = json.dumps(r.get("links_oficiais", []), ensure_ascii=False)
        homolog = r.get("homologado_por")
        if isinstance(homolog, (list, dict)):
            homolog = json.dumps(homolog, ensure_ascii=False)

        cur.execute("""
            INSERT OR REPLACE INTO regras_negocio (
                id, tipo, tipo_label, tema, assunto, conteudo, tags,
                prioridade, boost_weight, autor, data_homologacao, links_oficiais, homologado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rid, tipo, tipo_lbl, tema, assunto, conteudo, tags, prio, boost, autor, data_h, links, homolog))

    conn.commit()
    print(f"[OK] {len(regras)} regras canonicas de negocio ingeridas em main.db.")

def ingest_leis(conn):
    leis_file = os.path.join(KNOWLEDGE_DIR, "leis.json")
    if not os.path.exists(leis_file):
        return

    with open(leis_file, "r", encoding="utf-8") as f:
        leis = json.load(f)

    cur = conn.cursor()
    for lei in leis:
        lid = lei.get("id")
        num = str(lei.get("numero", ""))
        ano = int(lei.get("ano", 0)) if lei.get("ano") else None
        tipo = lei.get("tipo")
        ementa = lei.get("ementa")
        emissor = lei.get("orgao_emissor")
        pub = lei.get("data_publicacao")
        sit = lei.get("situacao")
        assuntos = json.dumps(lei.get("assuntos", []), ensure_ascii=False)
        fonte = lei.get("fonte_url")

        cur.execute("""
            INSERT OR REPLACE INTO leis_municipais (
                id, numero, ano, tipo, ementa, orgao_emissor, data_publicacao, situacao, assuntos, fonte_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (lid, num, ano, tipo, ementa, emissor, pub, sit, assuntos, fonte))

    conn.commit()
    print(f"[OK] {len(leis)} leis e normativas municipais ingeridas em main.db.")

def ingest_linhas_tarifa_zero(conn):
    tz_file = os.path.join(KNOWLEDGE_DIR, "linhas_tarifa_zero.json")
    if not os.path.exists(tz_file):
        return

    with open(tz_file, "r", encoding="utf-8") as f:
        linhas = json.load(f)

    if isinstance(linhas, dict):
        linhas = linhas.get("linhas", [linhas])

    cur = conn.cursor()
    for l in linhas:
        lid = str(l.get("id") or l.get("nome_oficial") or l.get("numero_linha", ""))
        num = str(l.get("numero_linha", ""))
        nome = str(l.get("nome_oficial") or l.get("nome_linha", ""))
        ruas = l.get("principais_ruas_atendidas") or []
        itin = ", ".join(ruas) if isinstance(ruas, list) else str(l.get("itinerario") or "")
        horarios = l.get("horarios_saida") or []
        if isinstance(horarios, (list, dict)):
            horario = json.dumps(horarios, ensure_ascii=False)
        else:
            horario = str(l.get("horario", "Diario"))
        tarifa_raw = l.get("tarifa", 0.0)
        try:
            tarifa = float(tarifa_raw)
        except (ValueError, TypeError):
            tarifa = 0.0
        sec = str(l.get("secretaria_responsavel") or l.get("orgao_gestor") or "SMSP")
        base_l = str(l.get("base_legal", "Decreto Municipal nº 8.120/2023"))

        cur.execute("""
            INSERT OR REPLACE INTO linhas_tarifa_zero (
                id, numero_linha, nome_linha, itinerario, horario, tarifa, secretarias_gestoras, base_legal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (lid, num, nome, itin, horario, tarifa, sec, base_l))

    conn.commit()
    print(f"[OK] {len(linhas)} registros de Linhas Tarifa Zero ingeridos em main.db.")

def ingest_bairros(conn):
    bairros_file = os.path.join(KNOWLEDGE_DIR, "bairros.json")
    if not os.path.exists(bairros_file):
        return

    with open(bairros_file, "r", encoding="utf-8") as f:
        bairros = json.load(f)

    cur = conn.cursor()
    for b in bairros:
        bid = b.get("id")
        nome = b.get("nome")
        dist = b.get("distrito")
        dist_int = int(dist.split("º")[0].strip()) if isinstance(dist, str) and "º" in dist else None
        dist_nome = b.get("distrito_nome")
        regiao = b.get("regiao")
        aliases = json.dumps(b.get("aliases", []), ensure_ascii=False)

        cur.execute("""
            INSERT OR REPLACE INTO bairros_distritos (
                id, nome, distrito, distrito_nome, regiao, aliases
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (bid, nome, dist_int, dist_nome, regiao, aliases))

    conn.commit()
    print(f"[OK] {len(bairros)} bairros e distritos ingeridos em main.db.")

def refresh_views(conn):
    cur = conn.cursor()
    cur.execute("DROP VIEW IF EXISTS vw_ia_servicos;")
    cur.execute("""
        CREATE VIEW vw_ia_servicos AS
        SELECT 
            s.id AS servico_id,
            sec.name AS secretaria_nome,
            sec.code AS secretaria_codigo,
            s.name AS servico_nome,
            c.name AS categoria,
            s.description AS descricao,
            s.how_to_access AS como_acessar,
            s.who_can_request AS quem_pode_solicitar,
            s.waiting_time AS tempo_espera,
            s.max_deadline AS prazo_maximo,
            s.cost AS custo,
            s.regulation_norm AS norma_reguladora
        FROM services s
        LEFT JOIN secretarias sec ON s.secretaria_id = sec.id
        LEFT JOIN categories c ON s.category_id = c.id
        WHERE s.status = 'published';
    """)
    conn.commit()
    print("[OK] View vw_ia_servicos atualizada com sucesso.")

def main():
    print("=== INICIANDO INGESTAO BANCODUQUEIA -> MAIN.DB ===")
    conn = get_conn()
    try:
        setup_additional_tables(conn)
        sec_map = ingest_secretarias(conn)
        ingest_equipamentos(conn, sec_map)
        ingest_servicos(conn, sec_map)
        ingest_regras_negocio(conn)
        ingest_leis(conn)
        ingest_linhas_tarifa_zero(conn)
        ingest_bairros(conn)
        refresh_views(conn)
        print("=== INGESTAO EM MAIN.DB CONCLUIDA COM SUCESSO ===")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
