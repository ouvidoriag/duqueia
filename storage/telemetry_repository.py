import sqlite3
from utils.db_client import query_one

class TelemetryRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_sessions_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM chat_sessions")
        return row[0] if row else 0

    def get_messages_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM chat_messages")
        return row[0] if row else 0

    def get_queries_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM rag_queries")
        return row[0] if row else 0
