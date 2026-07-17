import os
import sys
import sqlite3
import io

# Força saída UTF-8 no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Garante acesso à raiz do projeto
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config.settings import DATABASE_MAIN, DATABASE_VECTOR, DATABASE_CACHE, DATABASE_TELEMETRY
from storage import storage_manager

def format_size(path: str) -> str:
    if not os.path.exists(path):
        return "N/A"
    bytes_size = os.path.getsize(path)
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.2f} MB"

def main():
    print("=" * 60)
    print("      DUQUE IA — RELATÓRIO OPERACIONAL DE PERSISTÊNCIA")
    print("=" * 60)

    # 1. Main DB
    print("\n[MAIN DB] — Dados Estruturados Municipais")
    print(f"  Caminho do arquivo   : {DATABASE_MAIN}")
    print(f"  Tamanho em disco     : {format_size(DATABASE_MAIN)}")
    print(f"  Total de Secretarias : {storage_manager.main.get_secretarias_count()}")
    print(f"  Total de Unidades    : {storage_manager.main.get_unidades_count()} (ex: CRAS)")
    print(f"  Total de Serviços    : {storage_manager.main.get_services_count()}")
    
    health = storage_manager.health_check()
    print(f"  Integridade Física   : {health['main']['integrity']}")
    print(f"  Schema Version       : {health['main']['schema_version']}")
    print(f"  Modo de Journal (WAL): {health['main']['journal_mode']}")

    # 2. Vector DB
    print("\n[VECTOR DB] — Busca Semântica e Chunks")
    print(f"  Caminho do arquivo   : {DATABASE_VECTOR}")
    print(f"  Tamanho em disco     : {format_size(DATABASE_VECTOR)}")
    print(f"  Total de Chunks      : {storage_manager.vector.get_chunks_count()}")
    
    # Get embedding model
    model_row = None
    if os.path.exists(DATABASE_VECTOR):
        try:
            conn = sqlite3.connect(DATABASE_VECTOR)
            cur = conn.cursor()
            cur.execute("SELECT provider, model, dimension FROM embedding_metadata LIMIT 1")
            model_row = cur.fetchone()
            conn.close()
        except Exception:
            pass
            
    if model_row:
        print(f"  Provedor / Modelo    : {model_row[0]} / {model_row[1]} (Dim: {model_row[2]})")
    else:
        print("  Provedor / Modelo    : Não configurado ou offline")
    print(f"  Integridade Física   : {health['vector']['integrity']}")
    print(f"  Schema Version       : {health['vector']['schema_version']}")
    print(f"  Modo de Journal (WAL): {health['vector']['journal_mode']}")

    # 3. Cache DB
    print("\n[CACHE DB] — Triagem e Desempenho")
    print(f"  Caminho do arquivo   : {DATABASE_CACHE}")
    print(f"  Tamanho em disco     : {format_size(DATABASE_CACHE)}")
    print(f"  Total de Entradas    : {storage_manager.cache.get_entries_count()}")
    print(f"  Integridade Física   : {health['cache']['integrity']}")
    print(f"  Schema Version       : {health['cache']['schema_version']}")
    print(f"  Modo de Journal (WAL): {health['cache']['journal_mode']}")

    # 4. Telemetry DB
    print("\n[TELEMETRY DB] — Histórico e Instrumentação")
    print(f"  Caminho do arquivo   : {DATABASE_TELEMETRY}")
    print(f"  Tamanho em disco     : {format_size(DATABASE_TELEMETRY)}")
    print(f"  Sessões registradas  : {storage_manager.telemetry.get_sessions_count()}")
    print(f"  Mensagens de chat    : {storage_manager.telemetry.get_messages_count()}")
    print(f"  Histórico RAG Queries: {storage_manager.telemetry.get_queries_count()}")
    print(f"  Integridade Física   : {health['telemetry']['integrity']}")
    print(f"  Schema Version       : {health['telemetry']['schema_version']}")
    print(f"  Modo de Journal (WAL): {health['telemetry']['journal_mode']}")

    # 5. Providers Check
    print("\n[AI PROVIDERS] — Status das APIs de LLM")
    print(f"  Gemini API Status    : {health['providers']['gemini']['status']} ({health['providers']['gemini']['keys_loaded']} chaves carregadas)")
    print(f"  Groq API Status      : {health['providers']['groq']['status']}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
