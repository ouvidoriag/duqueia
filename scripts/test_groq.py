"""
Teste da API Groq - Diagnostico completo de modelos disponiveis
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sys, os
sys.path.append(os.path.abspath("."))

from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_API_KEY_HERE")

client = Groq(api_key=GROQ_API_KEY)

# Modelos mais relevantes para o projeto
MODELS_TO_TEST = [
    # Llama (rápidos e gratuitos)
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3.2-3b-preview",
    "llama-3.2-1b-preview",
    # Gemma
    "gemma2-9b-it",
    # Mistral
    "mistral-saba-24b",
    # Outros
    "qwen-qwq-32b",
]

PROMPT = "Diga apenas 'GROQ_OK' se você está funcionando. Nada mais."

print(f"Testando {len(MODELS_TO_TEST)} modelos na Groq...\n")
working = []
failed = []

for model in MODELS_TO_TEST:
    try:
        print(f"  {model:35} -> ", end="", flush=True)
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": PROMPT}],
            model=model,
            max_tokens=20,
            temperature=0
        )
        text = resp.choices[0].message.content.strip().replace("\n", " ")
        tokens = resp.usage.total_tokens if resp.usage else "?"
        print(f"[OK] Resposta: {text[:30]} | Tokens: {tokens}")
        working.append(model)
    except Exception as e:
        err = str(e)[:100].replace("\n", " ")
        print(f"[FAIL] {err}")
        failed.append(model)

print(f"\n=== RESUMO ===")
print(f"[OK] Funcionando ({len(working)}): {working}")
print(f"[FAIL] Falhou ({len(failed)}): {failed}")
