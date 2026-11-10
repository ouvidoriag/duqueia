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

## 2. Health Check do Servidor
- **Rota:** `/health`
- **Método:** `GET`
- **Corpo da Resposta:**
  ```json
  {
    "status": "ok",
    "workers": 4,
    "busyWorkers": 0,
    "queueLength": 0
  }
  ```

## 3. Telemetria e Métricas
- **Rota:** `/api/telemetry`
- **Método:** `GET`
- **Parâmetros:** `?limit=200`
- **Descrição:** Retorna o histórico de telemetria agregada e tempos de resposta do pipeline RAG.

## 4. Recarga Administrativa de Workers
- **Rota:** `/api/admin/reload-workers`
- **Método:** `POST`
- **Descrição:** Recarrega os workers Python em pool sem derrubar a aplicação Node.js.

---
[Avançar: Autenticação](Autenticacao.md) | [Voltar ao Sumário](../README.md)
