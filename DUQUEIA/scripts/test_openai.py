import os
import sys

# Adiciona o diretório pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openai import OpenAI

def test_openai():
    # Lê a chave da variável de ambiente, ou usa um valor genérico para não travar
    api_key = os.environ.get("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
    print("Iniciando teste da API da OpenAI...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Testando gpt-4o-mini
        print("Testando modelo gpt-4o-mini...", end="", flush=True)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Diga 'OPENAI_OK' se você está funcionando."}
            ],
            max_tokens=10
        )
        print(f" SUCCESS! Resposta: {response.choices[0].message.content.strip()}")
        
    except Exception as e:
        print(f" FAILED! Erro: {e}")

if __name__ == "__main__":
    test_openai()
