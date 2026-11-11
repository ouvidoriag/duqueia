# -*- coding: utf-8 -*-
"""
Sincroniza os 23 chunks canônicos exclusivos da tabela 'chunks' 
para a tabela 'duque_ia_chunks' em vector.db.
Garante que todas as regras de negócio canônicas e autoridades 
estejam presentes no inventário da busca vetorial/híbrida.
"""

import os
import sys
import json
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_VECTOR = os.path.join(BASE_DIR, "data", "db", "vector.db")

def sync_missing_chunks():
    print("=== SINCRONIZANDO CHUNKS CANÔNICOS EM DUQUE_IA_CHUNKS ===")
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.tipo, c.titulo, c.conteudo, c.metadata_json
        FROM chunks c
        LEFT JOIN duque_ia_chunks d ON c.id = d.source
        WHERE d.source IS NULL
    """)
    missing = cur.fetchall()
    print(f"[*] Chunks canônicos a sincronizar: {len(missing)}")

    inserted = 0
    for cid, tipo, tit, cont, meta_str in missing:
        cat_lower = tipo.lower()
        try:
            meta = json.loads(meta_str) if meta_str else {}
        except Exception:
            meta = {}
            
        meta["title"] = tit
        tags = meta.get("tags", [])
        
        # Garante inserção limpa em duque_ia_chunks
        cur.execute("""
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cid,
            cat_lower,
            cont,
            None, # Embedding será gerado na Etapa 3
            json.dumps(meta, ensure_ascii=False),
            json.dumps(tags, ensure_ascii=False)
        ))
        inserted += 1

    conn.commit()
    print(f"[OK] {inserted} chunks canônicos inseridos em 'duque_ia_chunks'.")

    # Verificação pós-sincronização
    cur.execute("""
        SELECT COUNT(*)
        FROM chunks c
        LEFT JOIN duque_ia_chunks d ON c.id = d.source
        WHERE d.source IS NULL
    """)
    remaining = cur.fetchone()[0]
    print(f"[OK] Chunks em 'chunks' sem correspondente em 'duque_ia_chunks': {remaining}")

    conn.close()

if __name__ == "__main__":
    sync_missing_chunks()

