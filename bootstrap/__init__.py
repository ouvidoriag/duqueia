"""
Módulo de Bootstrap do Duque IA.
Fornece utilitários de validação de ambiente, verificação de dependências,
diagnóstico de saúde da infraestrutura, inicialização de bancos de dados SQLite e gerenciamento do runtime Node.js.
"""

from .python_check import check_python_environment, check_requirements
from .database_init import setup_database, init_db
from .server_runner import check_node_dependencies, run_server
from .health import run_health_check

__all__ = [
    "check_python_environment",
    "check_requirements",
    "setup_database",
    "init_db",
    "check_node_dependencies",
    "run_server",
    "run_health_check"
]
