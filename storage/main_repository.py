import sqlite3
from utils.db_client import query_db, query_one

class MainRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_secretarias_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM secretarias")
        return row[0] if row else 0

    def get_services_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM services")
        return row[0] if row else 0

    def list_secretarias(self) -> list:
        return query_db(self.db_path, "SELECT id, name, code, address, phone, email, working_hours FROM secretarias")

    def get_unidades_by_secretaria(self, secretaria_id: int) -> list:
        return query_db(self.db_path, "SELECT id, name, address, phone, working_hours FROM secretaria_unidades WHERE secretaria_id = ?", (secretaria_id,))

    def get_unidades_count(self) -> int:
        row = query_one(self.db_path, "SELECT COUNT(*) FROM secretaria_unidades")
        return row[0] if row else 0
