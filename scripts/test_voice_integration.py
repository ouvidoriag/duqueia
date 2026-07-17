import os
import sys
import json

# Ajusta path para importar módulos da raiz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from voice.voice_router import VoiceRouter
from agent.agent import DuqueIAAgent

def main():
    print("=== TESTE DE INTEGRAÇÃO - CAMADA DE VOZ (DUQUE IA) ===")
    
    # Instancia o roteador de voz
    router = VoiceRouter()
    
    # 1. Teste de Entrada de Texto -> Saída de Áudio
    test_query = "Qual é o telefone da Ouvidoria Geral de Duque de Caxias?"
    print(f"\n[1] Testando entrada de texto: '{test_query}'")
    
    response_json = router.process_input(test_query, conversation_id="test_sess_123", generate_audio=True)
    
    try:
        data = json.loads(response_json)
        print(f" -> Resposta formatada: {data.get('answer')[:120]}...")
        audio_url = data.get("response_audio_url")
        if audio_url:
            full_audio_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", audio_url.lstrip("/")))
            print(f" -> Áudio gerado em: {full_audio_path}")
            if os.path.exists(full_audio_path):
                print(" -> [OK] Arquivo de áudio gerado com sucesso!")
            else:
                print(" -> [ERRO] O arquivo de áudio não foi encontrado no disco.")
        else:
            print(f" -> [ERRO] URL de áudio não retornada. Detalhe: {data.get('response_audio_error', 'Nenhum')}")
    except Exception as e:
        print(f" -> [FALHA] Erro ao ler resposta: {e}")
        print("Resposta bruta:")
        print(response_json)

if __name__ == "__main__":
    main()
