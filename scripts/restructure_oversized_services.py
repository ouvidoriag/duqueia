# -*- coding: utf-8 -*-
"""
Reestruturação Semântica dos 52 Serviços Públicos Extensos (> 3.000 caracteres):
Divide cada serviço extenso em 2 partes semânticas naturais:
  - Parte 1: Identificação, Órgão, Descrição, Como Solicitar e Documentação Exigida.
  - Parte 2: Etapas / Passo a Passo do Atendimento, Prazos, Custos/Taxas e Legislação.
Preserva 100% do conteúdo (ZERO corte ou truncamento arbitrário) com prefixo contextual de vínculo.
"""

import os
import sys
import json
import sqlite3
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_VECTOR = os.path.join(BASE_DIR, "data", "db", "vector.db")

def split_service(cid, tit, cont, meta):
    # Encontra o ponto de divisão em ETAPAS
    match = re.search(r'\n(?=(?:ETAPAS(?:\s*/\s*PASSO A PASSO|\s*DO PROCESSO)?\s*:))', cont, re.IGNORECASE)
    if not match:
        match = re.search(r'\n(?=PASSO A PASSO\s*:)', cont, re.IGNORECASE)

    if not match:
        return None

    split_idx = match.start()
    part1_cont = cont[:split_idx].strip()
    part2_body = cont[split_idx:].strip()

    # Extrai o nome do serviço para cabeçalho de vínculo na Parte 2
    servico_nome = tit.replace("Serviço:", "").strip()

    part2_cont = f"SERVIÇO MUNICIPAL (Continuação - Etapas e Prazos): {servico_nome}\n{part2_body}"

    tags = meta.get("tags", [])

    chunk_part1 = {
        "id": f"{cid}_p1",
        "tipo": "SERVICO_PUBLICO",
        "titulo": f"{tit} — Parte 1: Descrição e Documentação",
        "conteudo": part1_cont,
        "metadata": {
            **meta,
            "title": f"{tit} — Parte 1: Descrição e Documentação",
            "parent_id": cid,
            "part": 1,
            "total_parts": 2,
            "tags": tags + ["documentos", "requisitos", "como solicitar"]
        }
    }

    chunk_part2 = {
        "id": f"{cid}_p2",
        "tipo": "SERVICO_PUBLICO",
        "titulo": f"{tit} — Parte 2: Etapas, Prazos e Taxas",
        "conteudo": part2_cont,
        "metadata": {
            **meta,
            "title": f"{tit} — Parte 2: Etapas, Prazos e Taxas",
            "parent_id": cid,
            "part": 2,
            "total_parts": 2,
            "tags": tags + ["etapas", "passo a passo", "prazo", "custo", "taxas"]
        }
    }

    return chunk_part1, chunk_part2

def test_split():
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, titulo, length(conteudo), conteudo, metadata_json
        FROM chunks
        WHERE tipo = 'SERVICO_PUBLICO' AND length(conteudo) > 3000
    """)
    rows = cur.fetchall()

    print(f"Total de serviços > 3000 chars: {len(rows)}")
    success = 0
    lens_p1 = []
    lens_p2 = []

    for cid, tit, clen, cont, meta_str in rows:
        try:
            meta = json.loads(meta_str) if meta_str else {}
        except Exception:
            meta = {}

        res = split_service(cid, tit, cont, meta)
        if res:
            p1, p2 = res
            success += 1
            lens_p1.append(len(p1["conteudo"]))
            lens_p2.append(len(p2["conteudo"]))
        else:
            print(f"[ALERTA] Falha ao encontrar marcador em: {cid} ({tit})")

    print(f"\nServiços divididos com sucesso: {success} / {len(rows)}")
    print(f"Parte 1 (Docs & Requisitos): Média = {sum(lens_p1)/len(lens_p1):.1f} chars | Max = {max(lens_p1)} chars | Min = {min(lens_p1)} chars")
    print(f"Parte 2 (Etapas & Prazos)  : Média = {sum(lens_p2)/len(lens_p2):.1f} chars | Max = {max(lens_p2)} chars | Min = {min(lens_p2)} chars")

    conn.close()

def apply_split():
    print("=== APLICANDO SUBDIVISÃO DOS 52 SERVIÇOS PÚBLICOS EXTENSOS ===")
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, titulo, length(conteudo), conteudo, metadata_json
        FROM chunks
        WHERE tipo = 'SERVICO_PUBLICO' AND length(conteudo) > 3000
    """)
    rows = cur.fetchall()
    print(f"[*] Serviços a subdividir: {len(rows)}")

    inserted_parts = 0
    deleted_parents = 0

    for cid, tit, clen, cont, meta_str in rows:
        try:
            meta = json.loads(meta_str) if meta_str else {}
        except Exception:
            meta = {}

        res = split_service(cid, tit, cont, meta)
        if not res:
            continue

        p1, p2 = res

        # 1. Deleta o registro pai monolítico das 3 tabelas
        cur.execute("DELETE FROM chunks WHERE id = ?", (cid,))
        cur.execute("DELETE FROM chunks_fts WHERE id = ?", (cid,))
        cur.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (cid,))
        deleted_parents += 1

        # 2. Insere Parte 1 e Parte 2
        for part in [p1, p2]:
            pid = part["id"]
            tipo = part["tipo"]
            ptit = part["titulo"]
            pcont = part["conteudo"]
            pmeta_str = json.dumps(part["metadata"], ensure_ascii=False)
            ptags_str = json.dumps(part["metadata"]["tags"], ensure_ascii=False)

            # Tabela chunks
            cur.execute("""
                INSERT OR REPLACE INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
                VALUES (?, ?, ?, ?, ?, NULL)
            """, (pid, tipo, ptit, pcont, pmeta_str))

            # Tabela chunks_fts
            cur.execute("DELETE FROM chunks_fts WHERE id = ?", (pid,))
            cur.execute("""
                INSERT INTO chunks_fts (id, titulo, conteudo, tipo)
                VALUES (?, ?, ?, ?)
            """, (pid, ptit, pcont, tipo))

            # Tabela duque_ia_chunks
            cur.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (pid,))
            cur.execute("""
                INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
                VALUES (?, 'servico_publico', ?, NULL, ?, ?)
            """, (pid, pcont, pmeta_str, ptags_str))

            inserted_parts += 1

    conn.commit()
    print(f"[OK] {deleted_parents} serviços monolíticos removidos.")
    print(f"[OK] {inserted_parts} partes semânticas ({inserted_parts//2} serviços x 2 partes) inseridas nas 3 tabelas!")

    # Verificação pós-aplicação
    cur.execute("SELECT count(*) FROM chunks WHERE tipo = 'SERVICO_PUBLICO' AND length(conteudo) > 3000")
    remaining_over = cur.fetchone()[0]
    print(f"[OK] Serviços públicos > 3000 chars restantes em 'chunks': {remaining_over}")

    cur.execute("SELECT count(*) FROM chunks")
    c_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM chunks_fts")
    f_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM duque_ia_chunks")
    d_count = cur.fetchone()[0]
    print(f"[OK] Contagem Final em vector.db: chunks={c_count}, chunks_fts={f_count}, duque_ia_chunks={d_count}")

    conn.close()

if __name__ == "__main__":
    apply_split()
