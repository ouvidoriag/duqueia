#!/usr/bin/env python3
"""
sync.py  —  Duque IA / eusoulindo
Sincroniza automaticamente os arquivos do projeto com a pasta eusoulindo.

Uso:
    python eusoulindo/sync.py [--dry-run]
    
Flags:
    --dry-run   Simula as operações sem copiar nenhum arquivo.
"""

import os
import shutil
import sqlite3
import json
import argparse
from datetime import datetime

# Ajustar ROOT para o pai de eusoulindo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
DEST       = SCRIPT_DIR
DB_PATH    = os.path.join(ROOT, "agent", "duque_ia.db")

SYNC_MAP = {
    # (origem, destino_relativo_a_DEST)
    "bancoia/CARTA_DE_SERVICO_AJUSTE_23.05.26.xlsx": "datasets/excel/CARTA_DE_SERVICO_AJUSTE_23.05.26.xlsx",
    "bancoia/assuntoXsecretaria.csv":               "datasets/csv/assuntoXsecretaria.csv",
    "raw_csv_files/bairros_caxias.csv":             "datasets/csv/bairros_caxias.csv",
    "raw_excel_files/postos_saude_caxias.xlsx":     "datasets/excel/postos_saude_caxias.xlsx",
    "metrics/retrieval_metrics.csv":                "datasets/csv/retrieval_metrics.csv",
    "metrics/retrieval_performance.csv":            "datasets/csv/retrieval_performance.csv",
    "duque_ia_database_schema.html":                "documentation/html/duque_ia_database_schema.html",
    "scripts/setup/production_schema_supabase.sql": "database/schema/production_schema_supabase.sql",
    ".env.example":                                 "assets/.env.example",
}

def sync(dry_run=False):
    tag = "[DRY-RUN] " if dry_run else ""
    updated = 0
    skipped = 0

    print(f"\n{'='*60}")
    print(f"  Duque IA — Sincronização eusoulindo  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    # Sincronizar arquivos mapeados
    for rel_src, rel_dst in SYNC_MAP.items():
        src = os.path.join(ROOT, rel_src)
        dst = os.path.join(DEST, rel_dst)
        
        if not os.path.exists(src):
            print(f"  ⚠️  Não encontrado: {rel_src}")
            skipped += 1
            continue
        
        # Comparar timestamps
        src_mtime = os.path.getmtime(src)
        dst_mtime = os.path.getmtime(dst) if os.path.exists(dst) else 0
        
        if src_mtime > dst_mtime:
            print(f"  {tag}🔄 Atualizando: {os.path.basename(src)}")
            if not dry_run:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            updated += 1
        else:
            skipped += 1

    # Sincronizar PDFs novos
    pdf_src = os.path.join(ROOT, "bancoia", "OFICIOS")
    pdf_dst = os.path.join(DEST, "documentation/pdf")
    if os.path.exists(pdf_src):
        for fname in os.listdir(pdf_src):
            if not fname.lower().endswith(".pdf"):
                continue
            src = os.path.join(pdf_src, fname)
            dst = os.path.join(pdf_dst, fname)
            if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                print(f"  {tag}📄 PDF: {fname}")
                if not dry_run:
                    shutil.copy2(src, dst)
                updated += 1

    # Regenerar schema_full.sql e schema.json
    if os.path.exists(DB_PATH):
        print(f"\n  {tag}🗄️  Regenerando schema do banco...")
        if not dry_run:
            conn = sqlite3.connect(DB_PATH)
            cur  = conn.cursor()
            cur.execute("SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type DESC, name ASC")
            objects = cur.fetchall()
            cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name")
            all_tables = cur.fetchall()

            ddl = [
                "-- Duque IA — Schema Completo (auto-sincronizado)",
                f"-- Última sincronização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "", "PRAGMA foreign_keys = ON;", ""
            ]
            for obj_type, name, sql in objects:
                if name.startswith("sqlite_"):
                    continue
                ddl.append(f"-- {obj_type.upper()}: {name}")
                ddl.append(f"{sql.strip()};\n")

            schema_sql_path = os.path.join(DEST, "database/schema/schema_full.sql")
            with open(schema_sql_path, "w", encoding="utf-8") as f:
                f.write("\n".join(ddl))

            schema_json = {}
            for table_name, table_type in all_tables:
                cur.execute(f"PRAGMA table_info({table_name})")
                cols = cur.fetchall()
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    rc = cur.fetchone()[0]
                except Exception:
                    rc = None
                schema_json[table_name] = {
                    "type": table_type,
                    "row_count": rc,
                    "columns": [{"cid": c[0], "name": c[1], "type": c[2], "not_null": bool(c[3]), "default": c[4], "primary_key": bool(c[5])} for c in cols]
                }
            with open(os.path.join(DEST, "database/schema/schema.json"), "w", encoding="utf-8") as f:
                json.dump(schema_json, f, indent=2, ensure_ascii=False)

            conn.close()
            updated += 2
            print(f"     ✅ schema_full.sql e schema.json atualizados.")

    print(f"\n  ✅ Sincronização concluída — {updated} atualizado(s), {skipped} sem alteração.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza eusoulindo com o projeto Duque IA.")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem copiar arquivos")
    args = parser.parse_args()
    sync(dry_run=args.dry_run)
