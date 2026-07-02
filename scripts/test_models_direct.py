import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# Tenta usar o novo SDK (google.genai). Fallback para o legado.
try:
    from google import genai
    from google.genai import types as genai_types
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    genai_types = None
    _USE_NEW_SDK = False

def test_direct():
    keys_str = os.getenv("GEMINI_API_KEYS", "")
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    if not api_keys and os.getenv("GOOGLE_API_KEY"):
        api_keys = [os.getenv("GOOGLE_API_KEY")]

    if not api_keys:
        print("Nenhuma chave configurada!")
        return

    # Usaremos a primeira chave ativa para o teste direto
    active_key = api_keys[0]
    print(f"Testando diretamente com a primeira chave ativa: {active_key[:8]}...{active_key[-8:]}")

    if _USE_NEW_SDK:
        client = genai.Client(api_key=active_key)
    else:
        genai.configure(api_key=active_key)

    generation_models = [
        "gemini-2.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.5-pro"
    ]

    print("\n--- GERAÇÃO DE TEXTO DIRETA (Sem Fallbacks) ---")
    working_gen = []
    for model in generation_models:
        try:
            print(f"Testando {model:25} -> ", end="", flush=True)
            if _USE_NEW_SDK:
                resp = client.models.generate_content(
                    model=model,
                    contents="OK",
                )
                txt = resp.text
            else:
                model_obj = genai.GenerativeModel(model_name=model)
                txt = model_obj.generate_content("OK").text
            print(f"SUCCESS! Resposta: {txt.strip().replace('\n', ' ')}")
            working_gen.append(model)
        except Exception as e:
            err = str(e).replace('\n', ' ')
            print(f"FAILED! Erro: {err[:80]}")

    embedding_models = [
        "text-embedding-004",
        "gemini-embedding-2",
        "gemini-embedding-2-preview",
        "gemini-embedding-001"
    ]

    print("\n--- EMBEDDING DIRETO (Sem Fallbacks) ---")
    working_emb = []
    for model in embedding_models:
        try:
            print(f"Testando embedding {model:25} -> ", end="", flush=True)
            if _USE_NEW_SDK:
                resp = client.models.embed_content(
                    model=model,
                    contents="Teste de embedding",
                    config=genai_types.EmbedContentConfig(task_type="retrieval_document") if genai_types else None
                )
                dim = len(resp.embeddings[0].values)
            else:
                model_path = model if model.startswith("models/") else f"models/{model}"
                result = genai.embed_content(
                    model=model_path,
                    content="Teste de embedding",
                    task_type="retrieval_document"
                )
                dim = len(result.get("embedding", []))
            print(f"SUCCESS! Dimensão: {dim}")
            working_emb.append(model)
        except Exception as e:
            err = str(e).replace('\n', ' ')
            print(f"FAILED! Erro: {err[:80]}")

    print("\n=== RESUMO REAL DE MODELOS FUNCIONANDO DIRETAMENTE ===")
    print(f"Texto: {working_gen}")
    print(f"Embedding: {working_emb}")

if __name__ == "__main__":
    test_direct()
