import os
import re
import requests
import json
import sys
import io
from dotenv import load_dotenv

load_dotenv()

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def test_key(key):
    masked = key[:8] + "..." + key[-8:] if len(key) > 16 else key
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": "Diga 'OK'."}]}]
    }
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        if response.status_code == 200:
            return "ATIVO ✅", f"Ok"
        elif response.status_code == 429:
            return "LIMITE DE COTA ⚠️", "Erro 429"
        elif response.status_code == 400:
            return "INVÁLIDA ❌", f"Erro 400"
        elif response.status_code == 403:
            return "BLOQUEADA ❌", f"Erro 403"
        else:
            return f"ERRO {response.status_code} ❌", response.text
    except Exception as e:
        return "ERRO DE CONEXÃO ❌", str(e)

print("Procurando chaves do Gemini em os.environ...")
key_pattern = re.compile(r"(?:AIzaSy[A-Za-z0-9_\-]{33})|(?:AQ\.[A-Za-z0-9_\-]{30,})")

env_keys = set()
for env_name, env_val in os.environ.items():
    if "KEY" in env_name.upper() or "GEMINI" in env_name.upper() or "GOOGLE" in env_name.upper():
        matches = key_pattern.findall(env_val)
        for match in matches:
            env_keys.add((env_name, match))

print(f"\nChaves encontradas nas variáveis de ambiente ({len(env_keys)}):")
for name, val in env_keys:
    masked = val[:8] + "..." + val[-8:] if len(val) > 16 else val
    status, detail = test_key(val)
    print(f"- Var: {name} | Chave: {masked} | Status: {status} ({detail})")
