# -*- coding: utf-8 -*-
"""
Script de Ingestão Incremental do acervo Desktop/enderecos para main.db.
Importa:
1. Todos os 105 Bairros oficiais dos 4 Distritos de Duque de Caxias em 'bairros_distritos'.
2. Os 400 Endereços Georreferenciados com Latitude, Longitude, CEP e Logradouro em 'logradouros_enderecos'.
"""

import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DB = r"c:\Users\501379.PMDC\Desktop\enderecos\dados\enderecos_duque_de_caxias_v2.db"
DEST_DB = os.path.join(BASE_DIR, "data", "db", "main.db")

def main():
    print("=== INICIANDO INGESTAO DESKTOP/ENDERECOS -> MAIN.DB ===")
    if not os.path.exists(SRC_DB):
        print(f"[ERRO] Banco de enderecos nao encontrado em: {SRC_DB}")
        return

    src_conn = sqlite3.connect(SRC_DB)
    src_cur = src_conn.cursor()

    dest_conn = sqlite3.connect(DEST_DB)
    dest_cur = dest_conn.cursor()

    # 1. Cria tabela logradouros_enderecos em main.db se nao existir
    dest_cur.execute("""
    CREATE TABLE IF NOT EXISTS logradouros_enderecos (
        id INTEGER PRIMARY KEY,
        bairro_id INTEGER,
        bairro_nome TEXT,
        distrito_nome TEXT,
        logradouro TEXT NOT NULL,
        numero TEXT,
        complemento TEXT,
        cep TEXT,
        latitude REAL,
        longitude REAL,
        precisao_geo TEXT
    );
    """)

    # 2. Ingestao de todos os 105 bairros de enderecos_v2
    src_cur.execute("""
    SELECT b.id, b.nome, d.numero, d.nome, b.cep_padrao
    FROM bairros b
    JOIN distritos d ON b.distrito_id = d.id
    """)
    bairros_rows = src_cur.fetchall()
    bairros_ingested = 0
    for b_id, b_nome, d_num, d_nome, cep in bairros_rows:
        bid_str = f"bairro-{b_id}"
        dest_cur.execute("""
            INSERT INTO bairros_distritos (id, nome, distrito, distrito_nome, regiao, aliases)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nome = excluded.nome,
                distrito = excluded.distrito,
                distrito_nome = excluded.distrito_nome
        """, (bid_str, b_nome, d_num, d_nome, f"CEP: {cep}", f"[\"{b_nome}\"]"))
        bairros_ingested += 1

    # 3. Ingestao dos 400 enderecos georreferenciados
    src_cur.execute("""
    SELECT e.id, e.bairro_id, b.nome, d.nome, e.logradouro, e.numero, e.complemento, e.cep, e.latitude, e.longitude, e.precisao_geo
    FROM enderecos e
    LEFT JOIN bairros b ON e.bairro_id = b.id
    LEFT JOIN distritos d ON b.distrito_id = d.id
    """)
    end_rows = src_cur.fetchall()
    for r in end_rows:
        dest_cur.execute("""
            INSERT OR REPLACE INTO logradouros_enderecos (
                id, bairro_id, bairro_nome, distrito_nome, logradouro, numero, complemento, cep, latitude, longitude, precisao_geo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, r)

    dest_conn.commit()
    print(f"[OK] Ingestao de enderecos concluida: {bairros_ingested} bairros, {len(end_rows)} enderecos georreferenciados.")

    dest_cur.execute("SELECT count(*) FROM bairros_distritos")
    print(f"[OK] Total bairros_distritos em main.db: {dest_cur.fetchone()[0]}")
    dest_cur.execute("SELECT count(*) FROM logradouros_enderecos")
    print(f"[OK] Total logradouros_enderecos em main.db: {dest_cur.fetchone()[0]}")

    src_conn.close()
    dest_conn.close()
    print("=== INGESTAO DESKTOP/ENDERECOS CONCLUIDA COM SUCESSO ===")

if __name__ == "__main__":
    main()
