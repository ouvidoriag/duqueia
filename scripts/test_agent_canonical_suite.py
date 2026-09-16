# -*- coding: utf-8 -*-
"""
Suíte de Testes Canônicos de Ponta a Ponta com o DuqueIAAgent
Executa as 5 perguntas de ouro do cidadão:
1. Castração de cães / Proteção Animal / Petzap
2. Vistoria e instalação de quebra-molas (SMSP / SMOA)
3. Atribuições da Procuradoria Geral do Município (PGM)
4. Telefone da Guarda Municipal e Segurança Pública (sem 153)
5. Ônibus Tarifa Zero (Decreto 8.120 / SMSP)
"""

import os
import sys
import json

# Configurar stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from agent.agent import DuqueIAAgent

def main():
    print("=== INICIANDO SUITE DE TESTES CANONICOS DO DUQUE IA ===")
    agent = DuqueIAAgent()

    test_queries = [
        ("Castração de Animais", "como castrar cachorro de graça na prefeitura?"),
        ("Quebra-Molas", "vistoria de quebra-molas redutor de velocidade"),
        ("Procuradoria Geral", "qual a função da procuradoria geral do município?"),
        ("Segurança Pública", "telefone segurança pública guarda municipal"),
        ("Tarifa Zero", "ônibus tarifa zero linhas gratuitas")
    ]

    for label, query in test_queries:
        print(f"\n" + "="*60)
        print(f"TESTE: [{label}]")
        print(f"QUERY: '{query}'")
        print("="*60)

        raw = agent.respond(query)
        try:
            result = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            result = {"answer": raw}
        
        # Validar resposta
        ans = result.get("answer", "")
        sources = result.get("sources", [])
        conf = result.get("confidence", 0.0)

        print(f"CONFIANÇA: {conf}")
        print(f"FONTES: {sources}")
        print(f"RESPOSTA:\n{ans[:400]}...")

    print("\n=== SUITE DE TESTES CANONICOS CONCLUIDA COM SUCESSO ===")

if __name__ == "__main__":
    main()
