import sys
import os
import time

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

# Modelos Groq verificados e ativos (testados em 25/06/2026)
_GROQ_MODELS = {
    "fast": "llama-3.1-8b-instant",     # Triagem, coleta, respostas simples — 560 tokens/s
    "quality": "llama-3.3-70b-versatile", # Respostas complexas, RAG — mais inteligente
}

# Ordem de fallback (rápido primeiro, depois qualidade)
_GROQ_MODELS_FALLBACK = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
]


class GroqClient:
    """
    Cliente wrapper para a API da Groq (LLaMA ultrarrápido).
    Compatível com a interface do GeminiClient para uso em rotação.
    Não suporta embeddings (usa Gemini para isso).
    """

    def __init__(self):
        if not _GROQ_AVAILABLE:
            print("[GroqClient] AVISO: pacote 'groq' não instalado. Execute: pip install groq", file=sys.stderr)
            self._client = None
            self.api_key = None
            self.api_keys = []
            return

        self.api_key = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            print("[GroqClient] AVISO: GROQ_API_KEY não configurada no .env", file=sys.stderr)
            self._client = None
            self.api_keys = []
            return

        masked = self.api_key[:8] + "..." + self.api_key[-8:]
        print(f"[GroqClient] Inicializado com chave: {masked}", file=sys.stderr)
        self._client = Groq(api_key=self.api_key)
        self.api_keys = [self.api_key]
        self.generation_model_name = os.getenv("GROQ_MODEL", _GROQ_MODELS["fast"])
        self.quality_model_name = os.getenv("GROQ_QUALITY_MODEL", _GROQ_MODELS["quality"])

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate_response(
        self,
        prompt: str,
        system_instruction: str = None,
        model: str = None,
        prefer_quality: bool = False
    ) -> str:
        """
        Gera resposta de texto via Groq.
        Args:
            prefer_quality: Se True, usa llama-3.3-70b em vez do 8b rápido.
        """
        if not self.available:
            raise RuntimeError("GroqClient não disponível (chave ausente ou pacote não instalado).")

        # Seleciona modelo base
        if model:
            base_model = model
        elif prefer_quality:
            base_model = self.quality_model_name
        else:
            base_model = self.generation_model_name

        # Monta fallback em ordem
        models_to_try = [base_model] + [m for m in _GROQ_MODELS_FALLBACK if m != base_model]

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        last_exception = None
        for current_model in models_to_try:
            try:
                print(f"[GroqClient] Gerando com {current_model}...", end=" ", flush=True, file=sys.stderr)
                resp = self._client.chat.completions.create(
                    messages=messages,
                    model=current_model,
                    temperature=0.3,
                    max_tokens=1024,
                )
                text = resp.choices[0].message.content.strip()
                tokens = resp.usage.total_tokens if resp.usage else "?"
                print(f"OK ({tokens} tokens)", file=sys.stderr)
                return text
            except Exception as e:
                last_exception = e
                err = str(e)[:80]
                print(f"FALHOU: {err}", file=sys.stderr)
                time.sleep(0.3)

        raise last_exception or RuntimeError("Todos os modelos Groq falharam.")

    def generate_triage(self, prompt: str, system_instruction: str = None) -> str:
        """
        Versão otimizada para triagem: usa modelo rápido (8b) por padrão.
        """
        return self.generate_response(
            prompt,
            system_instruction=system_instruction,
            model=self.generation_model_name,
            prefer_quality=False
        )
