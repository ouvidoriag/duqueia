import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection(db_path: str):
    """Gerenciador de contexto para conexões do SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def query_db(db_path: str, query: str, params: tuple = ()) -> list:
    """Executa uma consulta SELECT e retorna todas as linhas."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def query_one(db_path: str, query: str, params: tuple = ()) -> tuple | None:
    """Executa uma consulta SELECT e retorna a primeira linha ou None."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

def execute_db(db_path: str, query: str, params: tuple = ()):
    """Executa um comando que altera o banco (INSERT, UPDATE, DELETE, CREATE) e commita."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
