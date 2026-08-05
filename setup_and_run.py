import os
import sys
import shutil

# Configura codificação UTF-8 no stdout para Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adiciona raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importa lógicas encapsuladas do módulo bootstrap
from bootstrap.python_check import check_python_environment, check_requirements, log
from bootstrap.database_init import setup_database, init_db
from bootstrap.server_runner import check_node_dependencies, run_server
from bootstrap.health import run_health_check

if __name__ == "__main__":
    # Suporte a flag de diagnósticos rápido
    if "--health" in sys.argv or "-h" in sys.argv and len(sys.argv) > 1 and sys.argv[1] != "-h":
        success = run_health_check()
        sys.exit(0 if success else 1)

    try:
        # Verifica se existe o .env
        if not os.path.exists(".env"):
            log("Arquivo .env não encontrado. Copiando do template .env.example...")
            shutil.copy(".env.example", ".env")
            
        check_requirements()
        setup_database()
        run_server()
    except KeyboardInterrupt:
        log("Servidor encerrado pelo usuário (Ctrl+C). Até logo! 👋")
        sys.exit(0)
