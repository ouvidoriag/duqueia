# -*- coding: utf-8 -*-
"""
Vetorização Incremental em Lote (Etapa 3 do Roadmap DUQUE IA 2.0):
Gera embeddings de 3.072 dimensões com o modelo oficial 'gemini-embedding-2'
para todos os chunks pendentes em vector.db (duque_ia_chunks e chunks.vetor_blob).

Características de Segurança:
  - Execução atômica e idempotente por lotes (batch_size=25).
  - Pool de 3 workers concorrentes para alta performance (~0.25s por chunk).
  - Commits transacionais a cada lote (resiliência contra interrupções).
  - Alimenta duque_ia_chunks.embedding (JSON) e chunks.vetor_blob (Binary float32).
"""

import os
import sys
import json
import sqlite3
import struct
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from utils.gemini_client import GeminiClient

DB_VECTOR = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")
BATCH_SIZE = 25
MAX_WORKERS = 3

def vectorize_all():
    print("=" * 70)
    print("   DUQUE IA — VETORIZAÇÃO INCREMENTAL EM LOTE (gemini-embedding-2)")
    print("=" * 70)

    client = GeminiClient()
    if not client.api_keys:
        print("[ERRO] Nenhuma chave de API configurada no .env!")
        sys.exit(1)

    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    cur.execute("""
        SELECT count(*)
        FROM duque_ia_chunks
        WHERE embedding IS NULL OR length(embedding) < 100
    """)
    total_pending = cur.fetchone()[0]

    cur.execute("""
        SELECT count(*)
        FROM duque_ia_chunks
        WHERE embedding IS NOT NULL AND length(embedding) >= 100
    """)
    already_embedded = cur.fetchone()[0]

    print(f"[*] Chunks já vetorizados com 3072d : {already_embedded}")
    print(f"[*] Chunks pendentes de vetorização : {total_pending}")

    if total_pending == 0:
        print("[OK] Todos os chunks já possuem embeddings de 3072 dimensões! 100% completo.")
        conn.close()
        return

    def embed_worker(item):
        cid, src, cont = item
        # Usar até 1800 caracteres para embedding semântico de alta densidade
        text_clean = cont[:1800].strip()
        for attempt in range(3):
            try:
                vec = client.get_embedding(text_clean, is_query=False)
                if vec and len(vec) == 3072:
                    return cid, src, vec, None
                time.sleep(0.5)
            except Exception as e:
                if attempt == 2:
                    return cid, src, None, str(e)
                time.sleep(1.0)
        return cid, src, None, "Tentativas esgotadas"

    start_total = time.time()
    processed_count = 0
    batch_idx = 0

    while True:
        cur.execute("""
            SELECT id, source, content
            FROM duque_ia_chunks
            WHERE embedding IS NULL OR length(embedding) < 100
            LIMIT ?
        """, (BATCH_SIZE,))
        batch_rows = cur.fetchall()

        if not batch_rows:
            break

        batch_idx += 1
        t_batch_start = time.time()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(embed_worker, (r[0], r[1], r[2])) for r in batch_rows]
            batch_results = [f.result() for f in as_completed(futures)]

        success_in_batch = 0
        for cid, src, vec, err in batch_results:
            if vec and len(vec) == 3072:
                vec_json = json.dumps(vec)
                cur.execute("UPDATE duque_ia_chunks SET embedding = ? WHERE id = ?", (vec_json, cid))
                
                # Se existe na tabela chunks, atualiza o vetor binário
                blob = struct.pack(f"{len(vec)}f", *vec)
                cur.execute("UPDATE chunks SET vetor_blob = ? WHERE id = ?", (blob, src))
                success_in_batch += 1
            else:
                print(f"  [AVISO] Falha no chunk ID={cid} (src={src}): {err}")

        conn.commit()
        processed_count += success_in_batch

        elapsed_batch = time.time() - t_batch_start
        elapsed_total = time.time() - start_total
        pct = (processed_count / total_pending) * 100
        avg_per_item = elapsed_total / processed_count if processed_count > 0 else 1.0
        eta_sec = (total_pending - processed_count) * avg_per_item
        eta_min = eta_sec / 60

        print(
            f"[Lote {batch_idx:02d}] Progresso: {processed_count}/{total_pending} ({pct:.1f}%) | "
            f"Lote: {elapsed_batch:.1f}s | Méd: {avg_per_item:.2f}s/chunk | ETA: {eta_min:.1f} min"
        )

        # Pausa preventiva entre lotes para respeitar rate limits da API
        time.sleep(0.15)

    conn.close()

    total_time = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"VETORIZAÇÃO CONCLUÍDA COM SUCESSO EM {total_time/60:.2f} MINUTOS!")
    print(f"Total de chunks vetorizados: {processed_count}")
    print("=" * 70)

if __name__ == "__main__":
    vectorize_all()
