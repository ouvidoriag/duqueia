# Endpoints da API — Duque IA

O servidor backend HTTP fornece uma API simples para interação com a interface cliente de atendimento.

## 1. Enviar Mensagem (Chat)
- **Rota:** `/api/chat`
- **Método:** `POST`
- **Headers:** `Content-Type: application/json`
- **Corpo da Requisição:**
  ```json
  {
    "message": "Qual o endereço da secretaria de saúde?",
    "sessionId": "sess_12345"
  }
  ```
- **Corpo da Resposta:**
  ```json
  {
    "answer": "A Secretaria Municipal de Saúde fica na Alameda James Franco, nº 3, Jardim Primavera, Duque de Caxias/RJ.",
    "sources": [],
    "confidence": 0.95,
    "intent_detected": "gis",
    "conversation_id": "sess_12345"
  }
  ```

---
[Avançar: Autenticação](Autenticacao.md) | [Voltar ao Sumário](../README.md)
