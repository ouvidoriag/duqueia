import sqlite3
import glob

db_files = glob.glob('**/*.db', recursive=True)
for db_path in db_files:
    print('='*50)
    print(f'DB: {db_path}')
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"Total tabelas: {len(tables)}")
        for t in tables:
            try:
                cnt = c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                print(f"  - {t}: {cnt} linhas")
            except Exception as e:
                print(f"  - {t}: Erro ({e})")
    except Exception as e:
        print(f"Erro ao abrir {db_path}: {e}")
