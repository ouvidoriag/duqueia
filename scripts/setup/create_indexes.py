import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "duque_ia.db")
DB_PATH = os.path.abspath(DB_PATH)

def create_indexes():
    if not os.path.exists(DB_PATH):
        print(f"[Erro] Banco de dados não encontrado em: {DB_PATH}")
        return

    print(f"Conectando ao banco de dados: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    indexes = [
        ("idx_chunks_category", "duque_ia_chunks(category)"),
        ("idx_services_secretaria", "services(secretaria_id)"),
        ("idx_services_category", "services(category_id)"),
        ("idx_phones_service", "service_phones(service_id)"),
        ("idx_emails_service", "service_emails(service_id)"),
        ("idx_links_service", "service_links(service_id)"),
        ("idx_steps_service", "service_steps(service_id)"),
        ("idx_documents_service", "service_documents(service_id)"),
        ("idx_priorities_service", "service_priorities(service_id)"),
        ("idx_unidades_secretaria", "secretaria_unidades(secretaria_id)")
    ]

    print("Criando índices de performance...")
    for idx_name, idx_target in indexes:
        sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_target};"
        cursor.execute(sql)
        print(f"  -> Índice {idx_name} configurado.")

    conn.commit()
    conn.close()
    print("Otimizacao de indices concluida com sucesso! [OK]")

if __name__ == "__main__":
    create_indexes()
