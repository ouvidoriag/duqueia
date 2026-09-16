# -*- coding: utf-8 -*-
"""
Script de Ingestão dos 1.575 Chunks Mestres do BANCODUQUEIA para vector.db.
1. Cria tabelas 'chunks' e 'chunks_fts' (FTS5) em data/db/vector.db.
2. Ingesta todos os 1.575 chunks de CHUNKS_MESTRES_UNIFICADOS.jsonl no índice FTS5.
3. Sincroniza incrementalmente os 1.575 chunks na tabela 'duque_ia_chunks'
   (para compatibilidade total com o mecanismo híbrido existente).
"""

import os
import sys
import json
import sqlite3
import struct
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_VECTOR = os.path.join(BASE_DIR, "data", "db", "vector.db")
CHUNKS_FILE = os.path.join(BASE_DIR, "data", "knowledge", "bancoduqueia", "pipeline_storage", "CHUNKS_MESTRES_UNIFICADOS.jsonl")

def main():
    print("=== INICIANDO INGESTAO BANCODUQUEIA -> VECTOR.DB ===")
    
    if not os.path.exists(CHUNKS_FILE):
        print(f"[ERRO] Arquivo de chunks nao encontrado: {CHUNKS_FILE}")
        sys.exit(1)

    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    # 1. Criação das tabelas de alta performance FTS5
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        tipo TEXT,
        titulo TEXT,
        conteudo TEXT,
        metadata_json TEXT,
        vetor_blob BLOB
    );
    """)

    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        id UNINDEXED,
        titulo,
        conteudo,
        tipo,
        tokenize = 'unicode61 remove_diacritics 1'
    );
    """)

    # Garante existência de duque_ia_chunks
    cur.execute("""
    CREATE TABLE IF NOT EXISTS duque_ia_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT UNIQUE,
        category TEXT,
        content TEXT,
        embedding TEXT,
        metadata TEXT,
        keywords TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # 2. Leitura dos chunks mestres unificados
    print(f"[*] Lendo {CHUNKS_FILE}...")
    chunks = []
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    print(f"[*] Total de chunks carregados do arquivo: {len(chunks)}")

    # Ingestão em chunks e chunks_fts
    fts_inseridos = 0
    duque_ia_inseridos = 0

    for c in chunks:
        cid = c.get("chunk_id")
        tipo = c.get("tipo_documento", "GERAL")
        titulo = c.get("titulo", "")
        conteudo = c.get("conteudo", "")
        meta = c.get("metadata", {})
        meta_str = json.dumps(meta, ensure_ascii=False)
        tags = meta.get("tags", [])
        tags_str = json.dumps(tags, ensure_ascii=False)
        
        # Vetor se disponível
        vec = c.get("vector")
        vetor_blob = struct.pack(f"{len(vec)}f", *vec) if vec and isinstance(vec, list) else None

        # Insert/Replace em chunks
        cur.execute("""
            INSERT OR REPLACE INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cid, tipo, titulo, conteudo, meta_str, vetor_blob))

        # Manutenção de chunks_fts
        cur.execute("DELETE FROM chunks_fts WHERE id = ?", (cid,))
        cur.execute("""
            INSERT INTO chunks_fts (id, titulo, conteudo, tipo)
            VALUES (?, ?, ?, ?)
        """, (cid, titulo, conteudo, tipo))
        fts_inseridos += 1

        # Sincronização incremental em duque_ia_chunks
        cat_lower = tipo.lower()
        cur.execute("SELECT id FROM duque_ia_chunks WHERE source = ?", (cid,))
        row_vec = cur.fetchone()
        if row_vec:
            cur.execute("""
                UPDATE duque_ia_chunks
                SET category = ?, content = ?, metadata = ?, keywords = ?
                WHERE id = ?
            """, (cat_lower, conteudo, meta_str, tags_str, row_vec[0]))
        else:
            cur.execute("""
                INSERT INTO duque_ia_chunks (source, category, content, metadata, keywords)
                VALUES (?, ?, ?, ?, ?)
            """, (cid, cat_lower, conteudo, meta_str, tags_str))
        duque_ia_inseridos += 1

    conn.commit()
    print(f"[OK] {fts_inseridos} chunks indexados em chunks e chunks_fts (FTS5).")
    print(f"[OK] {duque_ia_inseridos} chunks sincronizados em duque_ia_chunks.")

    # Verificação de contagem final
    cur.execute("SELECT count(*) FROM chunks")
    c_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM duque_ia_chunks")
    d_count = cur.fetchone()[0]
    print(f"[OK] Contagem final em vector.db: chunks={c_count}, duque_ia_chunks={d_count}")

    conn.close()
    print("=== INGESTAO EM VECTOR.DB CONCLUIDA COM SUCESSO ===")

if __name__ == "__main__":
    main()
