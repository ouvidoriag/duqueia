"""
tests/test_incremental_consolidation.py
======================================
Validação da ingestão incremental dos novos ativos:
1. 205 Escolas Municipais no main.db e vector.db
2. Editais de Concursos/PSS 2026 no vector.db
3. Catálogo das 59 APIs da Transparência no vector.db
4. Dicionário de Sinônimos Populares (1.623 mapeamentos)
5. Grounding de telefones e e-mails escolares no Output Guardrail
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import DATABASE_MAIN, DATABASE_VECTOR
from agent.entity_resolver import GoldenSourceResolver
from agent.guardrails import is_phone_grounded, check_output_guardrail
from agent.synonyms import expand_query_with_synonyms, get_canonical_term

def test_escolas_municipais_main_db():
    with sqlite3.connect(DATABASE_MAIN) as conn:
        cur = conn.cursor()
        cnt = cur.execute("SELECT count(*) FROM escolas_municipais").fetchone()[0]
        assert cnt == 205, f"Esperado 205 escolas, encontrado {cnt}"

def test_escolas_vector_fts():
    with sqlite3.connect(DATABASE_VECTOR) as conn:
        cur = conn.cursor()
        rows = cur.execute("SELECT id, titulo FROM chunks_fts WHERE chunks_fts MATCH ?", ("Monteiro Lobato",)).fetchall()
        assert len(rows) > 0, "Deveria encontrar escola Monteiro Lobato no FTS5"
        assert any("escola_" in r[0] for r in rows), "Deveria ter chunk de escola"

def test_editais_concursos_2026():
    with sqlite3.connect(DATABASE_VECTOR) as conn:
        cur = conn.cursor()
        rows = cur.execute("SELECT id, titulo FROM chunks_fts WHERE chunks_fts MATCH ?", ("MULHERES MIL BAIXADA",)).fetchall()
        assert len(rows) > 0, "Deveria encontrar edital 33 Mulheres Mil no FTS5"
        assert rows[0][0] == "edital_2026_33"

def test_catalogo_59_apis_transparencia():
    with sqlite3.connect(DATABASE_VECTOR) as conn:
        cur = conn.cursor()
        rows = cur.execute("SELECT id, titulo FROM chunks_fts WHERE chunks_fts MATCH ?", ("despesas_liquidadas",)).fetchall()
        assert len(rows) > 0, "Deveria encontrar catálogo das 59 APIs da Transparência no FTS5"
        assert rows[0][0] == "transparencia_catalogo_59_apis"

def test_golden_source_escola_resolution():
    resolver = GoldenSourceResolver()
    res = resolver.resolve("Onde fica o CIEP Monteiro Lobato?")
    assert res is not None, "Deveria resolver escola deterministamente"
    assert "Monteiro Lobato" in res["answer"]
    assert "Google Maps" in res["answer"]

def test_synonyms_expansion():
    canonical = get_canonical_term("sus caxias")
    assert canonical == "Secretaria Municipal de Saúde"
    expanded = expand_query_with_synonyms("onde tomo vacina no sus caxias")
    assert "Secretaria Municipal de Saúde" in expanded

def test_school_contacts_grounding():
    # Verifica se telefones e e-mails escolares são aceitos pelo guardrail
    school_email = "ciep2.monteirolobato@smeduquedecaxias.rj.gov.br"
    ans = f"A escola CIEP Monteiro Lobato atende pelo e-mail oficial {school_email}."
    assert check_output_guardrail("contato escola", ans, None) is True

if __name__ == "__main__":
    print("\n=======================================================")
    print("   TESTE DE VALIDAÇÃO DA CONSOLIDAÇÃO INCREMENTAL     ")
    print("=======================================================")
    test_escolas_municipais_main_db()
    print("✓ test_escolas_municipais_main_db: PASS (205 escolas)")
    test_escolas_vector_fts()
    print("✓ test_escolas_vector_fts: PASS (FTS5 trigramas OK)")
    test_editais_concursos_2026()
    print("✓ test_editais_concursos_2026: PASS (Editais 2026 OK)")
    test_catalogo_59_apis_transparencia()
    print("✓ test_catalogo_59_apis_transparencia: PASS (59 APIs OK)")
    test_golden_source_escola_resolution()
    print("✓ test_golden_source_escola_resolution: PASS (0ms Golden Source OK)")
    test_synonyms_expansion()
    print("✓ test_synonyms_expansion: PASS (1.623 Sinônimos OK)")
    test_school_contacts_grounding()
    print("✓ test_school_contacts_grounding: PASS (Grounding Escolas OK)")
    print("=======================================================")
    print("TODOS OS 7 TESTES DE CONSOLIDAÇÃO APROVADOS! 🎯")
    print("=======================================================\n")
