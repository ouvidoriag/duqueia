"""
inject_ouvidoria_chunk.py
=========================
Injeta o chunk oficial da Ouvidoria Geral diretamente no banco SQLite.
Usa hash determinístico para embedding (modo offline) e insere incrementalmente.
"""
import io
import os
import sys
import sqlite3
import hashlib
import struct
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

DB_PATH = os.path.join(ROOT, "agent", "duque_ia.db")
MD_PATH = os.path.join(ROOT, "data", "knowledge", "ouvidoria_geral_info.md")

SOURCE   = "ouvidoria_geral_info.md"
CATEGORY = "ouvidoria"
STRATEGY = "recursive_500_100"

# ── Embedding determinístico (mesmo algoritmo usado offline) ────────────────
def deterministic_hash_embedding(text: str, dims: int = 3072) -> list[float]:
    vec = []
    seed = text.encode("utf-8")
    for i in range(dims):
        h = hashlib.sha256(seed + struct.pack("<I", i)).digest()
        val = (struct.unpack("<f", h[:4])[0] % 1.0)
        vec.append(round(val, 6))
    mag = sum(v * v for v in vec) ** 0.5 or 1.0
    return [round(v / mag, 6) for v in vec]

def chunk_text(text: str, size: int = 500, overlap: int = 100) -> list[str]:
    """Divide o texto em chunks com sobreposição."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk_words = words[i:i + size]
        chunks.append(" ".join(chunk_words))
        i += size - overlap
    return chunks

def already_exists(cursor, source: str) -> bool:
    cursor.execute("SELECT COUNT(*) FROM duque_ia_chunks WHERE source = ?", (source,))
    return cursor.fetchone()[0] > 0

def main():
    print(f"[Inject] Banco: {DB_PATH}")
    print(f"[Inject] Fonte: {MD_PATH}")

    if not os.path.exists(MD_PATH):
        print(f"[ERRO] Arquivo não encontrado: {MD_PATH}")
        sys.exit(1)

    with open(MD_PATH, "r", encoding="utf-8") as f:
        full_text = f.read()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verifica a estrutura da tabela
    cursor.execute("PRAGMA table_info(duque_ia_chunks)")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"[Inject] Colunas da tabela: {cols}")

    # Remove chunks anteriores da mesma fonte para reinjetar limpo
    cursor.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (SOURCE,))
    deleted = cursor.rowcount
    if deleted:
        print(f"[Inject] Removidos {deleted} chunks anteriores de '{SOURCE}'.")

    # Detecta dimensão de embedding no banco
    cursor.execute("SELECT embedding FROM duque_ia_chunks LIMIT 1")
    row = cursor.fetchone()
    dims = 768
    if row and row[0]:
        try:
            sample_vec = json.loads(row[0])
            dims = len(sample_vec)
        except Exception:
            pass
    print(f"[Inject] Dimensão do embedding detectada: {dims}")

    # Gera os chunks
    chunks = chunk_text(full_text, size=500, overlap=100)
    print(f"[Inject] Gerando {len(chunks)} chunk(s)...")

    # Detecta as colunas disponíveis para INSERT
    base_cols = ["source", "category", "content", "embedding", "chunk_strategy"]
    insert_cols = [c for c in base_cols if c in cols]

    inserted = 0
    for idx, chunk_content in enumerate(chunks):
        if not chunk_content.strip():
            continue

        vec = deterministic_hash_embedding(chunk_content, dims=dims)
        vec_json = json.dumps(vec)

        values = {
            "source": SOURCE,
            "category": CATEGORY,
            "content": chunk_content,
            "embedding": vec_json,
            "chunk_strategy": STRATEGY,
        }

        col_list = ", ".join(insert_cols)
        placeholders = ", ".join(["?" for _ in insert_cols])
        vals = tuple(values[c] for c in insert_cols)

        cursor.execute(
            f"INSERT INTO duque_ia_chunks ({col_list}) VALUES ({placeholders})",
            vals
        )
        inserted += 1
        print(f"  [Chunk {idx+1}/{len(chunks)}] {len(chunk_content)} chars inserido.")

    conn.commit()
    conn.close()
    print(f"\n[Inject] ✅ Concluído! {inserted} chunk(s) inserido(s) para '{SOURCE}'.")

if __name__ == "__main__":
    main()
