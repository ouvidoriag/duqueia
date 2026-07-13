# Autenticação e Segurança da API — Duque IA

## Escopo Público
O endpoint `/api/chat` opera de forma pública sem autenticação via token (JWT) para possibilitar a integração com o portal do cidadão.

## Sessões
- O controle de sessão é feito via identificador único (`sessionId`) enviado no corpo das requisições pelo cliente.
- O Node.js isola processos Python por `sessionId` e limpa sessões inativas automaticamente após 30 minutos de inatividade para evitar vazamento de memória ou locks.

---
[Avançar: Exemplos](Exemplos.md) | [Voltar: Endpoints](Endpoints.md)
