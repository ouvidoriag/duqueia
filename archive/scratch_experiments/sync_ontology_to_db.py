import sqlite3
import json
import os

db_path = "data/db/main.db"
json_path = "data/ontology.json"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS municipal_entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT NOT NULL,
    keywords TEXT,
    secretaria TEXT,
    active INTEGER DEFAULT 1
);
""")

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        entities = json.load(f)

    for item in entities:
        cur.execute("""
            INSERT INTO municipal_entities (entity_id, entity_type, canonical_name, aliases, keywords, secretaria, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                entity_type=excluded.entity_type,
                canonical_name=excluded.canonical_name,
                aliases=excluded.aliases,
                keywords=excluded.keywords,
                secretaria=excluded.secretaria,
                active=excluded.active
        """, (
            item["entity_id"],
            item["entity_type"],
            item["canonical_name"],
            json.dumps(item.get("aliases", []), ensure_ascii=False),
            json.dumps(item.get("keywords", []), ensure_ascii=False),
            item.get("secretaria", ""),
            item.get("active", 1)
        ))

conn.commit()
print("Sincronização da Ontologia Municipal em data/db/main.db realizada com sucesso!")

cur.execute("SELECT entity_id, canonical_name, aliases FROM municipal_entities")
rows = cur.fetchall()
print(f"Total de entidades registradas em main.db: {len(rows)}")
for r in rows:
    print(f"  - [{r[0]}] {r[1]} -> Aliases: {r[2]}")
conn.close()
