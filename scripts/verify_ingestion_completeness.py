import pandas as pd
import sqlite3
import os

def check_ingestion():
    excel_path = r"data/knowledge/CRIADO/CARTA_DE_SERVICO_AJUSTE_23.05.26.xlsx"
    if not os.path.exists(excel_path):
        print("Excel não encontrado:", excel_path)
        return

    df = pd.read_excel(excel_path)
    df.columns = df.iloc[1].tolist()
    df = df.iloc[2:].reset_index(drop=True)
    
    total_excel_rows = len(df)
    print(f"Total de serviços no Excel: {total_excel_rows}")
    
    conn_main = sqlite3.connect("data/db/main.db")
    cur_main = conn_main.cursor()
    cur_main.execute("SELECT count(*) FROM services;")
    total_db_services = cur_main.fetchone()[0]
    print(f"Total de serviços no main.db (tabela services): {total_db_services}")

    cur_main.execute("SELECT count(*) FROM service_steps;")
    total_steps = cur_main.fetchone()[0]
    print(f"Total de passos no main.db (service_steps): {total_steps}")
    
    cur_main.execute("SELECT count(*) FROM service_documents;")
    total_docs = cur_main.fetchone()[0]
    print(f"Total de documentos no main.db (service_documents): {total_docs}")

    conn_vec = sqlite3.connect("data/db/vector.db")
    cur_vec = conn_vec.cursor()
    cur_vec.execute("SELECT count(*) FROM duque_ia_chunks WHERE category='carta_servicos';")
    total_vec_carta = cur_vec.fetchone()[0]
    print(f"Total de chunks de carta_servicos no vector.db (duque_ia_chunks): {total_vec_carta}")

    # Checa amostra de dados
    print("\n--- Verificação de campos no Excel vs DB ---")
    sample = df.iloc[0]
    print("Excel Serviço 1:", sample['Serviço'])
    print("  Documentação necessária:", sample.get('Documentação necessária'))
    print("  Passo a passo:", str(sample.get('Passo a passo'))[:100])
    print("  Tempo de espera:", sample.get('Tempo de espera'))
    print("  Prazo máximo:", sample.get('Prazo máximo'))
    print("  Norma:", sample.get('Norma que regulamenta'))

if __name__ == "__main__":
    check_ingestion()
