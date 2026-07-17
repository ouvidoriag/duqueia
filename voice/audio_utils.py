import os
import sys
from voice.voice_config import MAX_AUDIO_SIZE_MB

def check_audio_file(file_path: str) -> bool:
    """
    Verifica se o arquivo de áudio existe e respeita os limites de tamanho.
    """
    if not os.path.exists(file_path):
        print(f"[AudioUtils] Arquivo não encontrado: {file_path}", file=sys.stderr)
        return False
        
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_AUDIO_SIZE_MB:
        print(f"[AudioUtils] Arquivo muito grande ({size_mb:.2f} MB). Limite: {MAX_AUDIO_SIZE_MB} MB", file=sys.stderr)
        return False
        
    return True

def clean_transcript(text: str) -> str:
    """
    Remove ruídos conversacionais comuns de áudio gravado por munícipes.
    """
    if not text:
        return ""
    
    # Lista de preenchimentos conversacionais comuns para remover do início do áudio
    fillers = [
        "ô minha filha", "o minha filha", "então", "é o seguinte", 
        "bom dia", "boa tarde", "boa noite", "olá", "por favor",
        "queria saber", "gostaria de saber", "eu queria saber"
    ]
    
    cleaned = text.strip()
    # Limpeza básica do início da frase
    lowered = cleaned.lower()
    for filler in fillers:
        if lowered.startswith(filler):
            cleaned = cleaned[len(filler):].strip(",. ")
            lowered = cleaned.lower()
            
    # Restaura a primeira letra maiúscula
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
        
    return cleaned
