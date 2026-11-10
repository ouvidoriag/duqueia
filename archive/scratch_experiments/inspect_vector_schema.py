import sqlite3

conn = sqlite3.connect("data/db/vector.db")
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table';")
for row in cur.fetchall():
    print(row[0])
    print("-" * 50)
conn.close()
