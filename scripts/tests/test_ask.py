"""
==============================================================================
            DUQUE IA - SCRIPT DE TESTE RAPIDO (test_ask.py)
==============================================================================
Permite testar o agente de tres formas:

  1. Pergunta unica (via argumento):
       python scripts/tests/test_ask.py "Qual o CNPJ da Prefeitura?"

  2. Modo interativo (sem argumentos):
       python scripts/tests/test_ask.py

  3. Bateria de perguntas automaticas:
       python scripts/tests/test_ask.py --batch

Saida: exibe resposta JSON formatada + metricas de execucao.
==============================================================================
"""

import io
import os
import sys
import json
import time
import sqlite3

# --- Forca saida UTF-8 no Windows (evita UnicodeEncodeError no cp1252) ---
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Garante acesso a raiz do projeto (DUQUEIA/)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

from agent.main import DuqueIAAgent

# =============================================================================
# BATERIA DE PERGUNTAS PADRAO PARA TESTES AUTOMATICOS
# =============================================================================
PERGUNTAS_PADRAO = [
    "Qual o nome do prefeito de Duque de Caxias?",
    "Quais sao os bairros de Duque de Caxias?",
    "Como faco para pagar o IPTU?",
    "Quais secretarias fazem parte da administracao municipal?",
    "Qual a populacao de Duque de Caxias?",
    "Onde fica a prefeitura de Duque de Caxias?",
    "Como entrar em contato com a ouvidoria?",
    "Quais servicos o site da prefeitura oferece?",
    "Qual o PIB de Duque de Caxias?",
    "Existe transporte publico no municipio?",
]


# =============================================================================
# INSPECIONAR O BANCO DE DADOS
# =============================================================================
def inspecionar_banco(db_path: str):
    """Mostra resumo do que esta no banco de dados."""
    if not os.path.exists(db_path):
        print(f"[ERRO] Banco de dados nao encontrado: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM duque_ia_chunks")
    total = cur.fetchone()[0]

    cur.execute("SELECT category, COUNT(*) as n FROM duque_ia_chunks GROUP BY category ORDER BY n DESC")
    categorias = cur.fetchall()

    cur.execute("SELECT source, content FROM duque_ia_chunks LIMIT 3")
    amostras = cur.fetchall()

    conn.close()

    print("\n" + "=" * 70)
    print("        DUQUE IA --- INSPECAO DO BANCO DE CONHECIMENTO")
    print("=" * 70)
    print(f"  Total de chunks indexados : {total}")
    print(f"  Caminho do banco          : {db_path}")
    print("\n  Chunks por categoria:")
    for cat, n in categorias:
        bar = "#" * min(n, 40)
        print(f"    {cat:<22} {bar} ({n})")

    print("\n  Amostras de conteudo:")
    for i, (src, content) in enumerate(amostras, 1):
        preview = content[:100].replace("\n", " ").strip()
        print(f"    [{i}] {src}")
        print(f"        \"{preview}...\"")
    print("=" * 70 + "\n")


# =============================================================================
# FORMATAR RESPOSTA NA TELA
# =============================================================================
def exibir_resposta(pergunta: str, response_json: str, tempo: float):
    """Imprime a resposta de forma visual e legivel."""
    print("\n" + "-" * 70)
    print(f"  PERGUNTA : {pergunta}")
    print("-" * 70)

    try:
        data = json.loads(response_json)
        answer    = data.get("answer", "---")
        sources   = data.get("sources", [])
        confidence = data.get("confidence", 0.0)

        # Indicador textual de confianca
        if confidence >= 0.8:
            nivel = "[ALTA]"
        elif confidence >= 0.5:
            nivel = "[MEDIA]"
        else:
            nivel = "[BAIXA]"

        print(f"\n  RESPOSTA :\n")
        for line in answer.split("\n"):
            print(f"     {line}")

        print(f"\n  {nivel} Confianca : {confidence:.0%}")
        print(f"  Tempo        : {tempo * 1000:.0f}ms")

        if sources:
            print(f"\n  Fontes :")
            for s in sources:
                print(f"      * {s}")
        else:
            print(f"\n  Fontes : Nenhuma fonte identificada")

    except json.JSONDecodeError:
        print(f"  Resposta bruta: {response_json}")

    print("-" * 70)


# =============================================================================
# MODO BATERIA AUTOMATICA
# =============================================================================
def modo_bateria(agent: DuqueIAAgent):
    """Executa todas as perguntas padrao automaticamente."""
    print("\n" + "=" * 70)
    print("      DUQUE IA --- BATERIA DE TESTES AUTOMATICOS")
    print("=" * 70)

    resultados = []
    for i, pergunta in enumerate(PERGUNTAS_PADRAO, 1):
        print(f"\n  [{i:02d}/{len(PERGUNTAS_PADRAO)}] {pergunta}")
        t0 = time.time()
        resp = agent.respond(pergunta)
        elapsed = time.time() - t0

        try:
            data = json.loads(resp)
            conf = data.get("confidence", 0.0)
            respondeu = conf > 0.0
        except Exception:
            conf = 0.0
            respondeu = False

        status = "PASS" if respondeu else "SEM RESPOSTA"
        print(f"       -> Confianca: {conf:.0%} | Tempo: {elapsed * 1000:.0f}ms | {status}")
        resultados.append({
            "pergunta": pergunta,
            "confianca": conf,
            "tempo_ms": elapsed * 1000,
            "status": status
        })

    # Resumo final
    total = len(resultados)
    respostas = sum(1 for r in resultados if r["status"] == "PASS")
    print("\n" + "=" * 70)
    print(f"  RESULTADO FINAL   : {respostas}/{total} perguntas respondidas ({respostas/total:.0%})")
    print(f"  Confianca media   : {sum(r['confianca'] for r in resultados)/total:.0%}")
    print(f"  Latencia media    : {sum(r['tempo_ms'] for r in resultados)/total:.0f}ms")
    print("=" * 70)

    # Salva relatorio JSON
    relatorio_path = os.path.join(ROOT, "metrics", "batch_test_results.json")
    os.makedirs(os.path.dirname(relatorio_path), exist_ok=True)
    with open(relatorio_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\n  Relatorio salvo em: {relatorio_path}")


# =============================================================================
# MODO INTERATIVO (CHAT NO TERMINAL)
# =============================================================================
def modo_interativo(agent: DuqueIAAgent):
    """Loop interativo de perguntas e respostas no terminal."""
    print("\n" + "=" * 70)
    print("      DUQUE IA --- MODO INTERATIVO DE PERGUNTAS")
    print("=" * 70)
    print("  Digite sua pergunta sobre Duque de Caxias.")
    print("  Comandos especiais:")
    print("    'info'  -> Inspeciona o banco de dados")
    print("    'batch' -> Executa bateria de perguntas automaticas")
    print("    'sair'  -> Encerra o chat")
    print("=" * 70)

    while True:
        try:
            pergunta = input("\n  Voce: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Encerrando o DUQUE IA. Ate logo!")
            break

        if not pergunta:
            continue

        if pergunta.lower() == "sair":
            print("  Encerrando o DUQUE IA. Ate logo!")
            break
        elif pergunta.lower() == "info":
            inspecionar_banco(agent.db_vector)
            continue
        elif pergunta.lower() == "batch":
            modo_bateria(agent)
            continue

        t0 = time.time()
        resposta = agent.respond(pergunta)
        elapsed = time.time() - t0

        exibir_resposta(pergunta, resposta, elapsed)


# =============================================================================
# PONTO DE ENTRADA PRINCIPAL
# =============================================================================
def main():
    print("\n" + "=" * 70)
    print("            DUQUE IA --- SISTEMA RAG MUNICIPAL")
    print("               Prefeitura de Duque de Caxias")
    print("=" * 70)

    from config.settings import DATABASE_MAIN, DATABASE_VECTOR
    # Inicializa o agente
    agent = DuqueIAAgent(db_path=DATABASE_MAIN)

    # Inspeciona o banco
    inspecionar_banco(DATABASE_VECTOR)

    # Verifica argumentos de linha de comando
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--batch":
            modo_bateria(agent)
        else:
            # Pergunta unica passada como argumento
            pergunta = " ".join(sys.argv[1:])
            t0 = time.time()
            resposta = agent.respond(pergunta)
            elapsed = time.time() - t0
            exibir_resposta(pergunta, resposta, elapsed)
    else:
        # Modo interativo
        modo_interativo(agent)


if __name__ == "__main__":
    main()
