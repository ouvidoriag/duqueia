import sqlite3
from utils.db_client import query_one, execute_db

class CacheRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_entries_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM triage_cache")
        return row[0] if row else 0

    def get_cached_triage(self, query_hash: str, prompt_version: str, model_version: str) -> dict | None:
        row = query_one(
            self.db_path,
            "SELECT intent, confidence, needs_clarification, reason FROM triage_cache "
            "WHERE query_hash = ? AND prompt_version = ? AND model_version = ?",
            (query_hash, prompt_version, model_version)
        )
        if row:
            return {
                "intent": row[0],
                "confidence": float(row[1]),
                "needs_clarification": bool(row[2]),
                "reason": row[3],
                "source": "SQLITE_CACHE"
            }
        return None

    def save_triage_to_cache(self, query_hash: str, intent: str, confidence: float, needs_clarification: int, reason: str, model_version: str, prompt_version: str):
        execute_db(
            self.db_path,
            "INSERT OR REPLACE INTO triage_cache "
            "(query_hash, intent, confidence, needs_clarification, reason, model_version, prompt_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (query_hash, intent, confidence, needs_clarification, reason, model_version, prompt_version)
        )
