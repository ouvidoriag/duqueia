import sqlite3, json

conn = sqlite3.connect("data/db/duque_ia.db")
c = conn.cursor()

# Verifica a dimensão real dos embeddings no banco
c.execute("SELECT embedding FROM duque_ia_chunks LIMIT 1")
row = c.fetchone()
if row:
    emb = json.loads(row[0])
    real_dim = len(emb)
    print(f"Dimensão real dos embeddings no banco: {real_dim}")
    
    # Atualiza a tabela de metadata para refletir o modelo real
    c.execute("UPDATE embedding_metadata SET model=?, dimension=? WHERE model='text-embedding-004'",
              ("gemini-embedding-2", real_dim))
    conn.commit()
    print("Metadata de embedding atualizada com sucesso!")
    
    c.execute("SELECT * FROM embedding_metadata")
    rows = c.fetchall()
    for r in rows:
        print(f"  provider={r[0]}, model={r[1]}, dimension={r[2]}")
else:
    print("Banco vazio!")

conn.close()
