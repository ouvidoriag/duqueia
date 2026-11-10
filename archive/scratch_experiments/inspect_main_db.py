import sqlite3
import os

db_path = "data/db/main.db"
print("DB Exists:", os.path.exists(db_path))

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type IN ('table', 'view');")
rows = cur.fetchall()
print(f"Total tables/views in {db_path}: {len(rows)}")
for r in rows:
    print(r[0])
    print("-" * 50)
conn.close()
