import sqlite3

conn = sqlite3.connect("agent/duque_ia.db")
c = conn.cursor()
tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tabelas em agent/duque_ia.db:", tables)

for t in tables:
    count = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  - {t}: {count} linhas")
