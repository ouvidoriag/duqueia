"""
mock_provider.py — DUQUE IA
============================
Provedor LLM determinístico para testes offline.
Zero chamadas de rede. Zero quota. Zero timeout.

Ativação: defina a variável de ambiente DUQUE_IA_TEST_MODE=1
antes de importar qualquer módulo do agente.

A classe MockLLMProvider implementa a mesma interface do GeminiClient,
tornando a substituição transparente — os testes não precisam mudar nada.
"""

import json
import re
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Fixtures: respostas pré-definidas para cada padrão de query
# ---------------------------------------------------------------------------
# Cada entrada é (regex_pattern, triage_json, rag_text)
# O primeiro match vence.
TRIAGE_FIXTURES = [
    # Segurança / LGPD
    (r"cpf|protocolo do vizinho|dados pessoais de terceiro",
     {"intent": "LGPD", "confidence": 1.0, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: LGPD bloqueado."}),

    # Fora de competência
    (r"metro|metr[oô]|rod[oô]via federal|bolsa fam[ií]lia|inss|receita federal",
     {"intent": "FORA_COMPETENCIA", "confidence": 1.0, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: fora da competência municipal."}),

    # Saudação
    (r"^(ol[aá]|oi|bom dia|boa tarde|boa noite|tudo bem|oi tudo)",
     {"intent": "SAUDACAO", "confidence": 0.99, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: saudação detectada."}),

    # Iluminação ambígua
    (r"sem luz|falta de luz|lâmpada|lampada|poste sem luz|rua sem luz",
     {"intent": "AMBIGUO_LUZ", "confidence": 0.90, "needs_clarification": True,
      "rewritten_query": None,
      "reason": "Mock: ambiguidade luz — concessionária ou iluminação pública?"}),

    # Barulho ambíguo
    (r"barulho|som alto|festa|algazarra|zoeira",
     {"intent": "AMBIGUO_BARULHO", "confidence": 0.88, "needs_clarification": True,
      "rewritten_query": None,
      "reason": "Mock: ambiguidade barulho — vizinho ou evento público?"}),

    # Ouvidoria / Possível denúncia
    (r"xingou|tratou mal|grosseiro|grosseira|ofendeu|mal educado|humilhou|ameaçou|ameacou|destratou|mal atendido|mal atendida",
     {"intent": "POSSIVEL_DENUNCIA", "confidence": 0.95, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: relato de conduta inadequada."}),

    # Ouvidoria
    (r"quero reclamar|registrar reclama|abrir manifesta|ouvidoria|protocolo",
     {"intent": "OUVIDORIA_MANIFESTACAO", "tipo_manifestacao": "reclamacao",
      "confidence": 0.95, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: manifestação na ouvidoria."}),

    # Autoridade Pública
    (r"prefeito|vice-prefeito|vice prefeito|secretário|secretario|secretária|secretaria|ouvidor|procurador|controlador",
     {"intent": "AUTORIDADE_PUBLICA", "confidence": 0.98, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: busca de autoridade pública."}),

    # Identidade
    (r"quem [eé] voc[eê]|o que voc[eê] faz|para que serve|duque ia",
     {"intent": "IDENTIDADE", "confidence": 0.99, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: pergunta de identidade."}),

    # Programação
    (r"python|javascript|c\+\+|c#|código|programa[çc][ãa]o|script",
     {"intent": "PROGRAMACAO", "confidence": 1.0, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: programação bloqueada."}),

    # RAG Geral (default)
    (r".*",
     {"intent": "RAG_GERAL", "confidence": 0.85, "needs_clarification": False,
      "rewritten_query": None, "reason": "Mock: RAG geral."}),
]

RAG_RESPONSES = {
    "iptu": (
        "O IPTU (Imposto Predial e Territorial Urbano) em Duque de Caxias pode ser pago "
        "na **Secretaria Municipal de Fazenda**, localizada na Av. Presidente Kennedy, nº 1, "
        "Centro. Telefone: **(21) 2672-6200**. Você também pode acessar o portal online "
        "da prefeitura para emissão de boletos."
    ),
    "prefeito": (
        "O prefeito de Duque de Caxias é **Wilson Leite Reis** (Netinho do Posto). "
        "Ele está no **segundo mandato** à frente do município."
    ),
    "secretaria": (
        "Duque de Caxias possui diversas secretarias municipais, entre as principais: "
        "Secretaria de Saúde, Secretaria de Educação, Secretaria de Fazenda, Secretaria de Obras, "
        "Secretaria de Assistência Social, entre outras. "
        "Para informações de contato, acesse o portal da Prefeitura."
    ),
    "ouvidoria": (
        "A **Ouvidoria Geral de Duque de Caxias** pode ser acessada pelos canais: "
        "📞 Telefone: **(21) 2652-3835** | WhatsApp: **(21) 99824-5903** "
        "Você também pode registrar sua manifestação pelo app **Colab**."
    ),
    "default": (
        "Com base nas informações disponíveis, recomendo entrar em contato diretamente com "
        "a secretaria responsável ou acesse o portal da Prefeitura de Duque de Caxias "
        "em www.duquedecaxias.rj.gov.br para mais detalhes sobre este serviço."
    )
}


def _match_rag(query: str) -> str:
    """Retorna resposta RAG mock baseada em palavras-chave."""
    q = query.lower()
    for key, resp in RAG_RESPONSES.items():
        if key != "default" and key in q:
            return resp
    return RAG_RESPONSES["default"]


def _match_triage(query: str) -> dict:
    """Retorna o resultado de triagem mock mais adequado à query."""
    q = query.lower()
    for pattern, result in TRIAGE_FIXTURES:
        if re.search(pattern, q, re.IGNORECASE):
            r = dict(result)
            # Preenche rewritten_query com a query original se não definida
            if r.get("rewritten_query") is None:
                r["rewritten_query"] = query
            return r
    return TRIAGE_FIXTURES[-1][1]  # RAG_GERAL default


# ---------------------------------------------------------------------------
# MockLLMProvider
# ---------------------------------------------------------------------------

class MockLLMProvider:
    """
    Substituto determinístico do GeminiClient para testes.
    Implementa a mesma interface pública do GeminiClient.
    """

    # Simula lista de chaves não-vazia para que using_real = True no agente
    api_keys = ["mock-key-for-testing"]

    def __init__(self, latency_ms: float = 5.0):
        self._latency = latency_ms / 1000.0
        self._call_log: list[dict] = []
        # Mantém compatibilidade com atributos do GeminiClient
        self.current_key_index = 0
        self.key_cooldowns = {0: 0.0}
        self.embedding_model_name = "gemini-embedding-2"
        self.generation_model_name = "mock-gemini-lite"
        self._working_embedding_model = "gemini-embedding-2"
        self._client = None

    # ------------------------------------------------------------------
    # Interface principal: generate_response
    # ------------------------------------------------------------------
    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: int = 800,
        **kwargs
    ) -> str:
        """Simula uma chamada de geração de texto. Retorna resposta determinística."""
        time.sleep(self._latency)
        self._log("generate_response", prompt)
        
        # Detecta output guardrail
        if "Agente de Blindagem e Auditoria" in prompt:
            return "PERMITIDO"

        # Detecta se é um prompt de triagem (contém campos JSON esperados)
        if '"intent"' in prompt or "Categorias permitidas" in prompt or "RAG_GERAL" in prompt:
            query = self._extract_query_from_prompt(prompt)
            result = _match_triage(query)
            return json.dumps(result, ensure_ascii=False)

        # Detecta prompt de reescrita de query
        if "reescreva" in prompt.lower() or "rewrite" in prompt.lower() or "reformule" in prompt.lower():
            query = self._extract_query_from_prompt(prompt)
            return query  # Retorna a query sem modificação

        # Detecta prompt de relato ou possível denúncia
        if system_instruction and "possível denúncia" in system_instruction.lower():
            return (
                "Sinto muito pelo ocorrido. Se essa situação aconteceu com um servidor público municipal "
                "ou durante um atendimento da Prefeitura de Duque de Caxias, você pode registrar uma manifestação "
                "(reclamação ou denúncia) nos canais oficiais da nossa Ouvidoria Geral pelo aplicativo Colab."
            )

        # Detecta prompt de clarificação / esclarecimento
        if "clarif" in prompt.lower() or "esclarecimento" in prompt.lower():
            return "Poderia esclarecer melhor sua dúvida? Qual serviço ou local você está procurando?"

        # Detecta planner (retorna plano JSON)
        if '"queries"' in prompt or "plano de busca" in prompt.lower():
            query = self._extract_query_from_prompt(prompt)
            return json.dumps({
                "intent": "service_location",
                "queries": [query],
                "focus": ["general"]
            }, ensure_ascii=False)

        # Resposta RAG padrão
        query = self._extract_query_from_prompt(prompt)
        return _match_rag(query)

    # ------------------------------------------------------------------
    # Interface de interação (RAG com interaction_id)
    # ------------------------------------------------------------------
    def generate_interaction(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        previous_interaction_id: Optional[str] = None,
        model: Optional[str] = None,
        max_output_tokens: int = 800,
        **kwargs
    ) -> tuple:
        """Simula generate_interaction. Retorna (texto, interaction_id, model_name)."""
        time.sleep(self._latency)
        self._log("generate_interaction", prompt)
        query = self._extract_query_from_prompt(prompt)
        text = _match_rag(query)
        interaction_id = f"mock_interaction_{hash(prompt) & 0xFFFF:04x}"
        return text, interaction_id, self.generation_model_name

    # ------------------------------------------------------------------
    # Interface de embedding
    # ------------------------------------------------------------------
    def get_embedding(self, text: str, is_query: bool = False) -> list:
        """Retorna embedding mock com dimensão fixa (compatível com 3072)."""
        time.sleep(self._latency)
        self._log("get_embedding", text[:50])
        # Gera vetor deterministico baseado no hash do texto
        import hashlib
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        import random
        rng = random.Random(seed)
        vec = [rng.gauss(0, 1) for _ in range(3072)]
        # Normaliza
        norm = sum(x * x for x in vec) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------
    def _extract_query_from_prompt(self, prompt: str) -> str:
        """Extrai a query do cidadão de dentro de um prompt longo."""
        # Tenta encontrar padrão: "Consulta atual do cidadão: "query""
        m = re.search(r'(?:Consulta|Mensagem|Pergunta|query)[^:]*:\s*["\']([^"\']{5,})["\']', prompt, re.IGNORECASE)
        if m:
            return m.group(1)
        # Fallback: última linha não-vazia
        lines = [l.strip() for l in prompt.strip().split("\n") if l.strip()]
        return lines[-1] if lines else prompt[:100]

    def _log(self, method: str, content: str):
        self._call_log.append({
            "method": method,
            "content": content[:100],
            "at": time.time()
        })

    def get_call_log(self) -> list:
        """Retorna o histórico de chamadas (útil para assertions nos testes)."""
        return list(self._call_log)

    def reset_log(self):
        self._call_log.clear()


# ---------------------------------------------------------------------------
# Integração: patch transparente do GeminiClient
# ---------------------------------------------------------------------------

def install_mock_if_test_mode():
    """
    Verifica DUQUE_IA_TEST_MODE e, se ativo, substitui o GeminiClient
    por MockLLMProvider antes que qualquer módulo do agente seja importado.
    
    Chamar no início de cada script de teste:
        from utils.mock_provider import install_mock_if_test_mode
        install_mock_if_test_mode()
    
    Ou definir DUQUE_IA_TEST_MODE=1 no ambiente e deixar o GeminiClient
    detectar automaticamente.
    """
    import os
    if os.getenv("DUQUE_IA_TEST_MODE", "").strip() == "1":
        import utils.gemini_client as gc_module
        gc_module.GeminiClient = MockLLMProvider  # type: ignore[attr-defined]
        import sys
        print("[MockProvider] DUQUE_IA_TEST_MODE=1 — API interceptada pelo MockLLMProvider.", file=sys.stderr)
        return True
    return False
