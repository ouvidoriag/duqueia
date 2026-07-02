"""
Teste de integracao do LLMRouter - verifica fallback Gemini / Groq
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()

from utils.llm_router import get_router

router = get_router()

print("=== TESTE DO LLM ROUTER (Gemini + Groq) ===\n")

# Teste 1: Resposta geral (Gemini first)
print("--- Teste 1: generate_response (Gemini primeiro) ---")
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

# Teste 2: Triagem (Groq first)
print("--- Teste 2: generate_triage (Groq primeiro) ---")
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

# Teste 3: RAG (Gemini first com interaction)
print("--- Teste 3: generate_rag_response (Gemini RAG primeiro) ---")
try:
    text, new_id, provider = router.generate_rag_response(
        prompt="Onde fica a Prefeitura de Duque de Caxias?",
        system_instruction="Voce e o assistente DUQUE IA. Responda sobre a prefeitura de Duque de Caxias."
    )
    print(f"  Provedor usado: {provider}")
    print(f"  Interaction ID: {str(new_id)[:30] if new_id else 'None (Groq nao usa IDs)'}")
    print(f"  Resposta: {text[:100]}")
except Exception as e:
    print(f"  FALHOU: {e}")

print()
print("=== ESTATISTICAS DE USO ===")
stats = router.get_stats()
for k, v in stats.items():
    print(f"  {k}: {v}")
