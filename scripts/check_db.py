import sqlite3, json

conn = sqlite3.connect('data/db/duque_ia.db')
c = conn.cursor()

# Lista todas as tabelas
c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
for tname, tsql in tables:
    print(f"\n=== TABLE: {tname} ===")
    print(tsql)

# Verifica totais
c.execute("SELECT COUNT(*) FROM duque_ia_chunks")
total = c.fetchone()[0]
print(f"\n\nTotal de chunks: {total}")

# Verifica um embedding para descobrir dimensão atual
c.execute("SELECT embedding FROM duque_ia_chunks LIMIT 1")
row = c.fetchone()
if row:
    emb = json.loads(row[0])
    print(f"Dimensão do embedding atual no banco: {len(emb)}")

conn.close()
