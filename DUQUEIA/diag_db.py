import sqlite3

conn = sqlite3.connect('agent/duque_ia.db')
cur = conn.cursor()

# Ver as tabelas/views
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name")
print('=== Tabelas e Views ===')
for r in cur.fetchall():
    print(f'  [{r[1]}] {r[0]}')

# Schema de vw_ia_servicos
print('\n=== Schema vw_ia_servicos (primeiras colunas) ===')
try:
    cur.execute("SELECT * FROM vw_ia_servicos LIMIT 1")
    cols = [d[0] for d in cur.description]
    print('  Colunas:', cols)
    row = cur.fetchone()
    if row:
        for col, val in zip(cols, row):
            print(f'  {col}: {str(val)[:120]}')
except Exception as e:
    print(f'  Erro: {e}')

# Buscar chunks de quebra molas
print('\n=== Chunks: quebra molas ===')
try:
    cur.execute("SELECT * FROM vw_ia_servicos WHERE content LIKE '%quebra%' LIMIT 3")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        for col, val in zip(cols, row):
            print(f'  {col}: {str(val)[:150]}')
        print('  ---')
except Exception as e:
    print(f'  Erro: {e}')

# Buscar chunks de IPTU
print('\n=== Chunks: IPTU ===')
try:
    cur.execute("SELECT * FROM vw_ia_servicos WHERE content LIKE '%IPTU%' OR content LIKE '%iptu%' LIMIT 3")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        for col, val in zip(cols, row):
            print(f'  {col}: {str(val)[:150]}')
        print('  ---')
except Exception as e:
    print(f'  Erro: {e}')

conn.close()
