import sqlite3

conn = sqlite3.connect("data/db/vector.db")
print("SQL chunks_fts:")
row = conn.execute("SELECT sql FROM sqlite_master WHERE name='chunks_fts'").fetchone()
print(row[0] if row else "None")

triggers = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall()
print("\nTRIGGERS em vector.db:")
for t in triggers:
    print(t[0], "->", t[1])

