#!/usr/bin/env python3
"""
rebuild_db.py  —  Duque IA
Recria o banco de dados do zero a partir do schema_full.sql.
Execute este script para recriar o banco em qualquer máquina.

Uso:
    python rebuild_db.py [--output caminho/para/banco.db]
"""

import sqlite3
import argparse
import os

DEFAULT_DB = "duque_ia_rebuilt.db"

def rebuild(output_path: str):
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema", "schema_full.sql")
    
    if not os.path.exists(schema_path):
        print(f"ERRO: schema_full.sql não encontrado em {schema_path}")
        return

    if os.path.exists(output_path):
        resp = input(f"Arquivo '{output_path}' já existe. Sobrescrever? [s/N] ").strip().lower()
        if resp != "s":
            print("Operação cancelada.")
            return
        os.remove(output_path)

    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA foreign_keys = ON")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        conn.executescript(sql)
        conn.commit()
        print(f"✅ Banco recriado com sucesso em: {output_path}")
    except Exception as e:
        print(f"❌ Erro ao executar schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recria o banco SQLite do Duque IA do zero.")
    parser.add_argument("--output", default=DEFAULT_DB, help="Caminho do novo banco de dados")
    args = parser.parse_args()
    rebuild(args.output)
