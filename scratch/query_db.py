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

# Search for services matching Moradia/TRM
cursor.execute("""
    SELECT id, name, waiting_time, regulation_norm 
    FROM services 
    WHERE name LIKE '%Moradia%' OR description LIKE '%Moradia%' OR name LIKE '%TRM%'
""")
rows = cursor.fetchall()
print("--- services matching Moradia/TRM ---")
for r in rows:
    print(f"ID: {r[0]} | Name: {r[1]}")
    print(f"Waiting Time: {r[2]}")
    print(f"Regulation Norm: {r[3]}")
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
