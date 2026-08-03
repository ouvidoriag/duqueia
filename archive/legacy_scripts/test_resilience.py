import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.gemini_client import GeminiClient

def test_pro_blocking():
    client = GeminiClient()
    print("=== Testando bloqueio de modelo Pro ===")
    res = client.generate_response("Responda 'OK'", model="gemini-2.5-pro")
    print(f"Resultado com model='gemini-2.5-pro': {res.strip()}")

if __name__ == "__main__":
    test_pro_blocking()
