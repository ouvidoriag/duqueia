import sqlite3
import os

dbs = ['data/db/main.db', 'data/db/vector.db', 'data/db/cache.db', 'data/db/telemetry.db']

def search_term(term):
    print(f"\n=======================================================")
    print(f"BUSCANDO TERMO: '{term}' NOS BANCOS DE DADOS")
    print(f"=======================================================")
    
    for db_path in dbs:
        if not os.path.exists(db_path):
            continue
        try:
            conn = sqlite3.connect(db_path)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            for t in tables:
                try:
                    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()]
                    for col in cols:
                        query = f"SELECT rowid, {col} FROM {t} WHERE CAST({col} AS TEXT) LIKE ? LIMIT 5"
                        rows = conn.execute(query, (f"%{term}%",)).fetchall()
                        if rows:
                            print(f"\n[+] {db_path} -> Tabela '{t}', Coluna '{col}' ({len(rows)} amostras):")
                            for r in rows:
                                val = str(r[1])[:150].replace('\n', ' ')
                                print(f"    rowid={r[0]}: {val}")
                except Exception as e:
                    pass
            conn.close()
        except Exception as e:
            print(f"Erro em {db_path}: {e}")

if __name__ == "__main__":
    search_term("netinho")
    search_term("reis")
    search_term("prefeito")
    search_term("wilson miguel")

