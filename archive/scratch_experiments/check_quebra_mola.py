import sqlite3
import glob

print("=== VERIFICANDO TABELAS EM AGENT/DUQUE_IA.DB ===")
conn1 = sqlite3.connect("agent/duque_ia.db")
c1 = conn1.cursor()
tables1 = [t[0] for t in c1.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tabelas em duque_ia.db:", tables1)

for t in tables1:
    try:
        cols = [c[1] for c in c1.execute(f"PRAGMA table_info({t})").fetchall()]
        for col in cols:
            query = f"SELECT count(*) FROM {t} WHERE CAST({col} AS TEXT) LIKE '%quebra%' OR CAST({col} AS TEXT) LIKE '%lombada%' OR CAST({col} AS TEXT) LIKE '%redutor%'"
            try:
                res = c1.execute(query).fetchone()[0]
                if res > 0:
                    print(f"  [ACHOU!] Tabela '{t}' | Coluna '{col}': {res} registros")
            except Exception:
                pass
    except Exception as e:
        print(f"Erro ao verificar tabela {t}: {e}")

print("\n=== VERIFICANDO TABELAS EM DATABASE/VECTOR.DB ===")
conn2 = sqlite3.connect("database/vector.db")
c2 = conn2.cursor()
tables2 = [t[0] for t in c2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tabelas em vector.db:", tables2)

for t in tables2:
    try:
        cols = [c[1] for c in c2.execute(f"PRAGMA table_info({t})").fetchall()]
        for col in cols:
            query = f"SELECT count(*) FROM {t} WHERE CAST({col} AS TEXT) LIKE '%quebra%' OR CAST({col} AS TEXT) LIKE '%lombada%' OR CAST({col} AS TEXT) LIKE '%redutor%'"
            try:
                res = c2.execute(query).fetchone()[0]
                if res > 0:
                    print(f"  [ACHOU!] Tabela '{t}' | Coluna '{col}': {res} registros")
                    # Imprime os detalhes
                    details = c2.execute(f"SELECT * FROM {t} WHERE CAST({col} AS TEXT) LIKE '%quebra%' OR CAST({col} AS TEXT) LIKE '%lombada%' OR CAST({col} AS TEXT) LIKE '%redutor%' LIMIT 5").fetchall()
                    for d in details:
                        print("    -> Detalhes:", d)
            except Exception:
                pass
    except Exception as e:
        print(f"Erro ao verificar tabela {t}: {e}")

print("\n=== BUSCA EM DATA/PROCESSED/ ===")
json_files = glob.glob("data/processed/**/*.json", recursive=True) + glob.glob("data/processed/*.json")
for jf in json_files:
    try:
        with open(jf, "r", encoding="utf-8") as f:
            txt = f.read()
            if any(k in txt.lower() for k in ["quebra-mola", "quebra mola", "lombada", "redutor de velocidade"]):
                print(f"  - Achou em arquivo: {jf}")
    except Exception:
        pass
