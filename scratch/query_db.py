import os
import sys
import sqlite3

# Set up project path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from config.settings import DATABASE_MAIN

conn = sqlite3.connect(DATABASE_MAIN)
cursor = conn.cursor()

# Search for services matching gravidez
cursor.execute("""
    SELECT servico_id, secretaria_nome, servico_nome, descricao, como_acessar 
    FROM vw_ia_servicos 
    WHERE servico_nome LIKE '%gravidez%' OR descricao LIKE '%gravidez%'
""")
rows = cursor.fetchall()
print("--- vw_ia_servicos matching '%gravidez%' ---")
for r in rows:
    print(f"ID: {r[0]} | Sec: {r[1]} | Name: {r[2]}")
    print(f"Desc: {r[3]}")
    print(f"How: {r[4]}")
    print("-" * 50)
    
    # Query additional details
    s_id = r[0]
    cursor.execute("SELECT phone FROM service_phones WHERE service_id = ?", (s_id,))
    print(f"Phones: {[x[0] for x in cursor.fetchall()]}")
    cursor.execute("SELECT email FROM service_emails WHERE service_id = ?", (s_id,))
    print(f"Emails: {[x[0] for x in cursor.fetchall()]}")
    cursor.execute("SELECT link FROM service_links WHERE service_id = ?", (s_id,))
    print(f"Links: {[x[0] for x in cursor.fetchall()]}")
    cursor.execute("SELECT document_name FROM service_documents WHERE service_id = ?", (s_id,))
    print(f"Docs: {[x[0] for x in cursor.fetchall()]}")
    cursor.execute("SELECT step_number, description FROM service_steps WHERE service_id = ? ORDER BY step_number", (s_id,))
    print(f"Steps: {[f'{x[0]}: {x[1]}' for x in cursor.fetchall()]}")
    print("=" * 60)

conn.close()
