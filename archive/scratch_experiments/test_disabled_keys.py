import os
import sys
import time
import re

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(_PROJECT_ROOT, ".env")

try:
    from google import genai
    from google.genai import types
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    _USE_NEW_SDK = False

def mask_key(k: str) -> str:
    if len(k) <= 12:
        return k[:4] + "..."
    return k[:8] + "..." + k[-6:]

def test_disabled_keys():
    if not os.path.exists(ENV_PATH):
        print("Arquivo .env não encontrado.")
        return

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        env_content = f.read()

    # Extrai todas as chaves comentadas que começam com AIzaSy ou AQ.Ab8RN
    commented_keys = re.findall(r'#\s*-\s*(AQ\.Ab8RN[A-Za-z0-9_\-]+|AIzaSy[A-Za-z0-9_\-]+)', env_content)
    
    # Remove duplicatas mantendo ordem
    unique_disabled = []
    for k in commented_keys:
        k_clean = k.strip()
        if k_clean not in unique_disabled:
            unique_disabled.append(k_clean)

    print("="*75)
    print(f"TESTANDO TODAS AS {len(unique_disabled)} CHAVES DESATIVADAS / COMENTADAS DO .ENV")
    print("="*75)

    working_disabled = []
    still_blocked = []

    for idx, key in enumerate(unique_disabled, 1):
        masked = mask_key(key)
        print(f"\n[Testando Desativada {idx}/{len(unique_disabled)}] {masked} ...", end=" ", flush=True)

        start_t = time.time()
        try:
            if _USE_NEW_SDK:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents="Responda apenas OK",
                    config=types.GenerateContentConfig(
                        max_output_tokens=5,
                        temperature=0.0
                    )
                )
                txt = response.text.strip() if response and response.text else "OK"
            else:
                genai.configure(api_key=key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                res = model.generate_content("Responda apenas OK")
                txt = res.text.strip() if res and res.text else "OK"

            lat_ms = (time.time() - start_t) * 1000.0
            print(f"-> [REATIVADA!] FUNCIONANDO ({lat_ms:.0f}ms)")
            working_disabled.append((key, masked, lat_ms))

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print("-> [COTA 429] Ainda em limite de cota")
                still_blocked.append((key, masked, "Cota 429 excedida"))
            elif "400" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                print("-> [INVALIDA / BLOQUEADA 403]")
                still_blocked.append((key, masked, "Inválida / Bloqueada 403"))
            else:
                print(f"-> [ERRO] {err_str[:40]}")
                still_blocked.append((key, masked, err_str[:40]))

    print("\n" + "="*75)
    print("RESULTADO DO TESTE DAS CHAVES DESATIVADAS:")
    print(f"  Total de Chaves Desativadas Testadas: {len(unique_disabled)}")
    print(f"  [REATIVADAS/VOLTARAM A FUNCIONAR]  : {len(working_disabled)}")
    print(f"  [PERMANECEM BLOQUEADAS/COTA]        : {len(still_blocked)}")
    print("="*75)

    if working_disabled:
        print("\n🎉 AS SEGUINTES CHAVES VOLTARAM A FUNCIONAR E PODEM SER RE-ATIVADAS NO .ENV:")
        for k, m, lat in working_disabled:
            print(f"  • {m} (Chave completa: {k}) - {lat:.0f}ms")
    else:
        print("\nℹ️ Nenhuma das chaves desativadas voltou a funcionar no momento.")

if __name__ == "__main__":
    test_disabled_keys()
