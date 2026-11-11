"""
scripts/ingest_editais_transparencia.py
======================================
Ingestão incremental dos Editais PSS 2026 e do Catálogo das 59 APIs da Transparência.
Atualiza data/knowledge/ e vector.db (chunks, chunks_fts, duque_ia_chunks).
"""

import os
import sys
import shutil
import json
import sqlite3
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import DATABASE_VECTOR

EDITAIS_DIR = r"C:\Users\501379.PMDC\Desktop\PROJETOS\Transparencia\concursos_editais\md_2026"
CATALOGO_APIS_PATH = r"C:\Users\501379.PMDC\Desktop\PROJETOS\Transparencia\CATALOGO_COMPLETO_59_APIS.md"

DEST_EDITAIS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "concursos_editais_2026"))
DEST_TRANSPARENCIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "transparencia"))

def ingest_editais():
    print(f"\n1. Copiando editais de {EDITAIS_DIR} para {DEST_EDITAIS_DIR}...")
    os.makedirs(DEST_EDITAIS_DIR, exist_ok=True)
    os.makedirs(DEST_TRANSPARENCIA_DIR, exist_ok=True)

    files = [f for f in os.listdir(EDITAIS_DIR) if f.endswith(".md")]
    print(f"Total de editais encontrados: {len(files)}")

    for f in files:
        src = os.path.join(EDITAIS_DIR, f)
        dst = os.path.join(DEST_EDITAIS_DIR, f)
        shutil.copy2(src, dst)
    print(f"✓ {len(files)} arquivos de editais copiados para data/knowledge/concursos_editais_2026/")

    # Copia o catálogo das 59 APIs
    dest_cat_apis = os.path.join(DEST_TRANSPARENCIA_DIR, "catalogo_59_apis.md")
    shutil.copy2(CATALOGO_APIS_PATH, dest_cat_apis)
    print(f"✓ Catálogo das 59 APIs copiado para {dest_cat_apis}")

    # 2. Ingestão no vector.db
    with sqlite3.connect(DATABASE_VECTOR, timeout=10.0) as conn_vec:
        conn_vec.execute("PRAGMA journal_mode=WAL;")
        cur_v = conn_vec.cursor()

        chunks_inserted = 0

        for f in files:
            file_path = os.path.join(DEST_EDITAIS_DIR, f)
            with open(file_path, "r", encoding="utf-8") as ed_f:
                content = ed_f.read()

            # Extrai título e metadados
            lines = content.splitlines()
            title = lines[0].replace("#", "").strip() if lines else f"Edital PSS 2026 - {f}"
            
            # Extrai código do edital
            code_match = re.search(r"Código do Edital:\*\*\s*(\d+)", content)
            edital_code = code_match.group(1) if code_match else f.split("_")[1]

            # Pega o resumo (primeiros 1500 caracteres com metadados principais)
            resumo_linhas = []
            for line in lines[:40]:
                resumo_linhas.append(line)
            resumo_text = "\n".join(resumo_linhas)

            chunk_id = f"edital_2026_{edital_code}"
            tipo = "CONCURSOS"
            titulo = f"Edital Concurso/PSS 2026: {title}"
            
            # Conteúdo estruturado para RAG factual
            chunk_content = (
                f"{resumo_text}\n\n"
                f"### Informações Oficiais para o Cidadão\n"
                f"- Para consultar o texto integral deste edital e seus anexos, acesse o Portal da Transparência de Duque de Caxias.\n"
                f"- Fonte Oficial: Ouvidoria Geral / Portal da Transparência Municipal (Ano: 2026)."
            )

            metadata = {
                "source": f"concursos_editais_2026/{f}",
                "category": "concursos",
                "ano": 2026,
                "edital_code": edital_code,
                "secretaria": "SMA"
            }
            meta_json = json.dumps(metadata, ensure_ascii=False)

            cur_v.execute("""
                INSERT OR REPLACE INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
                VALUES (?, ?, ?, ?, ?, NULL)
            """, (chunk_id, tipo, titulo, chunk_content, meta_json))

            cur_v.execute("DELETE FROM chunks_fts WHERE id = ?", (chunk_id,))
            cur_v.execute("""
                INSERT INTO chunks_fts (id, titulo, conteudo, tipo)
                VALUES (?, ?, ?, ?)
            """, (chunk_id, titulo, chunk_content, tipo))

            duque_key = f"edital_2026_{edital_code}"
            keywords_str = f"concurso, pss, selecao, vaga, emprego, edital {edital_code}, transparencia, 2026, caxias"
            cur_v.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (duque_key,))
            cur_v.execute("""
                INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
                VALUES (?, 'concursos', ?, '[]', ?, ?)
            """, (duque_key, chunk_content, meta_json, keywords_str))

            chunks_inserted += 1

        # 3. Ingestão do Catálogo das 59 APIs
        with open(dest_cat_apis, "r", encoding="utf-8") as cat_f:
            cat_content = cat_f.read()

        cat_id = "transparencia_catalogo_59_apis"
        cat_tipo = "TRANSPARENCIA"
        cat_titulo = "Portal da Transparência: Catálogo das 59 APIs Oficiais de Duque de Caxias"
        cat_meta = json.dumps({"source": "catalogo_59_apis.md", "category": "transparencia"}, ensure_ascii=False)

        cur_v.execute("""
            INSERT OR REPLACE INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (cat_id, cat_tipo, cat_titulo, cat_content, cat_meta))

        cur_v.execute("DELETE FROM chunks_fts WHERE id = ?", (cat_id,))
        cur_v.execute("""
            INSERT INTO chunks_fts (id, titulo, conteudo, tipo)
            VALUES (?, ?, ?, ?)
        """, (cat_id, cat_titulo, cat_content, cat_tipo))

        cur_v.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (cat_id,))
        cur_v.execute("""
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, 'transparencia', ?, '[]', ?, ?)
        """, (cat_id, cat_content, cat_meta, "transparencia, api, despesas, receitas, contratos, licitacao, concurso, salarios, caxias"))

        conn_vec.commit()
    print(f"✓ vector.db: {chunks_inserted} editais + 1 catálogo de APIs ingeridos com sucesso no FTS5 e duque_ia_chunks!")

if __name__ == "__main__":
    ingest_editais()

