import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from config.settings import DATABASE_MAIN, DATABASE_VECTOR

def create_indexes():
    print("==================================================")
    print("CONFIGURANDO ÍNDICES DE PERFORMANCE (MAIN & VECTOR)")
    print("==================================================")

    # 1. Índices no main.db
    if os.path.exists(DATABASE_MAIN):
        print(f"\n[main.db] Conectando em: {DATABASE_MAIN}")
        conn = sqlite3.connect(DATABASE_MAIN)
        cur = conn.cursor()
        main_indexes = [
            ("idx_services_secretaria", "services(secretaria_id)"),
            ("idx_services_category", "services(category_id)"),
            ("idx_phones_service", "service_phones(service_id)"),
            ("idx_emails_service", "service_emails(service_id)"),
            ("idx_links_service", "service_links(service_id)"),
            ("idx_steps_service", "service_steps(service_id)"),
            ("idx_documents_service", "service_documents(service_id)"),
            ("idx_priorities_service", "service_priorities(service_id)"),
            ("idx_unidades_secretaria", "secretaria_unidades(secretaria_id)"),
            ("idx_unidades_name", "secretaria_unidades(name)"),
            ("idx_logradouros_nome", "logradouros_enderecos(logradouro)"),
            ("idx_logradouros_bairro", "logradouros_enderecos(bairro_nome)"),
            ("idx_logradouros_cep", "logradouros_enderecos(cep)"),
            ("idx_bairros_nome", "bairros(nome)"),
            ("idx_secretarias_name", "secretarias(name)"),
            ("idx_regras_tema", "regras_negocio(tema)"),
            ("idx_regras_assunto", "regras_negocio(assunto)"),
            ("idx_linhas_tarifa_zero", "linhas_tarifa_zero(numero_linha)")
        ]
        for idx_name, idx_target in main_indexes:
            try:
                cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_target};")
                print(f"  -> main.db: {idx_name} configurado.")
            except Exception as e:
                print(f"  -> [Aviso] {idx_name}: {e}")
        conn.commit()
        conn.close()

    # 2. Índices no vector.db
    if os.path.exists(DATABASE_VECTOR):
        print(f"\n[vector.db] Conectando em: {DATABASE_VECTOR}")
        conn = sqlite3.connect(DATABASE_VECTOR)
        cur = conn.cursor()
        vector_indexes = [
            ("idx_chunks_source", "duque_ia_chunks(source)"),
            ("idx_chunks_category", "duque_ia_chunks(category)"),
            ("idx_chunks_tipo", "chunks(tipo)")
        ]
        for idx_name, idx_target in vector_indexes:
            try:
                cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_target};")
                print(f"  -> vector.db: {idx_name} configurado.")
            except Exception as e:
                print(f"  -> [Aviso] {idx_name}: {e}")
        conn.commit()
        conn.close()

    print("\nOtimização de índices concluída com sucesso! [OK]")

if __name__ == "__main__":
    create_indexes()
