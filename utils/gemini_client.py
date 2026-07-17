import sys
import os
import time
import warnings
import json
from config.settings import GEMINI_MODEL, GEMINI_EMBEDDING_MODEL

# Suprime FutureWarnings de pacotes legados durante a transicao
warnings.filterwarnings("ignore", category=FutureWarning)

# Tenta usar o novo SDK (google.genai). Fallback para o legado se nao instalado.
try:
    from google import genai
    from google.genai import types as genai_types
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    genai_types = None
    _USE_NEW_SDK = False

# Modelos de embedding a tentar em ordem de prioridade
# Estes sao os modelos reais disponíveis para as chaves AIzaSy do projeto
_EMBEDDING_MODELS_FALLBACK = [
    "gemini-embedding-2",           # Mais recente e preciso
    "gemini-embedding-2-preview",   # Preview do gemini-embedding-2
    "gemini-embedding-001",         # Versao estavel anterior
    "models/gemini-embedding-2",    # Com prefixo (SDK legado)
    "models/gemini-embedding-001",  # Com prefixo (SDK legado)
]


class GeminiClient:
    """
    Cliente wrapper para a API do Gemini com suporte a rotação automática de chaves
    e retentativa. Compatível com google.genai (novo) e google.generativeai (legado).
    """

    def __init__(self):
        # ── Bloco 1: MockProvider automático em modo de teste ──────────────────
        # Se DUQUE_IA_TEST_MODE=1, substitui toda a lógica por respostas mock
        # sem qualquer chamada de rede. Isso elimina TIMEOUTs nos testes.
        if os.getenv("DUQUE_IA_TEST_MODE", "").strip() == "1":
            from utils.mock_provider import MockLLMProvider
            mock = MockLLMProvider()
            self.__class__ = mock.__class__
            self.__dict__.update(mock.__dict__)
            print("[GeminiClient] DUQUE_IA_TEST_MODE=1 — usando MockLLMProvider (zero rede).", file=sys.stderr)
            return
        # ───────────────────────────────────────────────────────────────────────

        # Carrega a lista de chaves do arquivo .env
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        # Remove aspas, barras invertidas e quebras de linha para suportar chaves multilinhas no .env
        keys_str = keys_str.replace('"', '').replace("'", "").replace("\\", "").replace("\n", "").replace("\r", "")
        all_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

        # Filtra chaves Gemini API válidas: AIzaSy... (padrão) e AQ.Ab8RN... (novas chaves de autorização/Auth)
        self.api_keys = [k for k in all_keys if k.startswith("AIzaSy") or k.startswith("AQ.")]
        self.oauth_keys = [k for k in all_keys if not (k.startswith("AIzaSy") or k.startswith("AQ."))]

        if self.oauth_keys:
            print(f"[GeminiClient] INFO: {len(self.oauth_keys)} chave(s) ignorada(s).", file=sys.stderr)

        # Fallback para chave singular se disponivel
        if not self.api_keys and os.getenv("GOOGLE_API_KEY"):
            self.api_keys = [os.getenv("GOOGLE_API_KEY")]

        self.current_key_index = 0
        self.embedding_model_name = GEMINI_EMBEDDING_MODEL
        self.generation_model_name = GEMINI_MODEL
        self._working_embedding_model = None  # cache do modelo que funcionou

        # Cliente instanciado pelo novo SDK (por chave ativa)
        self._client = None

        self.key_cooldowns = {i: 0.0 for i in range(len(self.api_keys))}

        if self.api_keys:
            self._configure_current_key()
        else:
            print("[GeminiClient] AVISO: Nenhuma chave de API configurada. "
                  "Sistema rodara em modo offline (fallback local).")



    def _configure_current_key(self):
        """Configura a chave ativa atual no SDK do Google."""
        if not self.api_keys:
            return
        active_key = self.api_keys[self.current_key_index]
        masked = active_key[:8] + "..." + active_key[-8:] if len(active_key) > 16 else "***"
        print(f"[GeminiClient] Chave ativa [{self.current_key_index}]: {masked}", file=sys.stderr)

        if _USE_NEW_SDK:
            # Novo SDK: instancia Client com a chave
            self._client = genai.Client(api_key=active_key)
        else:
            # Legado: configura globalmente
            genai.configure(api_key=active_key)

    def rotate_key(self, model_name: str = None):
        """Rotaciona para a proxima chave de API disponivel que nao esta em cooldown para o modelo."""
        if not self.api_keys:
            return False
        
        now = time.time()
        start_idx = self.current_key_index
        for offset in range(1, len(self.api_keys) + 1):
            next_idx = (start_idx + offset) % len(self.api_keys)
            cooldown_key = (next_idx, model_name) if model_name else next_idx
            if self.key_cooldowns.get(cooldown_key, 0.0) < now:
                self.current_key_index = next_idx
                self._configure_current_key()
                return True
        
        # Se todas estao em cooldown para este modelo, falha imediatamente sem sleep para ativar fallback offline rapido
        raise RuntimeError(f"Todas as chaves de API do Gemini estao em cooldown temporario para o modelo {model_name}.")

    def is_retryable_error(self, e) -> bool:
        """Determina se o erro é temporário/de cota (retryable) ou de código/chave inválida (não-retryable)."""
        error_msg = str(e).lower()
        if isinstance(e, (TypeError, ValueError, KeyError, NameError, AttributeError)):
            return False
        non_retryable_phrases = [
            "unexpected keyword argument",
            "invalid argument",
            "api key not valid",
            "incorrect api key provided",
            "invalid_api_key",
            "invalid api key",
            "not found",
            "400"
        ]
        if any(phrase in error_msg for phrase in non_retryable_phrases):
            return False
        return True

    def execute_with_rotation(self, func, model_name: str = None, *args, **kwargs):
        """
        Executa uma funcao da API do Gemini com roteamento robusto.
        Distingue erros de programacao de erros de cota (429/503).
        Caso ocorra erro temporario, coloca a chave em cooldown para o modelo e rotaciona imediatamente.
        """
        if not self.api_keys:
            raise RuntimeError("Nenhuma chave de API disponivel no sistema.")

        max_attempts = len(self.api_keys) * 2
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 1. Classifica o erro
                if not self.is_retryable_error(e):
                    print(f"[GeminiClient] ERRO NÃO RECUPERÁVEL: {e}. Abortando execução.", file=sys.stderr)
                    raise e
                
                # 2. Erro recuperável (429, 503, timeout)
                print(f"[GeminiClient] Erro recuperável na tentativa {attempt + 1}: {e}", file=sys.stderr)
                
                # Coloca a chave atual em cooldown de 60 segundos para este modelo
                cooldown_key = (self.current_key_index, model_name) if model_name else self.current_key_index
                self.key_cooldowns[cooldown_key] = time.time() + 60.0
                
                if attempt == max_attempts - 1:
                    break
                
                # Rotaciona chave imediatamente (se todas estiverem em cooldown, levantará RuntimeError instantâneo)
                self.rotate_key(model_name=model_name)

        raise RuntimeError("Todas as chaves de API falharam ou atingiram limite de cota.")

    # --------------------------------------------------------------------------
    # EMBEDDINGS
    # --------------------------------------------------------------------------
    def get_embedding(self, text: str, is_query: bool = False) -> list:
        """Gera vetor de embedding com fallback progressivo de modelos."""
        if not self.api_keys:
            return self._local_fallback_embedding(text)

        task_type = "retrieval_query" if is_query else "retrieval_document"

        # Se ja temos um modelo que funcionou antes, usa direto
        models_to_try = ([self._working_embedding_model] + _EMBEDDING_MODELS_FALLBACK
                         if self._working_embedding_model else _EMBEDDING_MODELS_FALLBACK)

        for model_name in models_to_try:
            try:
                if _USE_NEW_SDK:
                    def _call(m=model_name):
                        resp = self._client.models.embed_content(
                            model=m,
                            contents=text,
                            config=genai_types.EmbedContentConfig(task_type=task_type)
                        )
                        return resp.embeddings[0].values
                else:
                    def _call(m=model_name):
                        # Garante prefixo models/ para o SDK legado
                        model_path = m if m.startswith("models/") else f"models/{m}"
                        result = genai.embed_content(
                            model=model_path,
                            content=text,
                            task_type=task_type
                        )
                        return result.get("embedding", [])

                vector = _call()
                if vector:
                    self._working_embedding_model = model_name
                    return vector

            except Exception as e:
                err = str(e).lower()
                if "404" in err or "not found" in err:
                    # Modelo nao disponivel, tenta o proximo
                    continue
                # Outro erro: tenta rotacionar chave
                print(f"[GeminiClient] Erro de embedding ({model_name}): {e}", file=sys.stderr)
                self.rotate_key()
                time.sleep(0.5)

        return self._local_fallback_embedding(text)

    def generate_interaction(self, prompt: str, system_instruction: str = None, model: str = None, previous_interaction_id: str = None, temperature: float = None, max_output_tokens: int = None) -> tuple:
        """Gera resposta usando a API padrão do Gemini (generate_content) e retorna (texto_resposta, None, working_model)."""
        if not self.api_keys:
            return "Desculpe, o sistema esta rodando sem chaves de API ativas.", None, None

        requested_model = model if model else self.generation_model_name
        models_to_try = [requested_model]
        
        # Fallbacks padrão se o solicitado falhar
        default_fallbacks = [
            "gemini-2.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-3.5-flash"
        ]
        for m in default_fallbacks:
            if m not in models_to_try:
                models_to_try.append(m)

        last_exception = None
        for current_model in models_to_try:
            try:
                if _USE_NEW_SDK:
                    def _call(m=current_model):
                        config = {
                            "safety_settings": [
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                ),
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                ),
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                ),
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                )
                            ]
                        }
                        if system_instruction:
                            config["system_instruction"] = system_instruction
                        if temperature is not None:
                            config["temperature"] = temperature
                        if max_output_tokens is not None:
                            config["max_output_tokens"] = max_output_tokens
                        
                        resp = self._client.models.generate_content(
                            model=m,
                            contents=prompt,
                            config=genai_types.GenerateContentConfig(**config)
                        )
                        return resp.text, None
                else:
                    def _call(m=current_model):
                        model_obj = genai.GenerativeModel(
                            model_name=m,
                            system_instruction=system_instruction
                        )
                        gen_config = {}
                        if temperature is not None:
                            gen_config["temperature"] = temperature
                        if max_output_tokens is not None:
                            gen_config["max_output_tokens"] = max_output_tokens
                        
                        legacy_safety = [
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
                        ]
                        res = model_obj.generate_content(
                            prompt,
                            generation_config=genai.GenerationConfig(**gen_config) if gen_config else None,
                            safety_settings=legacy_safety
                        ).text
                        return res, None

                # Executa com rotação de chaves
                ans, c_id = self.execute_with_rotation(_call, model_name=current_model)
                return ans, c_id, current_model
            except Exception as e:
                last_exception = e
                print(f"[GeminiClient] Falha com o modelo {current_model} na geração de conteúdo: {e}. Tentando próximo fallback...", file=sys.stderr)
                time.sleep(0.5)

        raise last_exception if last_exception else RuntimeError("Todos os modelos falharam na geração de conteúdo.")


    def generate_response(self, prompt: str, system_instruction: str = None, model: str = None, temperature: float = None, max_output_tokens: int = None) -> str:
        """Gera resposta textual do modelo Gemini com fallback automático de modelos em caso de 429/erros."""
        if not self.api_keys:
            return "Desculpe, o sistema esta rodando sem chaves de API ativas."

        requested_model = model if model else self.generation_model_name
        models_to_try = [requested_model]
        
        # Fallbacks padrão se o solicitado falhar (priorizando modelos verificados)
        default_fallbacks = [
            "gemini-2.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-2.0-flash"
        ]
        for m in default_fallbacks:
            if m not in models_to_try:
                models_to_try.append(m)

        last_exception = None
        for current_model in models_to_try:
            try:
                if _USE_NEW_SDK:
                    def _call(m=current_model):
                        config = {
                            "safety_settings": [
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                ),
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                ),
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                ),
                                genai_types.SafetySetting(
                                    category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                    threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                                )
                            ]
                        }
                        if system_instruction:
                            config["system_instruction"] = system_instruction
                        if temperature is not None:
                            config["temperature"] = temperature
                        if max_output_tokens is not None:
                            config["max_output_tokens"] = max_output_tokens
                        resp = self._client.models.generate_content(
                            model=m,
                            contents=prompt,
                            config=genai_types.GenerateContentConfig(**config)
                        )
                        return resp.text
                else:
                    def _call(m=current_model):
                        model_obj = genai.GenerativeModel(
                            model_name=m,
                            system_instruction=system_instruction
                        )
                        gen_config = {}
                        if temperature is not None:
                            gen_config["temperature"] = temperature
                        if max_output_tokens is not None:
                            gen_config["max_output_tokens"] = max_output_tokens
                        
                        legacy_safety = [
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
                        ]
                        return model_obj.generate_content(
                            prompt,
                            generation_config=genai.GenerationConfig(**gen_config) if gen_config else None,
                            safety_settings=legacy_safety
                        ).text

                # Executa com rotação de chaves para este modelo específico
                return self.execute_with_rotation(_call, model_name=current_model)
            except Exception as e:
                last_exception = e
                print(f"[GeminiClient] Falha com o modelo {current_model}: {e}. Tenta próximo modelo de fallback.", file=sys.stderr)
                time.sleep(0.5)

        raise last_exception if last_exception else RuntimeError("Todos os modelos falharam na geração de conteúdo.")

    # --------------------------------------------------------------------------
    # FALLBACK LOCAL (SEM CHAVE)
    # --------------------------------------------------------------------------
    def _local_fallback_embedding(self, text: str) -> list:
        """
        Gera vetor determinístico baseado em hash para uso offline/dev.
        Dimensao: 768 (alinhado com text-embedding-004).
        """
        import hashlib
        hasher = hashlib.sha256()
        hasher.update(text.encode("utf-8"))
        seed = int(hasher.hexdigest(), 16)

        vector = []
        for _ in range(768):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            vector.append((seed % 2000 - 1000) / 1000.0)

        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector

    def _wait_for_file_active(self, uploaded_file):
        """Aguarda até que o arquivo carregado mude de PROCESSING para ACTIVE (máx 30s)."""
        import time
        start_time = time.time()
        file_obj = uploaded_file
        
        while True:
            try:
                if _USE_NEW_SDK:
                    file_obj = self._client.files.get(name=uploaded_file.name)
                else:
                    file_obj = genai.get_file(uploaded_file.name)
            except Exception as e:
                # Falhas de consulta temporárias não devem abortar a espera!
                print(f"[GeminiClient] Falha temporária ao consultar estado do arquivo: {e}", file=sys.stderr)
                time.sleep(1.0)
                if time.time() - start_time > 30:
                    raise TimeoutError("Tempo limite esgotado ao tentar consultar arquivo no Gemini.")
                continue

            state_attr = getattr(file_obj, "state", None)
            if state_attr is None:
                # Se a API não retornou o campo 'state', consideramos ACTIVE por precaução
                break
                
            state_str = str(state_attr).upper()
            if "ACTIVE" in state_str:
                break
            if "FAILED" in state_str:
                raise RuntimeError(f"O processamento do arquivo no Gemini falhou. Estado: {state_str}")
                
            if time.time() - start_time > 30: # Timeout de 30 segundos
                raise TimeoutError("Tempo limite de 30s esgotado aguardando o arquivo ficar ACTIVE no Gemini.")
                
            time.sleep(0.5)
            
        return file_obj

    def transcribe_and_clean_audio(self, audio_path: str) -> dict:
        """Transcreve, limpa e extrai intenção/bairro do áudio em uma única chamada de API."""
        prompt = (
            "Você é um processador inteligente do Duque IA.\n"
            "Receberá um áudio enviado pelo cidadão.\n"
            "Sua função é:\n"
            "1 - Transcrever literalmente o áudio em português.\n"
            "2 - Remover vícios de linguagem, cumprimentos (bom dia, etc.), introduções e ruídos conversacionais para gerar uma pergunta de busca objetiva.\n"
            "3 - Identificar se o cidadão mencionou o nome de um bairro ou o próprio nome.\n"
            "4 - Detectar a intenção da mensagem (ex: solicitacao, reclamacao, informacao).\n\n"
            "Retorne APENAS um JSON válido no seguinte formato (sem blocos de código markdown ou texto extra):\n"
            "{\n"
            "    \"raw_transcription\": \"transcrição literal...\",\n"
            "    \"question\": \"pergunta objetiva para busca RAG...\",\n"
            "    \"bairro\": \"nome do bairro se mencionado ou null\",\n"
            "    \"citizen_name\": \"nome se mencionado ou null\",\n"
            "    \"intent\": \"solicitacao/reclamacao/informacao...\"\n"
            "}"
        )
        
        def _call_new_sdk():
            uploaded_file = self._client.files.upload(file=audio_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                resp = self._client.models.generate_content(
                    model=self.generation_model_name,
                    contents=[uploaded_file, prompt]
                )
                text = resp.text.strip() if resp.text else "{}"
                
                # Remove blocos de código JSON markdown se houver
                import re
                cleaned_txt = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
                cleaned_txt = re.sub(r"^```\s*", "", cleaned_txt, flags=re.IGNORECASE)
                cleaned_txt = re.sub(r"\s*```$", "", cleaned_txt, flags=re.IGNORECASE)
                
                try:
                    return json.loads(cleaned_txt.strip())
                except Exception as parse_err:
                    print(f"[GeminiClient] Falha ao fazer parse do JSON retornado: {parse_err}. Texto bruto: {text}", file=sys.stderr)
                    return {"raw_transcription": text, "question": text, "bairro": None, "citizen_name": None, "intent": "desconhecida"}
            finally:
                try:
                    self._client.files.delete(name=uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar áudio temporário: {ex}", file=sys.stderr)

        def _call_legacy_sdk():
            uploaded_file = genai.upload_file(path=audio_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                model_obj = genai.GenerativeModel(model_name=self.generation_model_name)
                resp = model_obj.generate_content([uploaded_file, prompt])
                text = resp.text.strip() if resp.text else "{}"
                
                import re
                cleaned_txt = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
                cleaned_txt = re.sub(r"^```\s*", "", cleaned_txt, flags=re.IGNORECASE)
                cleaned_txt = re.sub(r"\s*```$", "", cleaned_txt, flags=re.IGNORECASE)
                
                try:
                    return json.loads(cleaned_txt.strip())
                except Exception as parse_err:
                    print(f"[GeminiClient] Falha ao fazer parse do JSON retornado (legacy): {parse_err}. Texto bruto: {text}", file=sys.stderr)
                    return {"raw_transcription": text, "question": text, "bairro": None, "citizen_name": None, "intent": "desconhecida"}
            finally:
                try:
                    genai.delete_file(uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar áudio temporário (legacy): {ex}", file=sys.stderr)

        func = _call_new_sdk if _USE_NEW_SDK else _call_legacy_sdk
        try:
            return self.execute_with_rotation(func, model_name=self.generation_model_name)
        except Exception as e:
            print(f"[GeminiClient] Falha ao processar áudio: {e}", file=sys.stderr)
            return {}

    # --------------------------------------------------------------------------
    # MÉTODOS MULTIMODAIS INTEGRADOS
    # --------------------------------------------------------------------------
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcreve áudio nativamente usando a API do Gemini com upload temporário."""
        prompt = (
            "Você é um transcritor profissional de áudio. "
            "Transcreva o áudio acima literalmente, palavra por palavra em português do Brasil. "
            "Não adicione nenhuma introdução, explicação ou comentário. Retorne apenas o texto falado."
        )
        
        def _call_new_sdk():
            uploaded_file = self._client.files.upload(file=audio_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                resp = self._client.models.generate_content(
                    model=self.generation_model_name,
                    contents=[uploaded_file, prompt]
                )
                return resp.text.strip() if resp.text else ""
            finally:
                try:
                    self._client.files.delete(name=uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar arquivo temporário de áudio: {ex}", file=sys.stderr)

        def _call_legacy_sdk():
            uploaded_file = genai.upload_file(path=audio_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                model_obj = genai.GenerativeModel(model_name=self.generation_model_name)
                resp = model_obj.generate_content([uploaded_file, prompt])
                return resp.text.strip() if resp.text else ""
            finally:
                try:
                    genai.delete_file(uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar arquivo temporário de áudio: {ex}", file=sys.stderr)

        func = _call_new_sdk if _USE_NEW_SDK else _call_legacy_sdk
        try:
            return self.execute_with_rotation(func, model_name=self.generation_model_name)
        except Exception as e:
            print(f"[GeminiClient] Falha ao transcrever áudio: {e}", file=sys.stderr)
            return ""

    def clean_citizen_speech(self, transcription: str) -> str:
        """Limpa vícios de fala do munícipe para gerar uma query limpa e objetiva para o RAG."""
        if not transcription.strip():
            return ""
            
        system_instruction = (
            "Sua função é transformar a fala do cidadão em uma pergunta objetiva para busca em banco de dados.\n"
            "NÃO RESPONDA A PERGUNTA. NÃO ADICIONE INFORMAÇÕES.\n"
            "Remova apenas:\n"
            "- vícios de linguagem\n"
            "- cumprimentos (Bom dia, boa tarde, etc.)\n"
            "- frases introdutórias\n"
            "- informações irrelevantes\n"
            "Retorne APENAS a pergunta final limpa."
        )
        
        try:
            cleaned = self.generate_response(
                prompt=f"Texto a ser limpo: \"{transcription}\"",
                system_instruction=system_instruction,
                temperature=0.0
            )
            return cleaned.strip().strip('"')
        except Exception as e:
            print(f"[GeminiClient] Erro ao limpar fala: {e}", file=sys.stderr)
            from voice.audio_utils import clean_transcript
            return clean_transcript(transcription)

    def generate_speech(self, text: str, output_dir: str, filename_prefix: str, persona: str = "duque_ia") -> str:
        """
        Gera áudio a partir de texto (Text-to-Speech) nativo do Gemini (Interactions API) ou fallbacks.
        Retorna o nome final do arquivo gerado (com extensão correta: .wav para Gemini, .mp3 para Translate/gTTS).
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Mapeamento de vozes suportadas pelo Gemini TTS conforme documentação oficial
        # Documentação de vozes: https://ai.google.dev/gemini-api/docs/speech-generation
        voice_map = {
            "duque_ia": "Charon",    # Voz institucional masculina (padrão)
            "ouvidoria": "Charon",   # Voz informativa/masculina
            "saude": "Vindemiatrix",  # Voz gentil/feminina
            "educacao": "Leda"       # Voz jovem/feminina
        }
        selected_voice = voice_map.get(persona, "Charon")

        # 1. Tentamos a síntese nativa do Gemini (saída em formato PCM raw → convertemos para WAV)
        if _USE_NEW_SDK:
            try:
                import base64
                import struct
                output_path_wav = os.path.join(output_dir, f"{filename_prefix}.wav")
                
                def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1, bits: int = 16) -> bytes:
                    """Empacota bytes PCM raw dentro de um cabeçalho RIFF WAV válido."""
                    byte_rate    = sample_rate * channels * bits // 8
                    block_align  = channels * bits // 8
                    data_size    = len(pcm_bytes)
                    chunk_size   = 36 + data_size

                    header = struct.pack(
                        '<4sI4s4sIHHIIHH4sI',
                        b'RIFF', chunk_size,      # RIFF header
                        b'WAVE',                   # Format
                        b'fmt ', 16,               # fmt chunk size
                        1,                         # PCM = 1
                        channels,
                        sample_rate,
                        byte_rate,
                        block_align,
                        bits,
                        b'data', data_size         # data chunk
                    )
                    return header + pcm_bytes

                def _call_tts():
                    prompt = f"Say in Portuguese: \"{text}\""
                    interaction = self._client.interactions.create(
                        model="gemini-3.1-flash-tts-preview",
                        input=prompt,
                        response_format={"type": "audio"},
                        generation_config={
                            "speech_config": [
                                {"voice": selected_voice}
                            ]
                        }
                    )
                    
                    if hasattr(interaction, "output_audio") and interaction.output_audio and interaction.output_audio.data:
                        # A Interactions API retorna PCM raw em base64 (sem cabeçalho WAV)
                        pcm_bytes = base64.b64decode(interaction.output_audio.data)
                        
                        # Obtém sample_rate reportado pela API (default 24000Hz)
                        sr = getattr(interaction.output_audio, "sample_rate", None) or 24000
                        ch = getattr(interaction.output_audio, "channels", None) or 1
                        print(f"[GeminiClient] PCM raw recebido: {len(pcm_bytes)} bytes | sample_rate={sr} | channels={ch}", file=sys.stderr)

                        # Empacota em WAV válido com cabeçalho RIFF
                        wav_bytes = _pcm_to_wav(pcm_bytes, sample_rate=sr, channels=ch)
                        with open(output_path_wav, "wb") as f:
                            f.write(wav_bytes)
                        print(f"[GeminiClient] WAV final salvo: {os.path.getsize(output_path_wav)} bytes", file=sys.stderr)
                        return True
                    raise ValueError("Nenhum dado de áudio retornado pelo modelo de TTS.")

                # Executa com rotação de chaves visando alta tolerância a falhas e timeout rígido de 10s
                import concurrent.futures
                success = False
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.execute_with_rotation, _call_tts, model_name="gemini-3.1-flash-tts-preview")
                    try:
                        success = future.result(timeout=10.0)
                    except concurrent.futures.TimeoutError:
                        print("[GeminiClient] Timeout de 10s atingido na Interactions API (TTS). Cancelando e usando fallback...", file=sys.stderr)
                    except Exception as tts_err:
                        print(f"[GeminiClient] Erro na thread de TTS: {tts_err}", file=sys.stderr)

                if success:
                    print(f"[GeminiClient] Áudio nativo do Gemini (WAV) gerado com a voz '{selected_voice}' em {output_path_wav}", file=sys.stderr)
                    return f"{filename_prefix}.wav"
            except Exception as e:
                print(f"[GeminiClient] Falha na síntese de áudio nativa via Interactions API: {e}. Usando fallback rápido do Google Translate...", file=sys.stderr)

        # 2. Fallback rápido direto via API do Google Translate (saída em formato MP3)
        output_path_mp3 = os.path.join(output_dir, f"{filename_prefix}.mp3")
        try:
            import urllib.request
            import urllib.parse
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=pt-br&client=tw-ob&q={encoded_text}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                audio_data = response.read()
                with open(output_path_mp3, "wb") as f:
                    f.write(audio_data)
            print(f"[GeminiClient] Áudio gerado via fallback do Google Translate (MP3) em {output_path_mp3}", file=sys.stderr)
            return f"{filename_prefix}.mp3"
        except Exception as e_translate:
            print(f"[GeminiClient] Falha no fallback do Google Translate: {e_translate}. Tentando gTTS...", file=sys.stderr)

        # 3. Fallback de último caso usando biblioteca gTTS (saída em formato MP3)
        try:
            from gtts import gTTS
            lang = "pt"
            tld = "com.br"
            tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
            tts.save(output_path_mp3)
            print(f"[GeminiClient] Áudio de fallback gTTS (MP3) gerado com sucesso em {output_path_mp3}", file=sys.stderr)
            return f"{filename_prefix}.mp3"
        except Exception as e:
            print(f"[GeminiClient] Falha em todos os métodos de TTS: {e}", file=sys.stderr)
            return ""

    def analyze_image(self, image_path: str) -> str:
        """Descreve e analisa imagem (ex: postes abertos, buracos, etc.) para estruturação do RAG."""
        prompt = (
            "Descreva detalhadamente o que está retratado nesta foto. "
            "Foque em identificar problemas de infraestrutura urbana, lixo, iluminação pública ou obras, "
            "e retorne uma descrição objetiva do fato."
        )
        
        def _call_new_sdk():
            uploaded_file = self._client.files.upload(file=image_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                resp = self._client.models.generate_content(
                    model=self.generation_model_name,
                    contents=[uploaded_file, prompt]
                )
                return resp.text.strip() if resp.text else ""
            finally:
                try:
                    self._client.files.delete(name=uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar imagem temporária: {ex}", file=sys.stderr)

        def _call_legacy_sdk():
            uploaded_file = genai.upload_file(path=image_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                model_obj = genai.GenerativeModel(model_name=self.generation_model_name)
                resp = model_obj.generate_content([uploaded_file, prompt])
                return resp.text.strip() if resp.text else ""
            finally:
                try:
                    genai.delete_file(uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar imagem temporária: {ex}", file=sys.stderr)

        func = _call_new_sdk if _USE_NEW_SDK else _call_legacy_sdk
        try:
            return self.execute_with_rotation(func, model_name=self.generation_model_name)
        except Exception as e:
            print(f"[GeminiClient] Falha ao analisar imagem: {e}", file=sys.stderr)
            return ""

    def analyze_pdf(self, pdf_path: str) -> str:
        """Analisa e resume documentos PDF usando a File API nativa do Gemini."""
        prompt = "Leia este documento PDF e forneça um resumo detalhado e estruturado das informações contidas nele."
        
        def _call_new_sdk():
            uploaded_file = self._client.files.upload(file=pdf_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                resp = self._client.models.generate_content(
                    model=self.generation_model_name,
                    contents=[uploaded_file, prompt]
                )
                return resp.text.strip() if resp.text else ""
            finally:
                try:
                    self._client.files.delete(name=uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar PDF temporário: {ex}", file=sys.stderr)

        def _call_legacy_sdk():
            uploaded_file = genai.upload_file(path=pdf_path)
            try:
                uploaded_file = self._wait_for_file_active(uploaded_file)
                model_obj = genai.GenerativeModel(model_name=self.generation_model_name)
                resp = model_obj.generate_content([uploaded_file, prompt])
                return resp.text.strip() if resp.text else ""
            finally:
                try:
                    genai.delete_file(uploaded_file.name)
                except Exception as ex:
                    print(f"[GeminiClient] Erro ao deletar PDF temporário: {ex}", file=sys.stderr)

        func = _call_new_sdk if _USE_NEW_SDK else _call_legacy_sdk
        try:
            return self.execute_with_rotation(func, model_name=self.generation_model_name)
        except Exception as e:
            print(f"[GeminiClient] Falha ao analisar PDF: {e}", file=sys.stderr)
            return ""
