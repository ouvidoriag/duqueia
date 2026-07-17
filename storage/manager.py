import os
import sqlite3
from utils.db_client import execute_db, query_one
from config.settings import DATABASE_MAIN, DATABASE_VECTOR, DATABASE_CACHE, DATABASE_TELEMETRY
from storage.main_repository import MainRepository
from storage.vector_repository import VectorRepository
from storage.cache_repository import CacheRepository
from storage.telemetry_repository import TelemetryRepository

class StorageManager:
    def __init__(self):
        self.main = MainRepository(DATABASE_MAIN)
        self.vector = VectorRepository(DATABASE_VECTOR)
        self.cache = CacheRepository(DATABASE_CACHE)
        self.telemetry = TelemetryRepository(DATABASE_TELEMETRY)

    def run_maintenance(self):
        """Executa VACUUM e ANALYZE em todos os bancos configurados."""
        paths = [DATABASE_MAIN, DATABASE_VECTOR, DATABASE_CACHE, DATABASE_TELEMETRY]
        for path in paths:
            if os.path.exists(path):
                print(f"[Maintenance] Executando VACUUM e ANALYZE em {os.path.basename(path)}...")
                try:
                    execute_db(path, "VACUUM;")
                    execute_db(path, "ANALYZE;")
                except Exception as e:
                    print(f"[Maintenance Error] Falha em {os.path.basename(path)}: {e}")

    def health_check(self) -> dict:
        """Verifica o status, integridade, modo WAL e status dos provedores de IA."""
        # Imports dinâmicos para evitar importações circulares
        from utils.gemini_client import GeminiClient
        from utils.groq_client import GroqClient

        report = {}
        paths = {
            "main": DATABASE_MAIN,
            "vector": DATABASE_VECTOR,
            "cache": DATABASE_CACHE,
            "telemetry": DATABASE_TELEMETRY
        }
        for name, path in paths.items():
            db_status = {
                "exists": os.path.exists(path),
                "path": path,
                "integrity": "unknown",
                "schema_version": 0,
                "journal_mode": "unknown"
            }
            if db_status["exists"]:
                try:
                    # Integrity Check
                    row = query_one(path, "PRAGMA integrity_check")
                    db_status["integrity"] = row[0] if row else "failed"
                    
                    # Schema Version
                    ver_row = query_one(path, "SELECT MAX(version) FROM schema_version")
                    db_status["schema_version"] = ver_row[0] if ver_row and ver_row[0] is not None else 0
                    
                    # WAL Mode Check
                    wal_row = query_one(path, "PRAGMA journal_mode;")
                    db_status["journal_mode"] = wal_row[0] if wal_row else "unknown"
                except Exception as e:
                    db_status["integrity"] = f"error: {str(e)}"
            report[name] = db_status

        # Checagem de Provedores de IA
        try:
            gemini = GeminiClient()
            gemini_keys = len(gemini.api_keys)
            gemini_status = "active" if gemini_keys > 0 else "offline/no_keys"
        except Exception as e:
            gemini_keys = 0
            gemini_status = f"error: {e}"

        try:
            groq = GroqClient()
            groq_status = "active" if groq.available else "offline/no_key"
        except Exception as e:
            groq_status = f"error: {e}"

        report["providers"] = {
            "gemini": {
                "status": gemini_status,
                "keys_loaded": gemini_keys
            },
            "groq": {
                "status": groq_status
            }
        }
        return report
