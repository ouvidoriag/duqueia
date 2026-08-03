"""
DUQUE IA — Relatório de Auditoria da Telemetria de Falhas (retrieval_failures)
Gera relatórios consolidados para a Ouvidoria e Equipe Técnica sobre falhas de busca e lacunas da ontologia.
"""
import os
import sys
import sqlite3
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config.settings import DATABASE_TELEMETRY

def generate_failures_report():
    if not os.path.exists(DATABASE_TELEMETRY):
        print(f"[Report] Banco de telemetria {DATABASE_TELEMETRY} não encontrado.")
        return

    conn = sqlite3.connect(DATABASE_TELEMETRY)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='retrieval_failures'")
    if not cur.fetchone():
        print("[Report] Tabela 'retrieval_failures' ainda não possui registros.")
        conn.close()
        return

    print("\n" + "=" * 70)
    print("      DUQUE IA — RELATÓRIO DE AUDITORIA DE FALHAS DE RETRIEVAL")
    print("=" * 70)

    cur.execute("""
        SELECT query, intent, top_source, expected_source, user_feedback, confidence, timestamp 
        FROM retrieval_failures 
        ORDER BY id DESC LIMIT 50
    """)
    failures = cur.fetchall()
    print(f"Total de ocorrências registradas recentemente: {len(failures)}\n")

    cur.execute("""
        SELECT query, COUNT(*) as count
        FROM retrieval_failures
        GROUP BY query
        ORDER BY count DESC LIMIT 10
    """)
    top_queries = cur.fetchall()

    if top_queries:
        print("--- TOP 10 PERGUNTAS COM MAIOR FREQUÊNCIA DE FALHA ---")
        for q, count in top_queries:
            print(f"  [{count}x] '{q}'")
        print("-" * 70)

    conn.close()

if __name__ == "__main__":
    generate_failures_report()
