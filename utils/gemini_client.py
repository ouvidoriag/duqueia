import sys
import os
import time
import warnings

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
        self.embedding_model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
        self.generation_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
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

        print("[GeminiClient] Nenhum modelo de embedding disponivel. Usando fallback local.", file=sys.stderr)
        return self._local_fallback_embedding(text)

    # --------------------------------------------------------------------------
    # GERACAO DE TEXTO
    # --------------------------------------------------------------------------
    def generate_interaction(self, prompt: str, system_instruction: str = None, model: str = None, previous_interaction_id: str = None, temperature: float = None, max_output_tokens: int = None) -> tuple:
        """Gera resposta usando a Interactions API do Gemini e retorna (texto_resposta, new_interaction_id, working_model)."""
        if not self.api_keys:
            return "Desculpe, o sistema esta rodando sem chaves de API ativas.", None, None

        requested_model = model if model else self.generation_model_name
        models_to_try = [requested_model]
        
        # Fallbacks padrão se o solicitado falhar (apenas modelos testados e suportados)
        default_fallbacks = [
            "gemini-2.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-3.5-flash"
        ]
        for m in default_fallbacks:
            if m not in models_to_try:
                models_to_try.append(m)

        # Valida o previous_interaction_id: só passa para a API se for um ID real do Gemini
        # IDs internos de sessão (ex: sess_XXXXXXXX) nunca devem ser enviados à API
        valid_interaction_id = None
        if previous_interaction_id and not previous_interaction_id.startswith("sess_"):
            valid_interaction_id = previous_interaction_id

        last_exception = None
        for current_model in models_to_try:
            try:
                if _USE_NEW_SDK:
                    def _call(m=current_model):
                        try:
                            call_kwargs = {
                                "model": m,
                                "input": prompt,
                                "previous_interaction_id": valid_interaction_id,
                            }
                            if system_instruction:
                                call_kwargs["system_instruction"] = system_instruction
                            resp = self._client.interactions.create(**call_kwargs)
                            return resp.output_text, resp.id
                        except Exception as e:
                            err_msg = str(e).lower()
                            if "not_found" in err_msg or "404" in err_msg or "method not found" in err_msg or "requested entity was not found" in err_msg:
                                print(f"[GeminiClient] Interactions API não suportada ou 404 para o modelo {m}. Caindo para generate_content...", file=sys.stderr)
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
                            raise e
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
                print(f"[GeminiClient] Falha com o modelo {current_model} na interaction: {e}. Tenta próximo de fallback.", file=sys.stderr)
                time.sleep(0.5)

        raise last_exception if last_exception else RuntimeError("Todos os modelos falharam na geração de interação.")


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
