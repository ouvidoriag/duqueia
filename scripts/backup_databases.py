# -*- coding: utf-8 -*-
"""
backup_databases.py — DUQUE IA
==============================
Rotina de Backup Transacional Seguro dos bancos SQLite do Duque IA.
Utiliza a Online Backup API nativa do SQLite para garantir consistência total
mesmo durante operações concorrentes em modo WAL (Write-Ahead Logging).
Aplica política de retenção rotativa mantendo apenas os 3 snapshots mais recentes.
"""

import os
import sys
import time
import shutil
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(ROOT_DIR, "data", "db")
BACKUP_BASE_DIR = os.path.join(ROOT_DIR, "data", "backups")

MAX_BACKUP_SNAPSHOTS = 3

DATABASES_TO_BACKUP = [
    "main.db",
    "vector.db",
    "cache.db",
    "telemetry.db"
]

def backup_single_database(source_path: str, dest_path: str) -> bool:
    """Executa cópia transacional segura utilizando a SQLite Online Backup API."""
    if not os.path.exists(source_path):
        print(f"⚠️  Banco de origem '{os.path.basename(source_path)}' não encontrado. Ignorando.")
        return False
        
    src_conn = None
    dst_conn = None
    try:
        src_conn = sqlite3.connect(source_path)
        dst_conn = sqlite3.connect(dest_path)
        
        # SQLite Online Backup API: copia página por página bloqueando de forma cooperativa
        src_conn.backup(dst_conn, pages=100, sleep=0.01)
        dst_conn.commit()
        
        # Validação pós-backup
        cur = dst_conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        check_res = cur.fetchone()[0]
        if check_res != "ok":
            raise RuntimeError(f"Integridade falhou no backup: {check_res}")
            
        src_size = round(os.path.getsize(source_path) / (1024 * 1024), 2)
        dst_size = round(os.path.getsize(dest_path) / (1024 * 1024), 2)
        print(f"  ✅ {os.path.basename(source_path):<15} -> Backup OK ({dst_size} MB | Integridade: {check_res})")
        return True
    except Exception as e:
        print(f"  ❌ Falha ao realizar backup de {os.path.basename(source_path)}: {e}")
        return False
    finally:
        if dst_conn:
            dst_conn.close()
        if src_conn:
            src_conn.close()

def rotate_old_backups(backup_base_dir: str, keep_limit: int = MAX_BACKUP_SNAPSHOTS):
    """Mantém apenas os 'keep_limit' backups mais recentes, expurgando pastas antigas."""
    if not os.path.exists(backup_base_dir):
        return
        
    entries = []
    for item in os.listdir(backup_base_dir):
        full_path = os.path.join(backup_base_dir, item)
        if os.path.isdir(full_path) and item.startswith("snapshot_"):
            entries.append((os.path.getmtime(full_path), full_path))
            
    entries.sort(key=lambda x: x[0], reverse=True)
    
    if len(entries) > keep_limit:
        to_delete = entries[keep_limit:]
        for _, path_to_del in to_delete:
            try:
                shutil.rmtree(path_to_del)
                print(f"  🧹 Backup antigo expurgado: {os.path.basename(path_to_del)}")
            except Exception as e:
                print(f"  ⚠️  Erro ao expurgar {path_to_del}: {e}")

def run_backup():
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_snapshot_dir = os.path.join(BACKUP_BASE_DIR, f"snapshot_{timestamp_str}")
    os.makedirs(target_snapshot_dir, exist_ok=True)
    
    print("=" * 65)
    print(f"   DUQUE IA — INICIANDO BACKUP TRANSACIONAL SEGURO (ONLINE API)")
    print(f"   Destino: {target_snapshot_dir}")
    print("=" * 65)
    
    t0 = time.time()
    success_count = 0
    
    for db_name in DATABASES_TO_BACKUP:
        src = os.path.join(DB_DIR, db_name)
        dst = os.path.join(target_snapshot_dir, db_name)
        if backup_single_database(src, dst):
            success_count += 1
            
    print("\nAplicando política de retenção rotativa de backups...")
    rotate_old_backups(BACKUP_BASE_DIR, keep_limit=MAX_BACKUP_SNAPSHOTS)
    
    elapsed = round(time.time() - t0, 2)
    print("-" * 65)
    print(f"Backup concluído com sucesso em {elapsed}s ({success_count}/{len(DATABASES_TO_BACKUP)} bancos preservados).")
    print("=" * 65)
    return success_count == len(DATABASES_TO_BACKUP)

if __name__ == "__main__":
    success = run_backup()
    sys.exit(0 if success else 1)
