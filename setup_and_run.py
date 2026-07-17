import os
import sys
import subprocess
import sqlite3
import shutil
import time

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def log(msg):
    print(f"\n🚀 [DUQUE IA SETUP] {msg}")

def check_requirements():
    # Detecta e avisa sobre versão do Python
    version = sys.version_info
    log(f"Versão do Python detectada: {version.major}.{version.minor}.{version.micro}")
    if version.major == 3 and version.minor >= 13:
        log("⚠️  ATENÇÃO: Você está executando uma versão recente do Python (>= 3.13). \n"
            "   Algumas dependências pesadas de IA (como torch, sentence-transformers, faiss ou onnxruntime) \n"
            "   podem apresentar incompatibilidades ou falhas de compilação. \n"
            "   Recomendamos o uso do Python 3.11.x ou 3.12.x para máxima estabilidade em produção.")

    log("Verificando dependências do Python (pip)...")
    try:
        # Testa se o pip está disponível
        subprocess.run([sys.executable, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("Módulo pip não encontrado. Tentando instalar ensurepip...")
        try:
            subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=True)
        except Exception as e:
            log(f"Aviso: Não foi possível instalar o pip automaticamente via ensurepip: {e}")

    try:
        log("Instalando pacotes do requirements.txt via sys.executable...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        log("Requisitos do Python instalados com sucesso!")
    except Exception as e:
        log(f"Aviso: Falha ao rodar pip install: {e}. Garanta as dependências manualmente.")

    log("Verificando dependências do Node.js (npm)...")
    import json
    has_dependencies = False
    if os.path.exists("package.json"):
        try:
            with open("package.json", "r", encoding="utf-8") as f:
                pkg = json.load(f)
                if pkg.get("dependencies"):
                    has_dependencies = True
        except Exception:
            pass

    if has_dependencies:
        if not os.path.exists("node_modules"):
            log("Pasta node_modules não encontrada e dependências detectadas. Rodando npm install...")
            try:
                subprocess.run(["npm", "install"], check=True)
            except Exception as e:
                log(f"Erro ao executar npm install: {e}. Tentando com shell=True...")
                subprocess.run("npm install", shell=True, check=True)
        else:
            log("Dependências do Node já instaladas.")
    else:
        log("Nenhuma dependência externa configurada no package.json. Pulando npm install.")

def init_db(db_path, schema_file, indexes_file=None, db_name=""):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    log(f"Configurando banco de dados: {db_name}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA temp_store = MEMORY;")
    cursor.execute("PRAGMA cache_size = -20000;")
    
    # Executa DDLs do Schema
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
            
    # Executa DDLs dos Índices
    if indexes_file and os.path.exists(indexes_file):
        with open(indexes_file, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
            
    cursor.execute("PRAGMA integrity_check;")
    status = cursor.fetchone()[0]
    if status != "ok":
        log(f"  ⚠️ AVISO {db_name}: Integridade falhou ({status})")
        
    t0_mig = time.time()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        execution_time_ms INTEGER,
        status TEXT,
        checksum TEXT
    );
    """)
    cursor.execute("SELECT MAX(version) FROM schema_version;")
    v_row = cursor.fetchone()
    current_version = v_row[0] if v_row and v_row[0] is not None else 0
    if current_version < 1:
        elapsed_ms = int((time.time() - t0_mig) * 1000)
        cursor.execute("INSERT INTO schema_version (version) VALUES (1);")
        cursor.execute(
            "INSERT INTO schema_migrations (version, execution_time_ms, status, checksum) VALUES (?, ?, ?, ?)",
            (1, elapsed_ms, "SUCCESS", "v1_baseline_hash_init")
        )
        conn.commit()
        log(f"  -> Versão de schema inicializada: Versão 1 (Baseline)")
    else:
        log(f"  -> Versão de schema atual: Versão {current_version}")
        
    conn.commit()
    return conn, cursor

def setup_database():
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from config.settings import DATABASE_MAIN, DATABASE_VECTOR, DATABASE_CACHE, DATABASE_TELEMETRY

    db_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database")

    # ==============================================================================
    # 1. SETUP DO BANCO PRINCIPAL (RELACIONAL) - main.db
    # ==============================================================================
    schema_main = os.path.join(db_dir, "schema_main.sql")
    indexes_main = os.path.join(db_dir, "indexes_main.sql")
    conn_main, cur_main = init_db(DATABASE_MAIN, schema_main, indexes_main, "Principal Relacional (main.db)")

    # Popula dados estruturados iniciais se main.db estiver vazio
    cur_main.execute("SELECT COUNT(*) FROM secretarias;")
    if cur_main.fetchone()[0] == 0:
        log("Banco de secretarias vazio. Populando dados iniciais...")
        secretarias_data = [
            ("Secretaria Municipal de Fazenda", "SMF", "Praça Roberto Silveira, nº 31 - Jardim 25 de Agosto", "(21) 2773-6300", "semf@duquedecaxias.rj.gov.br", "Segunda a sexta-feira, das 9h às 17h"),
            ("Secretaria Municipal de Obras e Agricultura", "SMO", "Avenida Primavera, 78 – Jardim Primavera", "(21) 2773-6150", "obraspmdc@gmail.com", "Segunda a sexta-feira, das 9h às 17h"),
            ("Secretaria Municipal de Urbanismo e Habitação", "SMU", "Alameda Bartolomeu Gusmão, 85 – Jardim Primavera", "(21) 2773-0202", "smuh@duquedecaxias.rj.gov.br", "Segunda a sexta-feira, das 9h às 17h"),
            ("Secretaria Municipal de Assistência Social e Direitos Humanos", "SMASDH", "Avenida Brigadeiro Lima e Silva, 1618 – Jardim 25 de Agosto", "(21) 2773-1066", "smasdh.caxias@gmail.com", "Segunda a sexta-feira, das 9h às 17h")
        ]
        cur_main.executemany("""
        INSERT INTO secretarias (name, code, address, phone, email, working_hours)
        VALUES (?, ?, ?, ?, ?, ?);
        """, secretarias_data)
        conn_main.commit()

    cur_main.execute("SELECT COUNT(*) FROM secretaria_unidades;")
    if cur_main.fetchone()[0] == 0:
        log("Banco de unidades físicas vazio. Populando CRAS de Duque de Caxias...")
        cras_units = [
            (4, "CRAS Jardim Primavera", "Alameda Esmeralda, 206 - Jardim Primavera, Duque de Caxias - RJ", "(21) 2773-1066", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Centenário", "Rua Doutor Manoel Reis, 120 - Centenário, Duque de Caxias - RJ", "(21) 2671-1508", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Imbariê", "Rua Feliciano Sodré, s/nº - Imbariê, Duque de Caxias - RJ", "(21) 2778-1926", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Parque Paulista", "Avenida Automóvel Clube, 120 - Parque Paulista, Duque de Caxias - RJ", "(21) 2773-5120", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Pilar", "Estrada do Pilar, s/nº - Pilar, Duque de Caxias - RJ", "(21) 2676-1520", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Xerém", "Avenida Dr. Sabino Árias, 15 - Xerém, Duque de Caxias - RJ", "(21) 2679-2236", "Segunda a sexta-feira, das 9h às 17h")
        ]
        cur_main.executemany("""
        INSERT INTO secretaria_unidades (secretaria_id, name, address, phone, working_hours)
        VALUES (?, ?, ?, ?, ?);
        """, cras_units)
        conn_main.commit()
    conn_main.close()

    # ==============================================================================
    # 2. SETUP DO BANCO VETORIAL (vector.db)
    # ==============================================================================
    schema_vector = os.path.join(db_dir, "schema_vector.sql")
    indexes_vector = os.path.join(db_dir, "indexes_vector.sql")
    conn_vector, cur_vector = init_db(DATABASE_VECTOR, schema_vector, indexes_vector, "Busca Semântica (vector.db)")
    conn_vector.close()

    # ==============================================================================
    # 3. SETUP DO BANCO DE CACHE (cache.db)
    # ==============================================================================
    schema_cache = os.path.join(db_dir, "schema_cache.sql")
    conn_cache, cur_cache = init_db(DATABASE_CACHE, schema_cache, None, "Cache de Triagem (cache.db)")
    conn_cache.close()

    # ==============================================================================
    # 4. SETUP DO BANCO DE TELEMETRIA (telemetry.db)
    # ==============================================================================
    schema_telemetry = os.path.join(db_dir, "schema_telemetry.sql")
    conn_telemetry, cur_telemetry = init_db(DATABASE_TELEMETRY, schema_telemetry, None, "Telemetria e Chats (telemetry.db)")
    conn_telemetry.close()
    
    log("Todos os 4 bancos de dados SQLite (main, vector, cache, telemetry) foram inicializados e validados com sucesso!")

def run_server():
    log("Iniciando o Duque IA Chat Server...")
    # Executa o node server.js sem shell=True por padrão
    try:
        subprocess.run(["node", "server.js"], check=True)
    except Exception as e:
        log(f"Falha ao iniciar o Node diretamente: {e}. Tentando com shell=True...")
        subprocess.run("node server.js", shell=True)

if __name__ == "__main__":
    # Verifica se existe o .env
    if not os.path.exists(".env"):
        log("Arquivo .env não encontrado. Copiando do template .env.example...")
        shutil.copy(".env.example", ".env")
        
    check_requirements()
    setup_database()
    run_server()
