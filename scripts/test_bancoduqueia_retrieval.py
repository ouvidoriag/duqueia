# -*- coding: utf-8 -*-
"""
Teste de Recuperação Semântica / FTS5 após a carga do BANCODUQUEIA
Testa as 5 consultas canônicas solicitadas:
1. Castração de cães / Petzap (SMPA)
2. Quebra-molas (SMSP estudo / SMOA obra)
3. Procuradoria Geral (Arts. 59 e 60 Lei Orgânica)
4. Telefone Guarda Municipal / Segurança (sem 153)
5. Ônibus Tarifa Zero (Decreto 8.120 / SMSP)
"""

import sys
import os
import json
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_VECTOR = os.path.join(BASE_DIR, "data", "db", "vector.db")

def test_fts(query, top_k=3):
    print(f"\n==========================================")
    print(f"QUERY: '{query}'")
    print(f"==========================================")
    
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()
    
    words = [w for w in query.replace("?", "").replace(",", "").split() if len(w) > 2]
    terms = " OR ".join([f'"{w}"' for w in words])
    
    cur.execute("""
        SELECT c.id, c.tipo, c.titulo, c.conteudo, c.metadata_json, rank
        FROM chunks_fts f
        JOIN chunks c ON f.id = c.id
        WHERE chunks_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (terms, top_k * 3))
    
    rows = cur.fetchall()
    
    # Aplica o peso de boost das regras de negócio
    scored_results = []
    for r in rows:
        cid, tipo, tit, cont, meta_str, rank = r
        try:
            meta = json.loads(meta_str)
        except:
            meta = {}
            
        boost = float(meta.get("boost_weight", 1.0))
        # Ajuste de pontuação combinada
        score = (-rank) * boost
        scored_results.append((cid, tipo, tit, cont, meta, score))
        
    scored_results.sort(key=lambda x: x[5], reverse=True)
    
    for idx, (cid, tipo, tit, cont, meta, score) in enumerate(scored_results[:top_k], 1):
        fonte = meta.get("fonte_oficial", meta.get("tipo_label", tipo))
        boost = meta.get("boost_weight", 1.0)
        linhas = cont.strip().split("\n")
        primeira_linha = linhas[0] if linhas else ""
        segunda_linha = linhas[1] if len(linhas) > 1 else ""
        
        print(f"[{idx}] [{tipo}] {tit} (Boost: {boost}, Score: {score:.2f})")
        print(f"    Fonte: {fonte}")
        print(f"    Trecho 1: {primeira_linha[:120]}")
        if segunda_linha:
            print(f"    Trecho 2: {segunda_linha[:120]}")
            
    conn.close()

if __name__ == "__main__":
    test_fts("como castrar cachorro de graça na prefeitura")
    test_fts("vistoria de quebra-molas redutor de velocidade")
    test_fts("qual a função da procuradoria geral do município")
    test_fts("telefone segurança pública guarda municipal")
    test_fts("ônibus tarifa zero linhas gratuitas")
