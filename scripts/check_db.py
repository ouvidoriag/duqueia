import os
import sys
import sqlite3
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config.settings import DATABASE_MAIN, DATABASE_VECTOR

def check_database(path, label):
    print(f"\n{'='*25} {label} ({path}) {'='*25}")
    if not os.path.exists(path):
        print("  Arquivo não encontrado!")
        return
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("PRAGMA integrity_check;")
    print(f"  Integrity check: {c.fetchone()[0]}")
    
    c.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY type, name")
    items = c.fetchall()
    for name, item_type in items:
        if name.startswith("sqlite_"):
            continue
        try:
            c.execute(f'SELECT COUNT(*) FROM "{name}"')
            count = c.fetchone()[0]
            print(f"  [{item_type.upper():5s}] {name:35s} : {count:6d} registros")
        except Exception as e:
            print(f"  [{item_type.upper():5s}] {name:35s} : ERRO ({e})")
    conn.close()

if __name__ == "__main__":
    check_database(DATABASE_MAIN, "MAIN DB (Estruturado)")
    check_database(DATABASE_VECTOR, "VECTOR DB (Vetorial)")
