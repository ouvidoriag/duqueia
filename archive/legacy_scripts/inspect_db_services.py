import sqlite3

def inspect_services():
    conn = sqlite3.connect("data/db/main.db")
    cur = conn.cursor()
    
    cur.execute("PRAGMA table_info(services);")
    cols = [c[1] for c in cur.fetchall()]
    print("Colunas de 'services':", cols)
    
    cur.execute("SELECT id, name, description, how_to_access, who_can_request, waiting_time, max_deadline, cost, regulation_norm FROM services LIMIT 5;")
    rows = cur.fetchall()
    print("\nExemplo de 5 serviços em 'services':")
    for r in rows:
        print(f"\nID {r[0]}: {r[1]}")
        print("  Descrição:", r[2])
        print("  Como acessar:", r[3])
        print("  Público:", r[4])
        print("  Tempo espera:", r[5])
        print("  Prazo máx:", r[6])
        print("  Custo:", r[7])
        print("  Norma:", r[8])

    print("\nProcurando por 'Fiscalização', 'Limpeza', 'Terreno' em 'services':")
    cur.execute("SELECT id, name, description, how_to_access, who_can_request, waiting_time, max_deadline, cost, regulation_norm FROM services WHERE name LIKE '%Fiscaliz%' OR name LIKE '%Limpeza%' OR name LIKE '%Terreno%' OR description LIKE '%terreno%' OR description LIKE '%abandonado%';")
    f_rows = cur.fetchall()
    print(f"\nTotal encontrados: {len(f_rows)}")
    for fr in f_rows:
        print(f"\nID {fr[0]}: {fr[1]}")
        print("  Desc:", fr[2])
        print("  Como acessar:", fr[3])
        print("  Quem pode solicitar:", fr[4])
        print("  Tempo espera:", fr[5])
        print("  Prazo máx:", fr[6])
        print("  Custo:", fr[7])
        print("  Norma:", fr[8])

if __name__ == "__main__":
    inspect_services()
