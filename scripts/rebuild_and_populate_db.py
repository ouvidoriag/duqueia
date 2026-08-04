import os
import sys
import subprocess
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from setup_and_run import setup_database, check_requirements

def main():
    print("============================================================")
    print("🚀 [DUQUE IA] RECONSTRUÇÃO E POPULAÇÃO COMPLETA DOS BANCOS")
    print("============================================================")
    
    # 1. Garante dependências
    check_requirements()
    
    # 2. Inicializa estrutura dos 4 bancos SQLite
    setup_database()
    
    # 3. Popula dados estruturados (Secretarias, Unidades, Serviços em main.db)
    print("\n📦 [1/3] Populando banco relacional (main.db) com serviços municipais...")
    try:
        import importlib
        mod_services = importlib.import_module("ingestion.parser.populate_structured_services")
        if hasattr(mod_services, "main"):
            mod_services.main()
        elif hasattr(mod_services, "populate"):
            mod_services.populate()
    except Exception as e:
        print(f"   ⚠️ Aviso ao popular serviços: {e}")
        
    # 4. Executa ingestão de PDFs e Carta de Serviços
    print("\n📄 [2/3] Processando PDFs e Carta de Serviços em data/processed...")
    try:
        mod_carta = importlib.import_module("ingestion.parser.parse_carta_servico")
        if hasattr(mod_carta, "main"):
            mod_carta.main()
    except Exception as e:
        print(f"   ⚠️ Aviso ao processar Carta de Serviços: {e}")

    try:
        mod_pdfs = importlib.import_module("ingestion.parser.parse_pdfs")
        if hasattr(mod_pdfs, "main"):
            mod_pdfs.main()
    except Exception as e:
        print(f"   ⚠️ Aviso ao processar PDFs: {e}")
        
    # 5. Gera vetores e popula vector.db
    print("\n🧠 [3/3] Gerando embeddings semânticos (vector.db)...")
    try:
        mod_embed = importlib.import_module("ingestion.embed.main")
        if hasattr(mod_embed, "main"):
            mod_embed.main()
    except Exception as e:
        print(f"   ⚠️ Aviso ao gerar embeddings: {e}")
        
    print("\n============================================================")
    print("✅ POPULAÇÃO DE DADOS CONCLUÍDA COM SUCESSO!")
    print("============================================================")

if __name__ == "__main__":
    main()
