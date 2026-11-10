import sqlite3
import os

db_paths = ["data/db/main.db", "data/db/vector.db"]

for db_path in db_paths:
    print(f"\n================ CHECKING {db_path} ================")
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables/Views in DB:", tables)

    # Search for saxofone in all text columns
    for t in tables:
        try:
            cur.execute(f"SELECT * FROM {t} WHERE 1=0;")
            cols = [d[0] for d in cur.description]
            text_cols = [c for c in cols if 'id' not in c.lower()]
            if text_cols:
                where_clause = " OR ".join([f"LOWER({c}) LIKE '%saxofone%'" for c in text_cols])
                query = f"SELECT * FROM {t} WHERE {where_clause};"
                cur.execute(query)
                rows = cur.fetchall()
                if rows:
                    print(f"\n[MATCH IN {t}] Found {len(rows)} rows:")
                    for row in rows[:5]:
                        print("  -", row)
                else:
                    print(f"No match for 'saxofone' in {t}")
        except Exception as e:
            print(f"Error checking {t}: {e}")

    conn.close()
