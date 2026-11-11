"""
scripts/ingest_escolas_municipais.py
====================================
Ingestão incremental das 205 escolas municipais e CIEPs de Duque de Caxias.
Atualiza main.db (tabela escolas_municipais) e vector.db (chunks, chunks_fts, duque_ia_chunks).
"""

import os
import sys
import csv
import json
import sqlite3
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import DATABASE_MAIN, DATABASE_VECTOR

CSV_PATH = r"C:\Users\501379.PMDC\Desktop\PROJETOS\web scraping\educação\escolas_duque_de_caxias.csv"

def ingest():
    print(f"Lendo escolas de: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        print("Erro: CSV não encontrado!")
        return

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)

    print(f"Total de escolas lidas no CSV: {len(rows)}")

    # 1. Ingestão no main.db
    with sqlite3.connect(DATABASE_MAIN, timeout=10.0) as conn_main:
        conn_main.execute("PRAGMA journal_mode=WAL;")
        conn_main.execute("""
            CREATE TABLE IF NOT EXISTS escolas_municipais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_inep TEXT UNIQUE,
                nome TEXT NOT NULL,
                distrito TEXT,
                endereco TEXT,
                bairro TEXT,
                cep TEXT,
                telefone TEXT,
                email TEXT,
                diretor TEXT,
                url_oficial TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn_main.execute("CREATE INDEX IF NOT EXISTS idx_escolas_nome ON escolas_municipais(nome);")
        conn_main.execute("CREATE INDEX IF NOT EXISTS idx_escolas_bairro ON escolas_municipais(bairro);")

        inserted_main = 0
        for r in rows:
            # Limpa chave com BOM se houver
            code = r.get("\ufeffcodigo_escola") or r.get("codigo_escola", "")
            nome = r.get("nome_escola", "").strip()
            distrito = r.get("distrito", "").strip()
            endereco = r.get("endereco", "").strip()
            bairro = r.get("bairro", "").strip()
            cep = r.get("cep", "").strip()
            telefone = r.get("telefones", "").strip()
            email = r.get("email", "").strip()
            diretor = r.get("diretor", "").strip()
            url = r.get("url", "").strip()

            conn_main.execute("""
                INSERT INTO escolas_municipais 
                (codigo_inep, nome, distrito, endereco, bairro, cep, telefone, email, diretor, url_oficial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(codigo_inep) DO UPDATE SET
                    nome=excluded.nome,
                    distrito=excluded.distrito,
                    endereco=excluded.endereco,
                    bairro=excluded.bairro,
                    cep=excluded.cep,
                    telefone=excluded.telefone,
                    email=excluded.email,
                    diretor=excluded.diretor,
                    url_oficial=excluded.url_oficial
            """, (code, nome, distrito, endereco, bairro, cep, telefone, email, diretor, url))
            inserted_main += 1

        conn_main.commit()
    print(f"✓ main.db: {inserted_main} escolas salvas na tabela 'escolas_municipais'.")

    # 2. Ingestão no vector.db
    with sqlite3.connect(DATABASE_VECTOR, timeout=10.0) as conn_vec:
        conn_vec.execute("PRAGMA journal_mode=WAL;")
        cur_v = conn_vec.cursor()

        inserted_chunks = 0
        inserted_duque = 0

        for r in rows:
            code = r.get("\ufeffcodigo_escola") or r.get("codigo_escola", "")
            nome = r.get("nome_escola", "").strip()
            distrito = r.get("distrito", "").strip()
            endereco = r.get("endereco", "").strip()
            bairro = r.get("bairro", "").strip()
            cep = r.get("cep", "").strip()
            telefone = r.get("telefones", "").strip()
            email = r.get("email", "").strip()
            diretor = r.get("diretor", "").strip()
            url = r.get("url", "").strip()

            chunk_id = f"escola_{code}"
            tipo = "EDUCACAO"
            titulo = f"Escola Municipal: {nome} - Bairro {bairro}"
            conteudo = (
                f"# {nome}\n"
                f"- **Tipo de Unidade**: Unidade Escolar Municipal / Rede Pública de Ensino\n"
                f"- **Distrito**: {distrito}\n"
                f"- **Bairro**: {bairro}\n"
                f"- **Endereço**: {endereco} - CEP: {cep}\n"
                f"- **Telefone de Contato**: {telefone if telefone else 'Atendimento presencial na secretaria escolar'}\n"
                f"- **E-mail Institucional**: {email if email else 'educacao@duquedecaxias.rj.gov.br'}\n"
                f"- **Direção Escolar**: {diretor if diretor else 'Equipe Diretiva Municipal'}\n"
                f"- **Órgão Gestor**: Secretaria Municipal de Educação (SME) de Duque de Caxias\n"
                f"- **Consulta no Sistema Educacional**: {url}"
            )
            metadata = {
                "source": "escolas_duque_de_caxias.csv",
                "category": "educacao",
                "inep": code,
                "distrito": distrito,
                "bairro": bairro,
                "secretaria": "SME"
            }
            meta_json = json.dumps(metadata, ensure_ascii=False)

            # Inserção incremental em chunks
            cur_v.execute("""
                INSERT OR REPLACE INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
                VALUES (?, ?, ?, ?, ?, NULL)
            """, (chunk_id, tipo, titulo, conteudo, meta_json))
            inserted_chunks += 1

            # Inserção incremental em chunks_fts
            # Remove se já existia no FTS para evitar duplicações
            cur_v.execute("DELETE FROM chunks_fts WHERE id = ?", (chunk_id,))
            cur_v.execute("""
                INSERT INTO chunks_fts (id, titulo, conteudo, tipo)
                VALUES (?, ?, ?, ?)
            """, (chunk_id, titulo, conteudo, tipo))

            # Inserção incremental em duque_ia_chunks (com verificação de duplicação por chave source+inep)
            duque_key = f"escola_{code}"
            keywords_str = f"escola, ciep, educacao, colegio, ensino, {bairro.lower()}, {nome.lower()}, caxias"
            cur_v.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (duque_key,))
            cur_v.execute("""
                INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
                VALUES (?, 'educacao', ?, '[]', ?, ?)
            """, (duque_key, conteudo, meta_json, keywords_str))
            inserted_duque += 1

        conn_vec.commit()
    print(f"✓ vector.db: {inserted_chunks} chunks inseridos em 'chunks' e 'chunks_fts'.")
    print(f"✓ vector.db: {inserted_duque} registros inseridos em 'duque_ia_chunks'.")

if __name__ == "__main__":
    ingest()
