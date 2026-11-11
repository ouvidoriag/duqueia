import sqlite3
import re
import os
import sys

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "db", "vector.db")

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Remove marcação OCR óptico
    t = re.sub(r'\s*\*?\(OCR[^\)]*\)\*?', '', text, flags=re.IGNORECASE)
    t = re.sub(r'###\s*Página\s*\d+\s*\*?\(OCR[^\)]*\)\*?', '', t, flags=re.IGNORECASE)
    # Remove prefixo numérico de arquivo (ex: 01_, 07_) e underscores
    t = re.sub(r'\b\d{2}_([A-Za-z0-9_]+)', lambda m: m.group(1).replace('_', ' '), t)
    return t.strip()

def run_cleaning():
    print(f"Connecting to {_DB_PATH}...")
    conn = sqlite3.connect(_DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT id, titulo, conteudo FROM chunks WHERE titulo LIKE ? OR conteudo LIKE ?", ('%OCR%', '%OCR%'))
    rows = cur.fetchall()
    print(f"Found {len(rows)} chunks in 'chunks' containing 'OCR'.")
    
    updated_count = 0
    for cid, tit, cont in rows:
        new_tit = clean_text(tit)
        new_cont = clean_text(cont)
        cur.execute("UPDATE chunks SET titulo = ?, conteudo = ? WHERE id = ?", (new_tit, new_cont, cid))
        # Atualiza chunks_fts se existir
        try:
            cur.execute("UPDATE chunks_fts SET titulo = ?, conteudo = ? WHERE id = ?", (new_tit, new_cont, cid))
        except Exception:
            pass
        updated_count += 1

    conn.commit()
    print(f"Successfully cleaned {updated_count} chunks in 'chunks'.")
    
    # Verifica duque_ia_chunks também
    cur.execute("SELECT source, content, metadata FROM duque_ia_chunks WHERE content LIKE ? OR metadata LIKE ?", ('%OCR%', '%OCR%'))
    d_rows = cur.fetchall()
    print(f"Found {len(d_rows)} rows in 'duque_ia_chunks' with 'OCR'.")
    for src, cont, meta in d_rows:
        new_cont = clean_text(cont)
        new_meta = clean_text(meta)
        cur.execute("UPDATE duque_ia_chunks SET content = ?, metadata = ? WHERE source = ?", (new_cont, new_meta, src))
    
    conn.commit()
    conn.close()
    print("Clean-up finished successfully!")

if __name__ == "__main__":
    run_cleaning()
