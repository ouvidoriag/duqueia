import os
import sys
import subprocess
import shutil
import json

def log(msg):
    print(f"\n🚀 [DUQUE IA SETUP] {msg}")

def check_node_dependencies():
    """Valida se o runtime Node.js está presente no sistema e verifica a existência de node_modules."""
    log("Verificando runtime e dependências do Node.js (npm)...")

    # 1. Verifica se o executável 'node' está no PATH
    if shutil.which("node") is None:
        raise RuntimeError(
            "Node.js não foi encontrado no PATH do sistema. "
            "Por favor, instale o Node.js v18 ou superior: https://nodejs.org/"
        )

    has_dependencies = False
    if os.path.exists("package.json"):
        try:
            with open("package.json", "r", encoding="utf-8") as f:
                pkg = json.load(f)
                if pkg.get("dependencies"):
                    has_dependencies = True
        except Exception as e:
            log(f"Aviso ao ler package.json: {e}")

    if has_dependencies:
        if not os.path.exists("node_modules"):
            log("⚠️ Pasta node_modules não encontrada. Executando npm install para instalar dependências do gateway Node...")
            try:
                subprocess.run(["npm", "install"], check=True)
                log("✅ Dependências do Node instaladas com sucesso!")
            except Exception as e:
                log(f"⚠️ Erro ao executar npm install diretamente: {e}. Tentando via shell...")
                try:
                    subprocess.run("npm install", shell=True, check=True)
                except Exception as ex:
                    log(f"❌ Falha ao instalar dependências Node: {ex}. Execute 'npm install' manualmente.")
        else:
            log("✅ Dependências do Node (node_modules) já instaladas.")
    else:
        log("✅ Nenhuma dependência externa declarada em package.json. Gateway pronto para iniciar.")

def run_server():
    """Inicia o servidor HTTP Gateway Node.js (server.js)."""
    check_node_dependencies()
    log("Iniciando o Duque IA Chat Server...")
    try:
        subprocess.run(["node", "server.js"], check=True)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log(f"Falha ao iniciar o Node diretamente: {e}. Tentando com shell=True...")
        try:
            subprocess.run("node server.js", shell=True)
        except KeyboardInterrupt:
            raise
