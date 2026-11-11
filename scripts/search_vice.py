import sqlite3

conn = sqlite3.connect("data/db/vector.db")
cur = conn.cursor()

print("--- CHUNKS matching 'vice' or 'aline' ---")
for r in cur.execute("SELECT id, tipo, titulo FROM chunks WHERE id LIKE '%vice%' OR titulo LIKE '%vice%' OR conteudo LIKE '%Aline%'").fetchall():
    print(r)

print("\n--- DUQUE_IA_CHUNKS matching 'vice' or 'aline' ---")
for r in cur.execute("SELECT id, tipo, titulo FROM duque_ia_chunks WHERE id LIKE '%vice%' OR titulo LIKE '%vice%' OR conteudo LIKE '%Aline%'").fetchall():
    print(r)

conn.close()

