import os
import sys
import uuid
import json
from voice.audio_utils import check_audio_file
from agent.agent import DuqueIAAgent

class VoiceRouter:
    """
    Roteador multimodal para interceptar mensagens de voz de munícipes.
    1. Transcreve o áudio de entrada para texto usando Gemini.
    2. Limpa ruídos conversacionais do texto usando Gemini.
    3. Roteia a query resultante para o processador RAG/Triage.
    4. Converte a resposta de texto de volta em áudio falado usando Gemini.
    5. Retorna JSON integrado com texto, transcrição e link do áudio.
    """
    def __init__(self, agent: DuqueIAAgent = None):
        self.agent = agent if agent else DuqueIAAgent()
        self.gemini = self.agent.gemini_client

    def process_input(self, input_value: str, conversation_id: str = None, is_audio: bool = False, generate_audio: bool = False, output_audio_dir: str = "public/audio") -> str:
        """
        Processa entrada de texto ou caminho de áudio.
        Retorna string JSON contendo a resposta integrada.
        """
        is_file_audio = isinstance(input_value, str) and os.path.exists(input_value) and input_value.lower().endswith(('.mp3', '.wav', '.ogg', '.opus', '.webm'))
        
        should_transcribe = is_audio or is_file_audio
        should_synthesize = should_transcribe or generate_audio
        
        raw_text = ""
        cleaned_text = ""
        audio_metadata = {}
        
        if should_transcribe:
            audio_path = input_value
            if not check_audio_file(audio_path):
                return json.dumps({
                    "error": "Arquivo de áudio inválido ou excede o limite de tamanho.",
                    "answer": "O áudio enviado é muito grande ou inválido. Por favor, envie uma mensagem mais curta.",
                    "intent_detected": "invalid_audio"
                }, ensure_ascii=False)

            print(f"[VoiceRouter] Iniciando processamento integrado do áudio via Gemini: {audio_path}", file=sys.stderr)
            audio_metadata = self.gemini.transcribe_and_clean_audio(audio_path)
            raw_text = audio_metadata.get("raw_transcription", "")
            cleaned_text = audio_metadata.get("question", "")
            
            if not cleaned_text:
                return json.dumps({
                    "error": "Não foi possível compreender o áudio enviado.",
                    "answer": "Não consegui compreender o áudio. Por favor, tente falar mais claro ou digite sua mensagem.",
                    "intent_detected": "audio_transcription_failed"
                }, ensure_ascii=False)

            print(f"[VoiceRouter] Transcrição bruta: \"{raw_text}\" | Transcrição limpa: \"{cleaned_text}\" | Bairro: {audio_metadata.get('bairro')} | Intenção: {audio_metadata.get('intent')}", file=sys.stderr)
            query_to_process = cleaned_text
        else:
            query_to_process = input_value

        # Processa no RAG / Agente Central
        agent_response_json = self.agent.respond(query_to_process, use_triage=True, conversation_id=conversation_id)
        
        try:
            data = json.loads(agent_response_json)
        except Exception:
            data = {"answer": agent_response_json}

        # Insere metadados de transcrição e contexto se veio de áudio
        if should_transcribe:
            data["transcription"] = {
                "raw": raw_text,
                "cleaned": cleaned_text,
                "confidence": 1.0
            }
            if audio_metadata.get("bairro"):
                data["context_bairro"] = audio_metadata["bairro"]
            if audio_metadata.get("citizen_name"):
                data["context_citizen_name"] = audio_metadata["citizen_name"]
            if audio_metadata.get("intent"):
                data["intent_detected"] = audio_metadata["intent"]

        # Gera resposta em áudio falado se necessário
        if should_synthesize:
            text_to_speak = data.get("answer", "")
            if text_to_speak:
                import re
                
                # ── Conversão inteligente para Voz: Linguagem natural, amigável e concisa ──
                try:
                    voice_system_instruction = (
                        "Você é a voz institucional oficial do Duque IA da Prefeitura de Duque de Caxias.\n"
                        "Sua tarefa é converter o texto informativo em uma fala simpática, calorosa e altamente conversacional.\n"
                        "REGRAS DE CONVERSÃO:\n"
                        "1. Não utilize listas, tópicos (bullets) ou markdown.\n"
                        "2. Seja amigável e use linguagem natural de um atendente municipal.\n"
                        "3. Mantenha o conteúdo completo; use no máximo 150 palavras.\n"
                        "4. NUNCA adicione informações não presentes no texto de entrada.\n"
                        "5. Se houver endereços, telefones, horários ou prazos, mantenha-os COMPLETOS e de forma clara.\n"
                        "6. Fale como se estivesse respondendo diretamente ao munícipe por mensagem de voz.\n"
                        "7. Não termine a frase de forma abrupta; sempre conclua o raciocínio."
                    )
                    
                    spoken_text = self.gemini.generate_response(
                        prompt=f"Texto informativo: \"{text_to_speak}\"",
                        system_instruction=voice_system_instruction,
                        temperature=0.2
                    )
                    
                    # Remove markdown residual de segurança
                    spoken_text = re.sub(r"\*\*|\*|#|`|\[.*?\]\(.*?\)", "", spoken_text)
                    spoken_text = " ".join(spoken_text.split())
                    print(f"[VoiceRouter] Texto original: \"{text_to_speak}\" | Texto para fala: \"{spoken_text}\"", file=sys.stderr)
                except Exception as voice_err:
                    print(f"[VoiceRouter] Falha ao formatar texto para voz: {voice_err}", file=sys.stderr)
                    # Fallback de segurança: limpa apenas markdown do texto original
                    spoken_text = re.sub(r"\*\*|\*|#|`|\[.*?\]\(.*?\)", "", text_to_speak)
                    spoken_text = " ".join(spoken_text.split())
                
                prefix = f"response_{uuid.uuid4().hex}"
                print(f"[VoiceRouter] Gerando resposta de voz via Gemini...", file=sys.stderr)
                persona = "duque_ia"
                if "ouvidoria" in spoken_text.lower():
                    persona = "ouvidoria"
                    
                generated_filename = self.gemini.generate_speech(spoken_text, output_audio_dir, prefix, persona=persona)
                if generated_filename:
                    data["response_audio_url"] = f"/audio/{generated_filename}"
                else:
                    data["response_audio_error"] = "Falha ao gerar síntese de voz."

        return json.dumps(data, ensure_ascii=False, indent=2)
