import os
import sys
import sqlite3
import io

# Força saída UTF-8 no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Garante acesso à pasta utils e root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from agent.main import DuqueIAAgent

def test_db_structure():
    db_path = os.path.join(ROOT, "agent", "duque_ia.db")
    print("==========================================================")
    print("    VALIDAÇÃO DO BANCO DE DADOS ESTRUTURADO DO DUQUE IA    ")
    print("==========================================================")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Verifica tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    
    required_tables = ["secretarias", "services", "service_phones", "service_steps", "service_documents"]
    all_ok = True
    print("Verificando tabelas:")
    for t in required_tables:
        if t in tables:
            print(f"  [OK] Tabela '{t}' existe.")
        else:
            print(f"  [ERRO] Tabela '{t}' não encontrada!")
            all_ok = False
            
    # 2. Verifica views
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
    views = [r[0] for r in cursor.fetchall()]
    if "vw_ia_servicos" in views:
        print("  [OK] View 'vw_ia_servicos' existe.")
    else:
        print("  [ERRO] View 'vw_ia_servicos' não encontrada!")
        all_ok = False
        
    # 3. Verifica dados carregados
    cursor.execute("SELECT COUNT(*) FROM services")
    count_services = cursor.fetchone()[0]
    print(f"Total de Serviços Cadastrados: {count_services}")
    
    cursor.execute("SELECT COUNT(*) FROM secretarias")
    count_sec = cursor.fetchone()[0]
    print(f"Total de Secretarias Cadastradas: {count_sec}")
    
    if count_services > 0 and count_sec > 0:
        print("  [OK] Dados carregados corretamente.")
    else:
        print("  [ERRO] Nenhum dado relacional populado!")
        all_ok = False
        
    # 4. Teste de Busca Estruturada no Agente
    agent = DuqueIAAgent(db_path=db_path)
    print("\nExecutando teste de recuperação estruturada:")
    # Exemplo: Serviço de Libras para Crianças
    results = agent.retrieve_context("Onde é oferecido o curso de Língua Brasileira de Sinais - Libras?")
    
    if results:
        print(f"  [OK] Recuperado com sucesso!")
        print(f"  -> Melhor Chunk Titulo: {results[0]['title']}")
        print(f"  -> Fonte do Chunk: {results[0]['source']}")
        print(f"  -> Score de Similaridade: {results[0]['similarity']:.4f}")
    else:
        print("  [ERRO] Falha ao recuperar contexto estruturado!")
        all_ok = False
        
    conn.close()
    
    print("\n" + "=" * 50)
    if all_ok:
        print("   >>> STATUS GERAL DA VALIDAÇÃO: SUCESSO ✅ <<<")
    else:
        print("   >>> STATUS GERAL DA VALIDAÇÃO: FALHA ❌ <<<")
    print("=" * 50)

if __name__ == "__main__":
    test_db_structure()
