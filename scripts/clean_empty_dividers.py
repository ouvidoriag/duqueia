# -*- coding: utf-8 -*-
"""
Higienização Cirúrgica de Chunks:
Remove EXCLUSIVAMENTE os 15 chunks que são meros cabeçalhos e divisores de página 
(sem qualquer conteúdo factual, telefone, endereço ou procedimento).
Preserva todos os 24 chunks com dados válidos (incluindo carta_01338 com endereço da Defesa Civil).
"""

import os
import sys
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_VECTOR = os.path.join(BASE_DIR, "data", "db", "vector.db")

CHUNKS_TO_REMOVE = [
    "geo_01568",
    "carta_01309",
    "carta_01416",
    "carta_01360",
    "carta_01423",
    "carta_01468",
    "carta_01317",
    "carta_01219",
    "carta_01330",
    "carta_01283",
    "carta_01386",
    "carta_01493",
    "carta_01325",
    "carta_01289",
    "carta_01454"
]

def clean_empty_dividers():
    print("=== HIGIENIZAÇÃO CIRÚRGICA DOS 15 CHUNKS DE DIVISÃO DE PÁGINA ===")
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    removed_chunks = 0
    removed_fts = 0
    removed_duque_ia = 0

    for cid in CHUNKS_TO_REMOVE:
        cur.execute("DELETE FROM chunks WHERE id = ?", (cid,))
        removed_chunks += cur.rowcount

        cur.execute("DELETE FROM chunks_fts WHERE id = ?", (cid,))
        removed_fts += cur.rowcount

        cur.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (cid,))
        removed_duque_ia += cur.rowcount

    conn.commit()
    print(f"[OK] Removidos de 'chunks': {removed_chunks}")
    print(f"[OK] Removidos de 'chunks_fts': {removed_fts}")
    print(f"[OK] Removidos de 'duque_ia_chunks': {removed_duque_ia}")

    # Validação de preservação do chunk carta_01338 (Defesa Civil)
    cur.execute("SELECT id, conteudo FROM chunks WHERE id = 'carta_01338'")
    row_dc = cur.fetchone()
    if row_dc:
        print(f"[OK] Validação de Preservação: 'carta_01338' (Defesa Civil) permanece intacto com {len(row_dc[1])} caracteres.")
    else:
        print("[ERRO] carta_01338 não encontrado!")

    conn.close()

if __name__ == "__main__":
    clean_empty_dividers()

