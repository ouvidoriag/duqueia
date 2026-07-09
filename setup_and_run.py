import os
import sys
import subprocess
import sqlite3
import shutil

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
    if not os.path.exists("node_modules"):
        log("Pasta node_modules não encontrada. Rodando npm install...")
        try:
            subprocess.run(["npm", "install"], check=True)
        except Exception as e:
            log(f"Erro ao executar npm install: {e}. Tentando com shell=True...")
            subprocess.run("npm install", shell=True, check=True)
    else:
        log("Dependências do Node já instaladas.")

def setup_database():
    db_path = os.path.join("agent", "duque_ia.db")
    
    # 1. Cria o banco e as tabelas estruturadas se não existirem
    log("Verificando e configurando o banco de dados local SQLite...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cria tabelas estruturadas básicas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS secretarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE,
        address TEXT,
        phone TEXT,
        email TEXT,
        working_hours TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS secretaria_unidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        secretaria_id INTEGER,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT,
        working_hours TEXT,
        FOREIGN KEY(secretaria_id) REFERENCES secretarias(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        secretaria_id INTEGER,
        FOREIGN KEY(secretaria_id) REFERENCES secretarias(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duque_ia_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        category TEXT,
        content TEXT,
        embedding BLOB,
        metadata TEXT,
        keywords TEXT
    );
    """)
    
    conn.commit()
    
    # 2. Popula dados estruturados se o banco estiver vazio
    cursor.execute("SELECT COUNT(*) FROM secretarias;")
    if cursor.fetchone()[0] == 0:
        log("Banco de secretarias vazio. Populando dados iniciais...")
        # Insere as secretarias principais (SMF, SMO, SMU, SMASDH)
        secretarias_data = [
            ("Secretaria Municipal de Fazenda", "SMF", "Praça Roberto Silveira, nº 31 - Jardim 25 de Agosto", "(21) 2773-6300", "semf@duquedecaxias.rj.gov.br", "Segunda a sexta-feira, das 9h às 17h"),
            ("Secretaria Municipal de Obras e Agricultura", "SMO", "Avenida Primavera, 78 – Jardim Primavera", "(21) 2773-6150", "obraspmdc@gmail.com", "Segunda a sexta-feira, das 9h às 17h"),
            ("Secretaria Municipal de Urbanismo e Habitação", "SMU", "Alameda Bartolomeu Gusmão, 85 – Jardim Primavera", "(21) 2773-0202", "smuh@duquedecaxias.rj.gov.br", "Segunda a sexta-feira, das 9h às 17h"),
            ("Secretaria Municipal de Assistência Social e Direitos Humanos", "SMASDH", "Avenida Brigadeiro Lima e Silva, 1618 – Jardim 25 de Agosto", "(21) 2773-1066", "smasdh.caxias@gmail.com", "Segunda a sexta-feira, das 9h às 17h")
        ]
        cursor.executemany("""
        INSERT INTO secretarias (name, code, address, phone, email, working_hours)
        VALUES (?, ?, ?, ?, ?, ?);
        """, secretarias_data)
        conn.commit()

    # 3. Popula unidades físicas (CRAS) se vazias
    cursor.execute("SELECT COUNT(*) FROM secretaria_unidades;")
    if cursor.fetchone()[0] == 0:
        log("Banco de unidades físicas vazio. Populando CRAS de Duque de Caxias...")
        cras_units = [
            (4, "CRAS Jardim Primavera", "Alameda Esmeralda, 206 - Jardim Primavera, Duque de Caxias - RJ", "(21) 2773-1066", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Centenário", "Rua Doutor Manoel Reis, 120 - Centenário, Duque de Caxias - RJ", "(21) 2671-1508", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Imbariê", "Rua Feliciano Sodré, s/nº - Imbariê, Duque de Caxias - RJ", "(21) 2778-1926", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Parque Paulista", "Avenida Automóvel Clube, 120 - Parque Paulista, Duque de Caxias - RJ", "(21) 2773-5120", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Pilar", "Estrada do Pilar, s/nº - Pilar, Duque de Caxias - RJ", "(21) 2676-1520", "Segunda a sexta-feira, das 9h às 17h"),
            (4, "CRAS Xerém", "Avenida Dr. Sabino Árias, 15 - Xerém, Duque de Caxias - RJ", "(21) 2679-2236", "Segunda a sexta-feira, das 9h às 17h")
        ]
        cursor.executemany("""
        INSERT INTO secretaria_unidades (secretaria_id, name, address, phone, working_hours)
        VALUES (?, ?, ?, ?, ?);
        """, cras_units)
        conn.commit()

    conn.close()
    log("Banco de dados local SQLite configurado com sucesso!")

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
