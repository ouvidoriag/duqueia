import os
import sys
import json
import re
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

# Tenta usar o novo SDK (google.genai). Fallback para o legado ou HTTP direto.
try:
    from google import genai
    _USE_NEW_SDK = True
except ImportError:
    try:
        import google.generativeai as genai
        _USE_NEW_SDK = False
    except ImportError:
        genai = None
        _USE_NEW_SDK = None

def mask_key(key):
    if len(key) <= 12:
        return key[:3] + "..." + key[-3:]
    return key[:8] + "..." + key[-6:]

def test_gemini_key_http(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": "ping"}]}]}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            txt = res_body.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return True, "200 OK (Funcionando)", txt.strip().replace("\n", " ")[:30]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        if e.code == 429:
            return False, "429 RATE LIMIT / COTA EXCEDIDA", err_body[:80]
        elif e.code == 403:
            return False, "403 BLOQUEADA / INVÁLIDA", err_body[:80]
        elif e.code == 400:
            return False, "400 CHAVE INVÁLIDA OU BAD REQUEST", err_body[:80]
        else:
            return False, f"HTTP {e.code}", err_body[:80]
    except Exception as ex:
        return False, f"ERRO CONEXAO: {str(ex)[:50]}", str(ex)[:80]

def test_groq_key(api_key):
    if not api_key:
        return False, "CHAVE AUSENTE", "Nenhuma chave Groq configurada"
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            txt = res_body['choices'][0]['message']['content']
            return True, "200 OK (Funcionando)", txt.strip().replace("\n", " ")[:30]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        return False, f"HTTP {e.code}", err_body[:80]
    except Exception as ex:
        return False, f"ERRO: {str(ex)[:50]}", str(ex)[:80]

def parse_env_file(env_path=".env"):
    active_keys = []
    temp_disabled_keys = []
    blocked_keys = []
    groq_key = os.getenv("GROQ_API_KEY", "")

    if not os.path.exists(env_path):
        return active_keys, temp_disabled_keys, blocked_keys, groq_key

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extrai GEMINI_API_KEYS
    raw_keys_str = os.getenv("GEMINI_API_KEYS", "")
    if raw_keys_str:
        active_keys = [k.strip() for k in raw_keys_str.split(",") if k.strip()]

    # Extrai chaves comentadas
    lines = content.splitlines()
    section = "active"
    for line in lines:
        line_str = line.strip()
        if "CHAVES DESATIVADAS TEMPORARIAMENTE" in line_str:
            section = "disabled"
        elif "CHAVES INATIVAS" in line_str or "Bloqueadas" in line_str:
            section = "blocked"
        
        if line_str.startswith("# -") or line_str.startswith("#"):
            match = re.search(r'(AQ\.Ab8RN[A-Za-z0-9_\-]+|AIzaSy[A-Za-z0-9_\-]+)', line_str)
            if match:
                k = match.group(1)
                if section == "disabled" and k not in active_keys and k not in temp_disabled_keys:
                    temp_disabled_keys.append(k)
                elif section == "blocked" and k not in active_keys and k not in blocked_keys:
                    blocked_keys.append(k)

    return active_keys, temp_disabled_keys, blocked_keys, groq_key

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    active_keys, temp_disabled_keys, blocked_keys, groq_key = parse_env_file()

    results = []

    print("==========================================================================")
    print("                DIAGNÓSTICO COMPLETO DAS CHAVES API                      ")
    print("==========================================================================")

    print("\n--- 1. TESTANDO CHAVES CONFIGURADAS COMO ATIVAS (GEMINI) ---")
    for idx, key in enumerate(active_keys, 1):
        ok, status, detail = test_gemini_key_http(key)
        icon = "[OK]  " if ok else "[ERRO]"
        print(f"[{idx:02d}/{len(active_keys):02d}] {icon} {mask_key(key):25} -> Status: {status}")
        if not ok:
            print(f"     Detalhe: {detail}")
        results.append({"category": "Ativa", "masked": mask_key(key), "ok": ok, "status": status, "detail": detail})

    print("\n--- 2. TESTANDO CHAVES DESATIVADAS TEMPORARIAMENTE (COTA EXCEDIDA) ---")
    for idx, key in enumerate(temp_disabled_keys, 1):
        ok, status, detail = test_gemini_key_http(key)
        icon = "[OK]  " if ok else "[ERRO]"
        print(f"[{idx:02d}/{len(temp_disabled_keys):02d}] {icon} {mask_key(key):25} -> Status: {status}")
        if not ok:
            print(f"     Detalhe: {detail}")
        results.append({"category": "Desativada Temp", "masked": mask_key(key), "ok": ok, "status": status, "detail": detail})

    print("\n--- 3. TESTANDO CHAVES BLOQUEADAS / VAZADAS (403) ---")
    for idx, key in enumerate(blocked_keys, 1):
        ok, status, detail = test_gemini_key_http(key)
        icon = "[OK]  " if ok else "[ERRO]"
        print(f"[{idx:02d}/{len(blocked_keys):02d}] {icon} {mask_key(key):25} -> Status: {status}")
        if not ok:
            print(f"     Detalhe: {detail}")
        results.append({"category": "Bloqueada/Vazada", "masked": mask_key(key), "ok": ok, "status": status, "detail": detail})

    if groq_key:
        print("\n--- 4. TESTANDO CHAVE GROQ API ---")
        ok, status, detail = test_groq_key(groq_key)
        icon = "[OK]  " if ok else "[ERRO]"
        print(f"[01/01] {icon} {mask_key(groq_key):25} -> Status: {status}")
        if not ok:
            print(f"     Detalhe: {detail}")
        results.append({"category": "Groq", "masked": mask_key(groq_key), "ok": ok, "status": status, "detail": detail})

    print("\n==========================================================================")
    print("                            RESUMO DA AUDITORIA                           ")
    print("==========================================================================")
    working_keys = [r for r in results if r["ok"]]
    failed_keys = [r for r in results if not r["ok"]]
    print(f"Total de Chaves Testadas: {len(results)}")
    print(f"Chaves FUNCIONANDO (200 OK): {len(working_keys)}")
    print(f"Chaves COM FALHA/COTA/BLOQUEIO: {len(failed_keys)}")
    print("--------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
