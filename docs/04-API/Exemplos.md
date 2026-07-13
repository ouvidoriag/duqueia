# Exemplos de Requisição da API — Duque IA

Você pode testar a API do Duque IA localmente usando a ferramenta `curl` em sua linha de comando:

```bash
curl -X POST http://localhost:3000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Olá", "sessionId": "test_session_1"}'
```

Resposta esperada:
```json
{
  "answer": "Olá! Sou o **DUQUE IA**, assistente virtual da Prefeitura de Duque de Caxias.\n\nComo posso ajudar você hoje?",
  "sources": [],
  "confidence": 1.0,
  "intent_detected": "saudacao",
  "conversation_id": "test_session_1"
}
```

---
[Avançar: Frontend](../05-Frontend/Estrutura.md) | [Voltar: Autenticação](Autenticacao.md)
