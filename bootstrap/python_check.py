import os
import sys
import importlib.util

SUPPORTED_PYTHON_VERSIONS = [(3, 10), (3, 11), (3, 12)]

def log(msg):
    print(f"\n🚀 [DUQUE IA SETUP] {msg}")

def check_python_environment():
    """Valida a versão do Python e verifica se a execução está em ambiente virtual (.venv)."""
    version = sys.version_info
    log(f"Versão do Python detectada: {version.major}.{version.minor}.{version.micro}")

    # 1. Validação de versão mínima
    if version < (3, 10):
        raise RuntimeError(
            f"Python {version.major}.{version.minor} não é suportado. "
            "O Duque IA requer Python 3.10, 3.11 ou 3.12 (Versão recomendada: 3.12)."
        )

    # 2. Recomendação para Python 3.13+
    if version >= (3, 13):
        log("⚠️  ATENÇÃO: Você está executando o Python 3.13+.\n"
            "   Algumas bibliotecas de IA/Embeddings podem apresentar falhas de compilação ou falta de rodas binárias.\n"
            "   Versões suportadas oficialmente em produção: Python 3.11 e 3.12.")

    # 3. Detecção de ambiente virtual (.venv)
    in_venv = (sys.prefix != sys.base_prefix) or hasattr(sys, "real_prefix")
    if not in_venv:
        log("⚠️  AVISO: Ambiente virtual (.venv) não detectado. Você está usando o Python global do sistema.")
        log("   Para evitar conflitos no Linux/Ubuntu (PEP 668):\n"
            "   1. sudo apt install python3-venv python3-full\n"
            "   2. python3 -m venv .venv\n"
            "   3. source .venv/bin/activate\n"
            "   4. pip install -r requirements.txt\n")

def check_requirements():
    """Verifica se os pacotes Python obrigatórios estão disponíveis no ambiente via importlib."""
    check_python_environment()

    log("Verificando dependências do Python via importlib...")
    required_modules = [
        ("dotenv", "python-dotenv"),
        ("google.genai", "google-genai"),
        ("google.generativeai", "google-generativeai"),
        ("requests", "requests"),
        ("pandas", "pandas"),
        ("yaml", "PyYAML"),
        ("pypdf", "pypdf"),
        ("openpyxl", "openpyxl"),
        ("gtts", "gTTS")
    ]

    missing_packages = []
    for mod_name, pkg_name in required_modules:
        if importlib.util.find_spec(mod_name) is None:
            missing_packages.append(pkg_name)

    if missing_packages:
        log(f"⚠️  ATENÇÃO: As seguintes dependências Python não foram encontradas no ambiente ({sys.executable}):")
        for pkg in missing_packages:
            log(f"   - {pkg}")
        log("\nInstale-as executando: pip install -r requirements.txt\n")
    else:
        log("✅ Todas as dependências essenciais do Python foram verificadas com sucesso!")
