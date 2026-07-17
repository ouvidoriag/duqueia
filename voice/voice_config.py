# ==============================================================================
#                      CONFIGURAÇÃO DE VOZ - DUQUE IA
# ==============================================================================
import os

# Configurações de limite de áudio
MAX_AUDIO_DURATION_SECONDS = 120.0  # Limite para transcrição direta rápida
MAX_AUDIO_SIZE_MB = 25.0            # Limite de tamanho de arquivo (aumentado para suportar respostas longas)

# Idioma padrão para transcrição e síntese
DEFAULT_LANGUAGE = "pt-BR"

# Personas de Voz (Configuração para TTS/gTTS ou outros provedores)
VOICE_PERSONAS = {
    "duque_ia": {
        "lang": "pt-BR",
        "tld": "com.br",  # Sotaque brasileiro
        "gender": "female",
    },
    "ouvidoria": {
        "lang": "pt-BR",
        "tld": "com.br",
        "gender": "male",
    }
}

DEFAULT_PERSONA = "duque_ia"
