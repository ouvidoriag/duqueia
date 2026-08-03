import sqlite3
import json

db_main = 'data/db/main.db'
db_vec = 'data/db/vector.db'

print('=== 1. TABELAS E VIEWS EM main.db ===')
conn = sqlite3.connect(db_main)
cur = conn.cursor()
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')")
for name, ttype in cur.fetchall():
    print(f"  [{ttype.upper()}] {name}")

print('\n=== 2. CONTEÚDO DE secretaria_unidades em main.db ===')
try:
    cur.execute("SELECT * FROM secretaria_unidades")
    rows = cur.fetchall()
    print(f"Total em secretaria_unidades: {len(rows)}")
    for r in rows:
        print(" ", r)
except Exception as e:
    print(" Erro em secretaria_unidades:", e)

print('\n=== 3. BUSCA POR CRAS ou JARDIM PRIMAVERA em secretarias / serviços ===')
try:
    cur.execute("SELECT id, name, code, address, phone FROM secretarias WHERE LOWER(name) LIKE '%assist%') OR LOWER(address) LIKE '%jardim primavera%'")
    for r in cur.fetchall():
        print("  [secretaria]", r)
except Exception as e:
    print(" Erro em secretarias:", e)

try:
    cur.execute("SELECT servico_id, secretaria_nome, servico_nome, descricao FROM vw_ia_servicos WHERE LOWER(servico_nome) LIKE '%cras%' OR LOWER(descricao) LIKE '%cras%' OR LOWER(servico_nome) LIKE '%assist%'")
    rows = cur.fetchall()
    print(f"\nTotal em vw_ia_servicos: {len(rows)}")
    for r in rows:
        print("  [servico]", r[0], "|", r[1], "|", r[2])
except Exception as e:
    print(" Erro em vw_ia_servicos:", e)

print('\n=== 4. BUSCA POR CRAS ou JARDIM PRIMAVERA em vector.db (duque_ia_chunks) ===')
conn_v = sqlite3.connect(db_vec)
cur_v = conn_v.cursor()
try:
    cur_v.execute("SELECT id, source, category, content FROM duque_ia_chunks WHERE LOWER(content) LIKE '%cras%' OR LOWER(content) LIKE '%jardim primavera%'")
    rows_v = cur_v.fetchall()
    print(f"Total de chunks no vector.db com CRAS ou Jardim Primavera: {len(rows_v)}")
    for r in rows_v:
        print(f"\n  [ID {r[0]} | Source: {r[1]} | Cat: {r[2]}]\n  {r[3][:300]}...")
except Exception as e:
    print(" Erro em vector.db:", e)
