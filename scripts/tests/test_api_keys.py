import os
import sys
import requests
import json
import io

# Configura saída UTF-8 no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Garante acesso ao diretório raiz
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

def test_key(key):
    masked = key[:8] + "..." + key[-8:] if len(key) > 16 else key
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": "Diga 'OK' se a chave está funcionando."}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            # Verifica se retornou texto
            try:
                text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return "ATIVO ✅", f"Retornou: '{text}'"
            except Exception:
                return "ATIVO ✅", "Resposta vazia/inesperada, mas API aceitou."
        elif response.status_code == 429:
            return "LIMITE DE COTA ⚠️", "Erro 429 - Rate limit / Quota esgotada."
        elif response.status_code == 400:
            return "INVÁLIDA / INCOMPATÍVEL ❌", f"Erro 400 - Argumento inválido. Detalhe: {response.text}"
        elif response.status_code == 403:
            return "BLOQUEADA / PRIVACIDADE ❌", f"Erro 403 - Permissão negada / Chave inativa."
        else:
            return f"ERRO {response.status_code} ❌", response.text
    except Exception as e:
        return "ERRO DE CONEXÃO ❌", str(e)

def main():
    print("==========================================================")
    print("      DIAGNÓSTICO DE CHAVES DE API DO GEMINI             ")
    print("==========================================================")
    
    # Lê as chaves dinamicamente da variável de ambiente no .env para não expor segredos
    env_keys = os.environ.get("GEMINI_API_KEYS", "")
    keys_to_test = [k.strip() for k in env_keys.split(",") if k.strip()]
    if not keys_to_test:
        keys_to_test = ["YOUR_API_KEY_HERE"]
    
    for i, key in enumerate(keys_to_test):
        masked = key[:8] + "..." + key[-8:] if len(key) > 16 else key
        print(f"\nChave {i} [{masked}]:")
        status, detail = test_key(key)
        print(f"  -> Status: {status}")
        print(f"  -> Detalhe: {detail}")
        
    print("\n==========================================================")
    print("      DIAGNÓSTICO CONCLUÍDO                              ")
    print("==========================================================")

if __name__ == "__main__":
    main()
