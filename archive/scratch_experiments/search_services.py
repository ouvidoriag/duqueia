import sqlite3

conn = sqlite3.connect("agent/duque_ia.db")
c = conn.cursor()

print("=== BUSCA NA TABELA SERVICES DE AGENT/DUQUE_IA.DB ===")
c.execute("SELECT id, name, secretaria_id FROM services")
rows = c.fetchall()
print(f"Total de serviços na tabela 'services': {len(rows)}")

tax_services = []
for r in rows:
    name = r[1]
    if any(k in name.lower() for k in ["isen", "ipi", "tax", "táxi", "deficien", "pcd", "matríc", "matric", "quebra"]):
        tax_services.append(r)

print(f"\nServiços encontrados relacionados a Isenção / Táxi / Matrícula / Quebra-mola: {len(tax_services)}")
for ts in tax_services:
    print(f"  - ID: {ts[0]} | Nome: {ts[1]}")
