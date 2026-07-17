import sqlite3
from utils.db_client import query_db, query_one, execute_db

class VectorRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_chunks_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM duque_ia_chunks")
        return row[0] if row else 0

    def list_chunks(self) -> list:
        return query_db(self.db_path, "SELECT source, category, content, embedding, metadata, keywords FROM duque_ia_chunks")

    def get_chunks_by_category(self, category: str, filter_field: str = "category") -> list:
        return query_db(
            self.db_path,
            f"SELECT DISTINCT source, category, content, metadata FROM duque_ia_chunks WHERE {filter_field} = ? ORDER BY source",
            (category,)
        )

    def delete_chunks_by_sources(self, sources: list):
        if not sources:
            return
        placeholders = ",".join("?" for _ in sources)
        execute_db(self.db_path, f"DELETE FROM duque_ia_chunks WHERE source IN ({placeholders})", tuple(sources))

    def insert_chunk(self, source: str, category: str, content: str, embedding_str: str, metadata_str: str, keywords_str: str):
        execute_db(
            self.db_path,
            "INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords) VALUES (?, ?, ?, ?, ?, ?)",
            (source, category, content, embedding_str, metadata_str, keywords_str)
        )
