# -*- coding: utf-8 -*-
"""
Módulo de Processamento e Ingestão Incremental de Webhooks do GSE/OGM para a Duque IA.
Executa UPSERT atômico em main.db e vector.db preservando integridade referencial,
regras de negócio e governança das secretarias.
"""

import os
import sys
import json
import sqlite3
import re
from datetime import datetime
import numpy as np

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

DB_MAIN = os.path.join(_PROJECT_ROOT, "data", "db", "main.db")
DB_VECTOR = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")
DB_TELEMETRY = os.path.join(_PROJECT_ROOT, "data", "db", "telemetry.db")

# Proibição absoluta do WhatsApp fictício
FORBIDDEN_WHATSAPP_PATTERN = re.compile(r'\(?21\)?\s*99824[-.\s]?5903', re.IGNORECASE)

def fix_encoding(text: str) -> str:
    """Corrige mojibake de UTF-8 interpretado como Latin-1 (ex: Ã§ -> ç, Ã£ -> ã)."""
    if not text or not isinstance(text, str):
        return text or ""
    if any(m in text for m in ['Ã', 'Â', 'â', 'ð']):
        try:
            return text.encode('latin1').decode('utf-8')
        except Exception:
            pass
    return text

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    fixed = fix_encoding(str(text))
    # Remove número fictício se vier em qualquer campo
    cleaned = FORBIDDEN_WHATSAPP_PATTERN.sub('', fixed)
    return cleaned.strip()

def ensure_schema():
    """Garante que colunas necessárias para enriquecimento SIGEM existam em main.db e tabela de log em telemetry.db."""
    # 1. main.db - secretaria_unidades
    conn = sqlite3.connect(DB_MAIN)
    c = conn.cursor()
    c.execute("PRAGMA table_info(secretaria_unidades);")
    cols = [r[1] for r in c.fetchall()]
    
    needed = [
        ("sigem_id", "TEXT"),
        ("bairro", "TEXT"),
        ("distrito", "TEXT"),
        ("cep", "TEXT"),
        ("latitude", "REAL"),
        ("longitude", "REAL"),
        ("email", "TEXT"),
        ("categoria", "TEXT"),
        ("status", "TEXT DEFAULT 'Ativo'"),
        ("updated_at", "TIMESTAMP")
    ]
    for col_name, col_type in needed:
        if col_name not in cols:
            c.execute(f"ALTER TABLE secretaria_unidades ADD COLUMN {col_name} {col_type};")
    conn.commit()
    conn.close()

    # 2. telemetry.db - webhook_events log
    tconn = sqlite3.connect(DB_TELEMETRY)
    tc = tconn.cursor()
    tc.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento TEXT,
            modulo TEXT,
            record_id TEXT,
            versao TEXT,
            alterado_em TEXT,
            payload_json TEXT,
            status TEXT,
            message TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    tc.execute("CREATE INDEX IF NOT EXISTS idx_webhook_events_modulo ON webhook_events (modulo, record_id);")
    tconn.commit()
    tconn.close()

def get_secretaria_id_by_sigla(sigla: str, nome: str = "") -> int:
    """Mapeia sigla ou nome da secretaria para o ID correspondente em main.db."""
    if not sigla and not nome:
        return 65 # Consolidado
    
    conn = sqlite3.connect(DB_MAIN)
    c = conn.cursor()
    
    # 1. Busca por sigla exata (ex: 'SMS', 'SMPA', 'SMF')
    sigla_clean = (sigla or "").strip().upper()
    if sigla_clean:
        c.execute("SELECT id FROM secretarias WHERE UPPER(code) = ?;", (sigla_clean,))
        row = c.fetchone()
        if row:
            conn.close()
            return row[0]
    
    # 2. Busca por nome parcial
    if nome:
        nome_clean = f"%{nome.strip()}%"
        c.execute("SELECT id FROM secretarias WHERE name LIKE ?;", (nome_clean,))
        row = c.fetchone()
        if row:
            conn.close()
            return row[0]
            
    conn.close()
    return 65 # Default Consolidado

def generate_embedding_blob(text: str) -> bytes | None:
    """Gera embedding de 3072 dimensões como float32 blob (12.288 bytes) via GeminiClient."""
    try:
        from utils.gemini_client import GeminiClient
        client = GeminiClient()
        emb = client.get_embedding(text, is_query=False)
        if emb and len(emb) == 3072:
            arr = np.array(emb, dtype=np.float32)
            return arr.tobytes()
    except Exception as e:
        print(f"[WebhookProcessor] Aviso: Não foi possível gerar embedding via Gemini: {e}")
    return None

def process_sigem_event(payload: dict) -> dict:
    """Processa evento do módulo SIGEM (equipamento.criado, equipamento.atualizado, equipamento.desativado)."""
    evento = payload.get("evento", "")
    dados = payload.get("dados_atuais", {})
    if not dados:
        return {"success": False, "error": "dados_atuais vazio"}

    sigem_id = str(dados.get("id") or "").strip()
    nome = sanitize_text(dados.get("nome") or dados.get("name") or "")
    sigla = sanitize_text(dados.get("sigla") or "")
    categoria = sanitize_text(dados.get("categoria") or "")
    secretaria_sigla = (dados.get("secretaria_sigla") or "").strip()
    secretaria_nome = sanitize_text(dados.get("secretaria_nome") or "")
    status = sanitize_text(dados.get("status") or "Ativo")
    horario = sanitize_text(dados.get("horario_funcionamento") or dados.get("horario") or dados.get("working_hours") or "")
    endereco = sanitize_text(dados.get("endereco_completo") or dados.get("endereco") or dados.get("address") or "")
    bairro = sanitize_text(dados.get("bairro_oficial") or dados.get("bairro") or "")
    distrito = sanitize_text(dados.get("distrito_oficial") or dados.get("distrito") or "")
    lat = dados.get("latitude") or dados.get("lat")
    lon = dados.get("longitude") or dados.get("lon")
    telefones = dados.get("telefones") or dados.get("phone") or []
    if isinstance(telefones, list):
        telefones_str = ", ".join([sanitize_text(t) for t in telefones if sanitize_text(t)])
    else:
        telefones_str = sanitize_text(telefones)
    emails = dados.get("emails") or dados.get("email") or []
    if isinstance(emails, list):
        emails_str = ", ".join([sanitize_text(e) for e in emails if sanitize_text(e)])
    else:
        emails_str = sanitize_text(emails)
    atualizado_em = dados.get("atualizado_em") or datetime.utcnow().isoformat()

    is_desativado = (evento == "equipamento.desativado") or (status.lower() in ["inativo", "desativado", "desativada"])
    secretaria_id = get_secretaria_id_by_sigla(secretaria_sigla, secretaria_nome)

    # 1. UPSERT em main.db (secretaria_unidades)
    conn = sqlite3.connect(DB_MAIN)
    c = conn.cursor()
    
    # Busca por sigem_id ou por nome exato
    c.execute("SELECT id FROM secretaria_unidades WHERE sigem_id = ? OR LOWER(name) = LOWER(?);", (sigem_id, nome))
    row = c.fetchone()
    
    if row:
        unit_id = row[0]
        c.execute("""
            UPDATE secretaria_unidades
            SET name = ?, address = ?, phone = ?, working_hours = ?, secretaria_id = ?,
                latitude = ?, longitude = ?, bairro = ?, distrito = ?, email = ?,
                categoria = ?, status = ?, sigem_id = ?, updated_at = ?
            WHERE id = ?;
        """, (nome, endereco, telefones_str, horario, secretaria_id, lat, lon, bairro, distrito, emails_str, categoria, status, sigem_id, atualizado_em, unit_id))
        action = "updated"
    else:
        c.execute("""
            INSERT INTO secretaria_unidades (
                secretaria_id, name, address, phone, working_hours,
                latitude, longitude, bairro, distrito, email, categoria, status, sigem_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (secretaria_id, nome, endereco, telefones_str, horario, lat, lon, bairro, distrito, emails_str, categoria, status, sigem_id, atualizado_em))
        unit_id = c.lastrowid
        action = "inserted"
    
    conn.commit()
    conn.close()

    # 2. UPSERT em vector.db (chunks e duque_ia_chunks)
    vconn = sqlite3.connect(DB_VECTOR)
    vc = vconn.cursor()

    chunk_id = f"sigem_{sigem_id}"
    chunk_title = f"Equipamento Público: {nome} ({bairro or 'Duque de Caxias'})"
    
    chunk_content = (
        f"EQUIPAMENTO PÚBLICO MUNICIPAL: {nome}\n"
        f"Órgão Responsável: {secretaria_nome} ({secretaria_sigla})\n"
        f"Categoria: {categoria}\n"
        f"Endereço: {endereco}\n"
        f"Bairro Oficial: {bairro} | Distrito: {distrito}\n"
        f"Horário de Funcionamento: {horario}\n"
        f"Telefones de Contato: {telefones_str or 'Não informado'}\n"
        f"E-mails: {emails_str or 'Não informado'}\n"
        f"Status da Unidade: {status}\n"
    )
    if lat and lon:
        chunk_content += f"Coordenadas GPS: Latitude {lat}, Longitude {lon}\n"

    metadata = {
        "tipo": "EQUIPAMENTO_PUBLICO",
        "modulo": "sigem",
        "sigem_id": sigem_id,
        "unit_id": unit_id,
        "bairro": bairro,
        "distrito": distrito,
        "secretaria": secretaria_sigla,
        "status": status,
        "updated_at": atualizado_em
    }
    metadata_json = json.dumps(metadata, ensure_ascii=False)

    if is_desativado:
        # Se foi desativado, remove do índice para não sugerir unidade fechada
        vc.execute("DELETE FROM chunks WHERE id = ?;", (chunk_id,))
        vc.execute("DELETE FROM duque_ia_chunks WHERE source = ?;", (chunk_id,))
        vector_action = "deleted_chunk"
    else:
        # Gera embedding
        embedding_blob = generate_embedding_blob(chunk_content)

        # Upsert em 'chunks' (mantém chunks_fts sincronizado via trigger)
        vc.execute("SELECT id FROM chunks WHERE id = ?;", (chunk_id,))
        if vc.fetchone():
            vc.execute("""
                UPDATE chunks
                SET tipo = 'EQUIPAMENTO_PUBLICO', titulo = ?, conteudo = ?, metadata_json = ?, vetor_blob = ?
                WHERE id = ?;
            """, (chunk_title, chunk_content, metadata_json, embedding_blob, chunk_id))
        else:
            vc.execute("""
                INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
                VALUES (?, 'EQUIPAMENTO_PUBLICO', ?, ?, ?, ?);
            """, (chunk_id, chunk_title, chunk_content, metadata_json, embedding_blob))

        # Upsert em 'duque_ia_chunks'
        vc.execute("SELECT id FROM duque_ia_chunks WHERE source = ?;", (chunk_id,))
        row_dia = vc.fetchone()
        keywords = f"{nome} {sigla} {bairro} {distrito} {categoria} {secretaria_sigla}"
        if row_dia:
            if embedding_blob:
                vc.execute("""
                    UPDATE duque_ia_chunks
                    SET category = 'EQUIPAMENTO_PUBLICO', content = ?, embedding = ?, metadata = ?, keywords = ?
                    WHERE source = ?;
                """, (chunk_content, embedding_blob, metadata_json, keywords, chunk_id))
            else:
                vc.execute("""
                    UPDATE duque_ia_chunks
                    SET category = 'EQUIPAMENTO_PUBLICO', content = ?, metadata = ?, keywords = ?
                    WHERE source = ?;
                """, (chunk_content, metadata_json, keywords, chunk_id))
        else:
            vc.execute("""
                INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
                VALUES (?, 'EQUIPAMENTO_PUBLICO', ?, ?, ?, ?);
            """, (chunk_id, chunk_content, embedding_blob, metadata_json, keywords))

        vector_action = "upserted_chunk"

    vconn.commit()
    vconn.close()

    return {
        "success": True,
        "modulo": "sigem",
        "action": action,
        "vector_action": vector_action,
        "unit_id": unit_id,
        "nome": nome,
        "status": status
    }

def process_cds_event(payload: dict) -> dict:
    """Processa evento do módulo CDS (servico.criado, servico.atualizado, servico.desativado)."""
    evento = payload.get("evento", "")
    dados = payload.get("dados_atuais", {})
    if not dados:
        return {"success": False, "error": "dados_atuais vazio"}

    cds_id = str(dados.get("id") or "").strip()
    name = sanitize_text(dados.get("nome") or dados.get("name") or "")
    description = sanitize_text(dados.get("descricao") or dados.get("description") or "")
    how_to_access = sanitize_text(dados.get("como_acessar") or dados.get("how_to_access") or "")
    address = sanitize_text(dados.get("endereco") or dados.get("address") or "")
    who_can_request = sanitize_text(dados.get("quem_pode_solicitar") or dados.get("who_can_request") or "")
    waiting_time = sanitize_text(dados.get("tempo_espera") or dados.get("waiting_time") or "")
    max_deadline = sanitize_text(dados.get("prazo_maximo") or dados.get("max_deadline") or "")
    cost = sanitize_text(dados.get("custo") or dados.get("cost") or "Gratuito")
    regulation_norm = sanitize_text(dados.get("norma_regulamentadora") or dados.get("regulation_norm") or "")
    status = sanitize_text(dados.get("status") or "published")
    secretaria_nome = sanitize_text(dados.get("secretaria_nome") or "")
    secretaria_sigla = (dados.get("secretaria_sigla") or "").strip()
    
    cat = dados.get("categorias") or dados.get("categoria_nome") or dados.get("categoria") or ""
    if isinstance(cat, list) and cat:
        categoria_nome = sanitize_text(cat[0])
    else:
        categoria_nome = sanitize_text(cat)
    atualizado_em = dados.get("atualizado_em") or datetime.utcnow().isoformat()

    is_desativado = (evento == "servico.desativado") or (status.lower() in ["disabled", "desativado", "desativada", "inativo"])
    secretaria_id = get_secretaria_id_by_sigla(secretaria_sigla, secretaria_nome)

    # 1. UPSERT em main.db (services)
    conn = sqlite3.connect(DB_MAIN)
    c = conn.cursor()
    
    # Tenta achar por ID numérico ou por Nome
    c.execute("SELECT id FROM services WHERE id = ? OR LOWER(name) = LOWER(?);", (cds_id, name))
    row = c.fetchone()

    if row:
        service_id = row[0]
        c.execute("""
            UPDATE services
            SET name = ?, description = ?, how_to_access = ?, address = ?,
                who_can_request = ?, waiting_time = ?, max_deadline = ?, cost = ?,
                regulation_norm = ?, status = ?, secretaria_id = ?, updated_at = ?
            WHERE id = ?;
        """, (name, description, how_to_access, address, who_can_request, waiting_time, max_deadline, cost, regulation_norm, status, secretaria_id, atualizado_em, service_id))
        action = "updated"
    else:
        c.execute("""
            INSERT INTO services (
                id, secretaria_id, name, description, how_to_access, address,
                who_can_request, waiting_time, max_deadline, cost, regulation_norm, status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (cds_id if cds_id.isdigit() else None, secretaria_id, name, description, how_to_access, address, who_can_request, waiting_time, max_deadline, cost, regulation_norm, status, atualizado_em))
        service_id = c.lastrowid
        action = "inserted"

    conn.commit()
    conn.close()

    # 2. UPSERT em vector.db
    vconn = sqlite3.connect(DB_VECTOR)
    vc = vconn.cursor()

    chunk_id = f"cds_{cds_id}"
    chunk_title = f"Serviço Municipal: {name} ({secretaria_nome})"
    
    chunk_content = (
        f"SERVIÇO PÚBLICO MUNICIPAL: {name}\n"
        f"Órgão / Secretaria Responsável: {secretaria_nome}\n"
        f"Categoria: {categoria_nome}\n"
        f"Descrição do Serviço: {description}\n"
        f"Como Solicitar / Etapas: {how_to_access}\n"
        f"Quem Pode Solicitar: {who_can_request}\n"
        f"Prazo Máximo de Conclusão: {max_deadline or 'Conforme demanda'} (Tempo de Espera: {waiting_time or 'Conforme ordem de chegada'})\n"
        f"Custo do Serviço: {cost}\n"
        f"Base Legal / Regulamentação: {regulation_norm}\n"
        f"Locais de Atendimento / Endereço: {address}\n"
        f"Status do Serviço: {status}\n"
    )

    metadata = {
        "tipo": "CARTA_SERVICOS",
        "modulo": "cds",
        "cds_id": cds_id,
        "service_id": service_id,
        "secretaria": secretaria_sigla,
        "status": status,
        "updated_at": atualizado_em
    }
    metadata_json = json.dumps(metadata, ensure_ascii=False)

    if is_desativado:
        vc.execute("DELETE FROM chunks WHERE id = ?;", (chunk_id,))
        vc.execute("DELETE FROM duque_ia_chunks WHERE source = ?;", (chunk_id,))
        vector_action = "deleted_chunk"
    else:
        embedding_blob = generate_embedding_blob(chunk_content)

        vc.execute("SELECT id FROM chunks WHERE id = ?;", (chunk_id,))
        if vc.fetchone():
            vc.execute("""
                UPDATE chunks
                SET tipo = 'CARTA_SERVICOS', titulo = ?, conteudo = ?, metadata_json = ?, vetor_blob = ?
                WHERE id = ?;
            """, (chunk_title, chunk_content, metadata_json, embedding_blob, chunk_id))
        else:
            vc.execute("""
                INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
                VALUES (?, 'CARTA_SERVICOS', ?, ?, ?, ?);
            """, (chunk_id, chunk_title, chunk_content, metadata_json, embedding_blob))

        vc.execute("SELECT id FROM duque_ia_chunks WHERE source = ?;", (chunk_id,))
        row_dia = vc.fetchone()
        keywords = f"{name} {secretaria_nome} {categoria_nome} servico publico duque de caxias"
        if row_dia:
            if embedding_blob:
                vc.execute("""
                    UPDATE duque_ia_chunks
                    SET category = 'CARTA_SERVICOS', content = ?, embedding = ?, metadata = ?, keywords = ?
                    WHERE source = ?;
                """, (chunk_content, embedding_blob, metadata_json, keywords, chunk_id))
            else:
                vc.execute("""
                    UPDATE duque_ia_chunks
                    SET category = 'CARTA_SERVICOS', content = ?, metadata = ?, keywords = ?
                    WHERE source = ?;
                """, (chunk_content, metadata_json, keywords, chunk_id))
        else:
            vc.execute("""
                INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
                VALUES (?, 'CARTA_SERVICOS', ?, ?, ?, ?);
            """, (chunk_id, chunk_content, embedding_blob, metadata_json, keywords))

        vector_action = "upserted_chunk"

    vconn.commit()
    vconn.close()

    return {
        "success": True,
        "modulo": "cds",
        "action": action,
        "vector_action": vector_action,
        "service_id": service_id,
        "name": name,
        "status": status
    }

def log_webhook_event(payload: dict, result: dict):
    """Grava o evento no histórico de auditoria em telemetry.db."""
    try:
        tconn = sqlite3.connect(DB_TELEMETRY)
        tc = tconn.cursor()
        evento = payload.get("evento", "desconhecido")
        modulo = payload.get("modulo", "desconhecido")
        record_id = str(payload.get("id", ""))
        versao = str(payload.get("versao", ""))
        alterado_em = payload.get("alterado_em", "")
        payload_str = json.dumps(payload, ensure_ascii=False)
        status = "sucesso" if result.get("success") else "erro"
        msg = json.dumps(result, ensure_ascii=False)

        tc.execute("""
            INSERT INTO webhook_events (evento, modulo, record_id, versao, alterado_em, payload_json, status, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (evento, modulo, record_id, versao, alterado_em, payload_str, status, msg))
        tconn.commit()
        tconn.close()
    except Exception as e:
        print(f"[WebhookProcessor] Aviso: falha ao logar evento em telemetry.db: {e}")

def process_webhook_payload(payload: dict) -> dict:
    """Ponto de entrada para processamento de webhook."""
    ensure_schema()
    
    modulo = (payload.get("modulo") or "").lower()
    evento = payload.get("evento") or ""

    if modulo == "sigem" or evento.startswith("equipamento."):
        result = process_sigem_event(payload)
    elif modulo == "cds" or evento.startswith("servico."):
        result = process_cds_event(payload)
    else:
        result = {"success": False, "error": f"Módulo desconhecido: '{modulo}' (evento: '{evento}')"}

    log_webhook_event(payload, result)
    return result

def main():
    """Entrada CLI: lê JSON de sys.stdin ou argumento."""
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            raw_input = f.read()
    elif len(sys.argv) > 1:
        raw_input = sys.argv[1]
    else:
        raw_input = sys.stdin.read()

    try:
        payload = json.loads(raw_input)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"JSON inválido: {e}"}))
        sys.exit(1)

    res = process_webhook_payload(payload)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

