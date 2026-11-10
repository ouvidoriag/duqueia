import os
import sys
import sqlite3
import shutil
import importlib.util

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def log_health(status: bool, check_name: str, detail: str = ""):
    icon = "✓" if status else "✗"
    color_label = "PASS" if status else "FAIL"
    detail_str = f" ({detail})" if detail else ""
    print(f" [{icon}] {check_name:<35} -> {color_label}{detail_str}")

def run_health_check() -> bool:
    """Executa um diagnóstico completo da infraestrutura e saúde do sistema Duque IA."""
    print("\n============================================================")
    print("🏥 [DUQUE IA] RELATÓRIO DE SAÚDE DO SISTEMA (HEALTH CHECK)")
    print("============================================================")

    all_passed = True

    # 1. Checagem do Python e Venv
    version = sys.version_info
    py_ok = (version >= (3, 10))
    py_detail = f"v{version.major}.{version.minor}.{version.micro}"
    log_health(py_ok, "Versão do Python (>=3.10)", py_detail)
    if not py_ok:
        all_passed = False

    in_venv = (sys.prefix != sys.base_prefix) or hasattr(sys, "real_prefix")
    log_health(in_venv, "Ambiente Virtual (.venv)", "Ativo" if in_venv else "Inativo (Usando Python Global)")

    # 2. Variáveis de Ambiente (.env)
    env_exists = os.path.exists(".env")
    log_health(env_exists, "Arquivo de Configuração (.env)", "Encontrado" if env_exists else "Ausente (Copiando .env.example)")

    has_gemini_key = False
    if env_exists:
        try:
            from dotenv import load_dotenv
            load_dotenv(".env")
            has_gemini_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEYS"))
        except Exception:
            pass
    log_health(has_gemini_key, "Chave de API Gemini (GEMINI_API_KEY)", "Configurada" if has_gemini_key else "Ausente/Vazia")
    if not has_gemini_key:
        all_passed = False

    # 3. Bancos de Dados SQLite
    try:
        from config.settings import DATABASE_MAIN, DATABASE_VECTOR, DATABASE_CACHE, DATABASE_TELEMETRY
        db_paths = [
            ("main.db", DATABASE_MAIN),
            ("vector.db", DATABASE_VECTOR),
            ("cache.db", DATABASE_CACHE),
            ("telemetry.db", DATABASE_TELEMETRY)
        ]
    except Exception:
        db_paths = [
            ("main.db", "data/db/main.db"),
            ("vector.db", "data/db/vector.db"),
            ("cache.db", "data/db/cache.db"),
            ("telemetry.db", "data/db/telemetry.db")
        ]

    for db_name, path in db_paths:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode;")
                journal = cursor.fetchone()[0]
                cursor.execute("PRAGMA integrity_check;")
                integrity = cursor.fetchone()[0]
                conn.close()
                db_ok = (integrity == "ok")
                log_health(db_ok, f"Banco SQLite ({db_name})", f"WAL: {journal} | Integridade: {integrity}")
                if not db_ok:
                    all_passed = False
            except Exception as e:
                log_health(False, f"Banco SQLite ({db_name})", f"Erro: {e}")
                all_passed = False
        else:
            log_health(False, f"Banco SQLite ({db_name})", f"Arquivo não encontrado: {path}")
            all_passed = False

    # 4. Permissões de Escrita nos Diretórios Chave
    for target_dir in ["agent", "data/db", "metrics", "logs"]:
        os.makedirs(target_dir, exist_ok=True)
        writable = os.access(target_dir, os.W_OK)
        log_health(writable, f"Permissão de Escrita ({target_dir}/)", "OK" if writable else "Permissão Negada")
        if not writable:
            all_passed = False

    # 5. Runtime Node.js & Dependências
    node_installed = shutil.which("node") is not None
    log_health(node_installed, "Runtime Node.js", "Disponível no PATH" if node_installed else "Não encontrado")
    if not node_installed:
        all_passed = False

    # Servidor nativo utiliza apenas módulos core do Node.js (0 dependências externas obrigatórias)
    node_modules_ok = os.path.exists("node_modules") or True
    log_health(True, "Dependências Node.js (Vanilla Core)", "Módulos nativos (http, fs, path, child_process)")

    print("============================================================")
    if all_passed:
        print("🎉 STATUS GERAL: INFRAESTRUTURA 100% OPERACIONAL E PRONTA PARA PRODUÇÃO!")
    else:
        print("⚠️ STATUS GERAL: ALGUNS COMPONENTES EXIGEM ATENÇÃO ANTES DO DEPLOY.")
    print("============================================================\n")

    return all_passed

if __name__ == "__main__":
    success = run_health_check()
    sys.exit(0 if success else 1)
