import os
import sys
import time
from dotenv import load_dotenv

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

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

def test_keys():
    keys_raw = os.getenv("GEMINI_API_KEYS", "")
    # Limpa aspas e caracteres indesejados
    keys_str = keys_raw.replace('"', '').replace("'", "").replace("\\", "").replace("\n", "").replace("\r", "")
    all_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

    print("="*75)
    print(f"AUDITORIA E DIAGNÓSTICO DAS CHAVES DA API DO GEMINI ({len(all_keys)} chaves no total)")
    print("="*75)

    if not all_keys:
        print("❌ Nenhuma chave GEMINI_API_KEYS foi encontrada no arquivo .env!")
        return

    report = []
    active_count = 0
    quota_exhausted_count = 0
    invalid_count = 0

    for idx, key in enumerate(all_keys):
        masked = mask_key(key)
        print(f"\n[Testando Chave {idx+1}/{len(all_keys)}] {masked} ...", end=" ", flush=True)

        start_time = time.time()
        status = ""
        latency_ms = 0.0
        error_msg = ""

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

            latency_ms = (time.time() - start_time) * 1000.0
            status = "ATIVA / FUNCIONANDO"
            active_count += 1
            print(f"-> [OK] SUCESSO ({latency_ms:.0f}ms)")

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            err_str = str(e)
            
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
                status = "COTA EXCEDIDA (429)"
                quota_exhausted_count += 1
                error_msg = "Cota de requisições excedida (429)."
                print(f"-> [COTA 429] Limit Exceeded")
            elif "400" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                status = "CHAVE INVALIDA / REVOGADA"
                invalid_count += 1
                error_msg = "Chave inválida ou expirada (400/403)."
                print(f"-> [INVALIDA] Key Error")
            else:
                status = f"ERRO: {err_str[:40]}"
                invalid_count += 1
                error_msg = err_str[:80]
                print(f"-> [ERRO] {err_str[:40]}")

        report.append({
            "idx": idx + 1,
            "masked": masked,
            "status": status,
            "latency_ms": round(latency_ms, 1),
            "details": error_msg or "OK"
        })

    print("\n" + "="*75)
    print("RESUMO CONSOLIDADO DAS CHAVES GEMINI:")
    print(f"  Total de Chaves Testadas : {len(all_keys)}")
    print(f"  [OK] Chaves Ativas Operacionais : {active_count}")
    print(f"  [429] Chaves Cota Excedida     : {quota_exhausted_count}")
    print(f"  [ERRO] Chaves Invalidas        : {invalid_count}")
    print("="*75)

    # Tabela detalhada em Markdown
    md_lines = [
        "# Relatório de Diagnóstico de Chaves Gemini API",
        f"**Data do Teste:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Total Auditado:** {len(all_keys)} chaves  ",
        f"**Chaves Ativas Operacionais:** {active_count} ✅  ",
        f"**Chaves com Cota Excedida (429):** {quota_exhausted_count} ⚠️  ",
        f"**Chaves Inválidas/Bloqueadas:** {invalid_count} ❌  ",
        "",
        "| # | Chave Masked | Status Operacional | Latência | Observações |",
        "|:---:|:---|:---|:---:|:---|"
    ]

    for r in report:
        md_lines.append(f"| **{r['idx']}** | `{r['masked']}` | **{r['status']}** | {r['latency_ms']}ms | {r['details']} |")

    report_path = os.path.join(_PROJECT_ROOT, "metrics", "diagnostico_chaves_gemini.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n[Sucesso] Relatorio completo salvo em: {report_path}")

if __name__ == "__main__":
    test_keys()
