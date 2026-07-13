# Engenharia de Prompts — Duque IA

O Duque IA baseia seu comportamento conversacional e restrições de escopo por meio de instruções de sistema configuradas no cliente Gemini.

## Diretrizes de Resposta Conversacional (POP)
As instruções proíbem expressamente saudações como "Olá" ou "Oi" quando o histórico de diálogo estiver preenchido (`history` não vazio):
```python
if history:
    system_instruction += (
        "\nREGRA DE CONVERSA EM ANDAMENTO:\n"
        "- A conversa já está em andamento. NUNCA comece a resposta com saudações, saudações de boas-vindas, ou cumprimentos (como 'Olá', 'Oi', 'Bom dia', 'Tudo bem', 'Que bom ver você', etc.).\n"
        "- Vá direto para o assunto e inicie a resposta diretamente com os dados factuais solicitados."
    )
```

---
[Avançar: Fluxos](Fluxos.md) | [Voltar ao Sumário](../README.md)
