import os
import sys
import requests
import json
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def test_model(model_name, key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": "Diga 'OK'."}]}]
    }
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            try:
                text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return "SUPORTADO ✅", f"Retornou: '{text}'"
            except Exception:
                return "SUPORTADO ✅", "Resposta vazia."
        else:
            return f"NÃO SUPORTADO (Erro {response.status_code}) ❌", response.text.strip().replace("\n", " ")
    except Exception as e:
        return "ERRO DE CONEXÃO ❌", str(e)

def main():
    # Pega a primeira chave do .env dinamicamente
    env_keys = os.environ.get("GEMINI_API_KEYS", "")
    key = env_keys.split(",")[0].strip() if env_keys else "YOUR_API_KEY_HERE"
    
    models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite"
    ]
    
    print("==========================================================")
    print("      DIAGNÓSTICO DE MODELOS DO GEMINI                   ")
    print("==========================================================")
    
    for m in models:
        print(f"\nTestando modelo '{m}':")
        status, detail = test_model(m, key)
        print(f"  -> Status: {status}")
        print(f"  -> Detalhe: {detail}")
        
    print("\n==========================================================")
    print("      DIAGNÓSTICO CONCLUÍDO                              ")
    print("==========================================================")

if __name__ == "__main__":
    main()
