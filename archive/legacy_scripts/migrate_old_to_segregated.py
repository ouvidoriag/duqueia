import sqlite3
import os

ROOT = r"c:\Users\501379.PMDC\Desktop\PRODUCAO"
old_db = os.path.join(ROOT, "data", "db", "duque_ia.db")
main_db = os.path.join(ROOT, "data", "db", "main.db")
vector_db = os.path.join(ROOT, "data", "db", "vector.db")

def copy_table(src_db, dest_db, table_name):
    print(f"Copiando tabela '{table_name}' de {os.path.basename(src_db)} para {os.path.basename(dest_db)}...")
    src_conn = sqlite3.connect(src_db)
    dest_conn = sqlite3.connect(dest_db)
    
    src_cursor = src_conn.cursor()
    dest_cursor = dest_conn.cursor()
    
    try:
        # Get column names
        src_cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in src_cursor.fetchall()]
        if not columns:
            print(f"  Tabela '{table_name}' não existe no banco de origem ou está vazia.")
            return
            
        # Select all data
        src_cursor.execute(f"SELECT * FROM {table_name};")
        rows = src_cursor.fetchall()
        
        # Clear destination table
        dest_cursor.execute(f"DELETE FROM {table_name};")
        
        # Insert
        placeholders = ",".join("?" for _ in columns)
        dest_cursor.executemany(f"INSERT OR REPLACE INTO {table_name} ({','.join(columns)}) VALUES ({placeholders});", rows)
        dest_conn.commit()
        print(f"  Tabela '{table_name}' copiada com sucesso! ({len(rows)} registros)")
    except Exception as e:
        print(f"  Erro ao copiar tabela '{table_name}': {e}")
    finally:
        src_conn.close()
        dest_conn.close()

if os.path.exists(old_db):
    print("Iniciando migração dos dados históricos...")
    
    # Copia tabelas de busca semântica para vector.db
    copy_table(old_db, vector_db, "duque_ia_chunks")
    copy_table(old_db, vector_db, "core_documents")
    copy_table(old_db, vector_db, "chunks_metadata")
    copy_table(old_db, vector_db, "embedding_metadata")
    
    # Copia tabelas estruturadas de serviços/usuários para main.db
    copy_table(old_db, main_db, "categories")
    copy_table(old_db, main_db, "services")
    copy_table(old_db, main_db, "service_phones")
    copy_table(old_db, main_db, "service_emails")
    copy_table(old_db, main_db, "service_links")
    copy_table(old_db, main_db, "service_steps")
    copy_table(old_db, main_db, "service_documents")
    copy_table(old_db, main_db, "service_priorities")
    copy_table(old_db, main_db, "service_categories")
    copy_table(old_db, main_db, "service_history")
    copy_table(old_db, main_db, "users")
    copy_table(old_db, main_db, "secretarias")
    copy_table(old_db, main_db, "secretaria_unidades")
    
    print("\nMigração concluída!")
else:
    print("Banco de dados legado 'duque_ia.db' não encontrado. Nenhuma migração necessária.")
