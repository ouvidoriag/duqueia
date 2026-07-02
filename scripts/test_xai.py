"""
Teste da API xAI (Grok) - verifica modelos disponíveis
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import httpx, json

import os

XAI_API_KEY = os.environ.get("XAI_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.x.ai/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {XAI_API_KEY}"
}

# Modelos a testar (Grok usa OpenAI-compatible + /responses endpoint proprio)
MODELS = [
    "grok-4",
    "grok-4.3",
    "grok-3",
    "grok-3-mini",
    "grok-3-fast",
    "grok-3-mini-fast",
    "grok-2",
    "grok-2-mini",
    "grok-beta",
]

def test_model_responses_api(model: str) -> dict:
    """Usa o endpoint /responses (xAI nativo)"""
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": "Voce e um assistente. Responda apenas com 'GROK_OK'."},
            {"role": "user", "content": "Teste de conexao."}
        ]
    }
    try:
        r = httpx.post(f"{BASE_URL}/responses", headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # Tenta extrair o texto da resposta
            output = data.get("output", [])
            text = ""
            for item in output:
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            text += content.get("text", "")
            return {"ok": True, "text": text.strip()[:50], "status": r.status_code}
        else:
            return {"ok": False, "status": r.status_code, "error": r.text[:100]}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)[:80]}

def test_model_chat_api(model: str) -> dict:
    """Usa o endpoint /chat/completions (OpenAI-compatible)"""
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Diga apenas GROK_OK."}
        ],
        "max_tokens": 10
    }
    try:
        r = httpx.post(f"{BASE_URL}/chat/completions", headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"ok": True, "text": text.strip()[:50], "status": r.status_code}
        else:
            return {"ok": False, "status": r.status_code, "error": r.text[:100]}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)[:80]}


print("=== TESTE xAI (Grok) - /responses API ===\n")
working_responses = []
for model in MODELS:
    print(f"  {model:25} -> ", end="", flush=True)
    result = test_model_responses_api(model)
    if result["ok"]:
        print(f"[OK] {result['text']}")
        working_responses.append(model)
    else:
        print(f"[FAIL] {result.get('status', '?')} - {result.get('error', '')[:70]}")

print("\n=== TESTE xAI (Grok) - /chat/completions API (OpenAI-compat) ===\n")
working_chat = []
for model in MODELS:
    print(f"  {model:25} -> ", end="", flush=True)
    result = test_model_chat_api(model)
    if result["ok"]:
        print(f"[OK] {result['text']}")
        working_chat.append(model)
    else:
        print(f"[FAIL] {result.get('status', '?')} - {result.get('error', '')[:70]}")

print("\n=== RESUMO ===")
print(f"[/responses]       Funcionando: {working_responses}")
print(f"[/chat/completions] Funcionando: {working_chat}")
