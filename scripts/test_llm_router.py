"""
Teste de integração do LLMRouter (Exclusivo Gemini)
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()

from utils.llm_router import get_router

router = get_router()

print("=== TESTE DO LLM ROUTER (Exclusivo Gemini) ===\n")

# Teste 1: Resposta geral (Gemini)
print("--- Teste 1: generate_response (Gemini 2.5 Flash) ---")
try:
    text, provider = router.generate_response(
        prompt="Diga apenas: ROUTER_OK",
        system_instruction="Voce e um assistente. Responda apenas com o que for pedido."
    )
    print(f"  Provedor usado: {provider}")
    print(f"  Resposta: {text[:60]}")
except Exception as e:
    print(f"  FALHOU: {e}")

print()

# Teste 2: Triagem (Gemini Lite)
print("--- Teste 2: generate_triage (Gemini 3.1 Flash Lite) ---")
try:
    text, provider = router.generate_triage(
        prompt='Classifique esta mensagem e retorne apenas "SAUDACAO": "ola"',
        system_instruction="Classificador de intencoes. Responda apenas com a classificacao."
    )
    print(f"  Provedor usado: {provider}")
    print(f"  Resposta: {text[:80]}")
except Exception as e:
    print(f"  FALHOU: {e}")

print()

# Teste 3: RAG (Gemini com Interaction ID)
print("--- Teste 3: generate_rag_response (Gemini RAG) ---")
try:
    text, new_id, provider = router.generate_rag_response(
        prompt="Onde fica a Prefeitura de Duque de Caxias?",
        system_instruction="Voce e o assistente DUQUE IA. Responda sobre a prefeitura de Duque de Caxias."
    )
    print(f"  Provedor usado: {provider}")
    print(f"  Interaction ID: {str(new_id)[:30] if new_id else 'Nenhum'}")
    print(f"  Resposta: {text[:100]}")
except Exception as e:
    print(f"  FALHOU: {e}")

print()
print("=== ESTATISTICAS DE USO ===")
stats = router.get_stats()
for k, v in stats.items():
    print(f"  {k}: {v}")

