import sqlite3
import os
import glob

def find_databases():
    db_files = glob.glob("**/*.db", recursive=True)
    print("Arquivos .db encontrados:", db_files)
    for db_path in db_files:
        print(f"\n==========================================")
        print(f"Banco: {db_path}")
        print(f"==========================================")
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cur.fetchall()]
            print("Tabelas:", tables)
            for t in tables:
                cur.execute(f"SELECT count(*) FROM {t};")
                count = cur.fetchone()[0]
                print(f"  - Tabela '{t}': {count} registros")
        except Exception as e:
            print(f"Erro ao ler {db_path}: {e}")

if __name__ == "__main__":
    find_databases()
