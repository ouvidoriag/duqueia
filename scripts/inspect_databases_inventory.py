import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for db_name in ['main.db', 'vector.db', 'cache.db', 'telemetry.db']:
    db_path = os.path.join('data', 'db', db_name)
    if not os.path.exists(db_path):
        print(f"{db_name}: NOT FOUND")
        continue
    size = os.path.getsize(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA integrity_check")
    integrity = c.fetchone()[0]
    c.execute("PRAGMA journal_mode")
    journal = c.fetchone()[0]
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in c.fetchall()]
    table_counts = {}
    for t in tables:
        try:
            c.execute(f'SELECT count(*) FROM "{t}"')
            table_counts[t] = c.fetchone()[0]
        except Exception as e:
            table_counts[t] = f"ERR: {e}"
    print(f"\n=== {db_name} ({size:,} bytes | WAL: {journal} | Integrity: {integrity}) ===")
    for t, cnt in sorted(table_counts.items()):
        print(f"  • {t}: {cnt} registros")
    conn.close()
