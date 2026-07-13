# Controllers do Backend — Duque IA

O backend é orquestrado pelo arquivo principal `server.js` utilizando bibliotecas nativas do Node.js.

## Controle de Requisições HTTP
O servidor intercepta chamadas na porta configurada e roteia de acordo com a URL requisitada:
- Requisições estáticas para `/public/*` são resolvidas lendo arquivos físicos da pasta.
- Chamadas para `/api/chat` são deserializadas e enviadas ao serviço gerenciador do agente Python.

---
[Avançar: Services](Services.md) | [Voltar ao Sumário](../README.md)
