import sys
import os
from dotenv import load_dotenv

# Adiciona o diretório pai (raiz) ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Carrega variáveis do arquivo .env
load_dotenv()

from utils.gemini_client import GeminiClient

def test_models():
    client = GeminiClient()
    print("Chaves de API configuradas no cliente:")
    print(f"Total de chaves: {len(client.api_keys)}")
    
    # Modelos de geração de texto a testar
    generation_models = [
        "gemini-2.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    
    print("\n=== TESTANDO MODELOS DE GERAÇÃO DE TEXTO ===")
    working_gen_models = []
    for model in generation_models:
        try:
            print(f"Testando {model}...", end="", flush=True)
            res = client.generate_response(
                prompt="Diga 'OK' se você está funcionando.",
                model=model
            )
            print(f" SUCCESS! Resposta: {res.strip()}")
            working_gen_models.append(model)
        except Exception as e:
            print(f" FAILED! Erro: {e}")

    print("\n=== TESTANDO MODELOS DE EMBEDDING ===")
    embedding_models = [
        "gemini-embedding-2",
        "gemini-embedding-2-preview",
        "gemini-embedding-001",
        "text-embedding-004"
    ]
    
    working_emb_models = []
    for model in embedding_models:
        try:
            print(f"Testando embedding {model}...", end="", flush=True)
            # Para testar um modelo específico temporariamente
            client.embedding_model_name = model
            # Força limpar cache do modelo que funcionou para testar este
            client._working_embedding_model = None
            vec = client.get_embedding("Teste de embedding", is_query=False)
            print(f" SUCCESS! Dimensão do vetor: {len(vec)}")
            working_emb_models.append(model)
        except Exception as e:
            print(f" FAILED! Erro: {e}")

    print("\n=== RESUMO ===")
    print(f"Modelos de geração de texto funcionando: {working_gen_models}")
    print(f"Modelos de embedding funcionando: {working_emb_models}")

if __name__ == "__main__":
    test_models()
