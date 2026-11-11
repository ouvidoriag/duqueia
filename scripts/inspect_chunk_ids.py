import sqlite3

conn = sqlite3.connect("data/db/vector.db")
rows = conn.execute("SELECT id, tipo, titulo FROM chunks ORDER BY id DESC LIMIT 10").fetchall()
for r in rows:
    print(r)

