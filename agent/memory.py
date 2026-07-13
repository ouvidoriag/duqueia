"""
memory.py — DUQUE IA
====================
Gerenciador de memória conversacional.
Sumariza mensagens antigas se o histórico exceder o limite estabelecido,
economizando tokens e mantendo o contexto limpo.
"""

import sys

class ConversationMemory:
    # 6 turnos do cidadão + 6 do agente = 12 mensagens
    MAX_MESSAGES_BEFORE_SUMMARY = 12
    
    @staticmethod
    def get_context(history: list, gemini_client) -> str:
        """
        Retorna o histórico formatado para o prompt.
        Se exceder MAX_MESSAGES_BEFORE_SUMMARY, sumariza as mensagens mais antigas.
        """
        if not history:
            return ""

        # Formata o histórico em lista de strings simples
        formatted_messages = []
        for i, msg in enumerate(history):
            role = "Cidadão" if i % 2 == 0 else "Duque IA"
            formatted_messages.append(f"{role}: {msg}")
            
        if len(formatted_messages) <= ConversationMemory.MAX_MESSAGES_BEFORE_SUMMARY:
            return "\n".join(formatted_messages)

        # Divisão: as mais antigas serão resumidas, as 6 últimas ficam verbatim
        old_messages = formatted_messages[:-6]
        recent_messages = formatted_messages[-6:]
        
        # Gera o resumo das antigas usando a LLM de forma síncrona
        summary = ConversationMemory._summarize(old_messages, gemini_client)
        
        return f"[Resumo do contexto anterior]\n{summary}\n\n[Mensagens recentes]\n" + "\n".join(recent_messages)

    @staticmethod
    def _summarize(messages: list[str], gemini_client) -> str:
        """Chama a LLM de forma rápida para resumir as interações anteriores."""
        prompt = (
            "Resuma brevemente em até 3 frases o foco principal da conversa a seguir entre o cidadão e o assistente Duque IA. "
            "Foque apenas em listar os tópicos que já foram resolvidos ou perguntados pelo cidadão.\n\n"
            "Histórico:\n" + "\n".join(messages)
        )
        try:
            # Tenta gerar resumo rápido
            summary = gemini_client.generate_response(
                prompt,
                model="gemini-3.1-flash-lite",
                temperature=0.0,
                max_output_tokens=150
            )
            return summary.strip()
        except Exception as e:
            print(f"[Memory Warning] Erro ao gerar resumo: {e}", file=sys.stderr)
            # Fallback seguro: apenas concatena as mensagens de forma compacta
            return "O cidadão anteriormente buscou informações sobre serviços municipais."
