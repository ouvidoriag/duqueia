import os
import sys
import json
import io

# Garante que a saída use UTF-8 no Windows/Pipe de forma segura
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

# Carrega as configurações do ambiente (.env)
load_dotenv()

# Garante que a RAIZ do projeto seja o PRIMEIRO item do sys.path.
# Isso é crítico: quando o Python executa agent/main.py diretamente,
# ele insere o diretório 'agent/' como sys.path[0], o que quebra
# os imports 'from agent.xxx import ...' dentro dos módulos filhos.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_AGENT_DIR = os.path.abspath(os.path.dirname(__file__))

# Remove o diretório 'agent/' do path se estiver lá (inserido automaticamente pelo Python)
while _AGENT_DIR in sys.path:
    sys.path.remove(_AGENT_DIR)

# Insere a raiz do projeto na primeira posição
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Importa o agente orquestrador principal
from agent.agent import DuqueIAAgent

def main():
    # Detecta se está rodando em modo interativo (terminal) ou via pipe (server.js / testes)
    _is_tty = sys.stdin.isatty()

    if _is_tty:
        print("==========================================================")
        print("      INICIALIZANDO O DUQUE IA - ATENDIMENTO MUNICIPAL     ")
        print("==========================================================")

    agent = DuqueIAAgent()
    db_path = agent.db_path

    if not os.path.exists(db_path):
        if _is_tty:
            print(f"[Aviso] Banco de dados em '{db_path}' não encontrado.")
        return

    if _is_tty:
        print("Conectado ao Banco de Conhecimento.")
        print("Triagem: ATIVADA | Digite 'sair' para encerrar | 'json' para ver resposta bruta")
        print("----------------------------------------------------------\n")

    conversation_id = None
    # Em modo pipe, começa com JSON ativado por padrão
    show_json = not _is_tty

    while True:
        try:
            query = input("" if not _is_tty else "Munícipe: ")
            if not query.strip():
                continue
            cmd = query.strip().lower()
            if cmd == "sair":
                if _is_tty:
                    print("Encerrando o DUQUE IA. Até logo!")
                break
            if cmd == "json":
                show_json = not show_json
                if _is_tty:
                    print(f"[Modo JSON: {'ATIVADO' if show_json else 'DESATIVADO'}]")
                continue
            if cmd == "nova sessao":
                conversation_id = None
                if _is_tty:
                    print("[Nova sessão iniciada]")
                continue

            raw = agent.respond(query, use_triage=True, conversation_id=conversation_id)

            try:
                data = json.loads(raw)
                conversation_id = data.get("conversation_id", conversation_id)

                if show_json:
                    # Em modo pipe: saída limpa para facilitar parsing pelo servidor
                    print(raw, flush=True)
                else:
                    answer = data.get("answer", "")
                    intent = data.get("intent_detected", "?")
                    confidence = data.get("confidence", 0)
                    total_ms = data.get("metrics", {}).get("total_time_ms", 0)

                    print(f"\nDUQUE IA: {answer}")
                    print(f"\n[intent={intent} | confiança={confidence:.0%} | {total_ms:.0f}ms | sessão={str(conversation_id)[:20]}...]")

            except Exception:
                print(raw, flush=True)

            if _is_tty:
                print()

        except (KeyboardInterrupt, EOFError):
            if _is_tty:
                print("\nEncerrando o DUQUE IA. Até logo!")
            break

if __name__ == "__main__":
    main()
