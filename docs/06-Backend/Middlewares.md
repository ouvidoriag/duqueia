# Middlewares do Backend — Duque IA

Embora o Node.js não utilize Express, o servidor `server.js` implementa proteções equivalentes a middlewares:

- **Controle de Timeout**: Destrói processos Python inativos após 30 minutos sem mensagens recebidas.
- **Tratamento de Exceções**: Se o processo do agente Python cair de forma inesperada, o servidor captura a falha e reinicia a sessão de forma transparente, retornando uma resposta padrão amigável ao cliente.

---
[Avançar: Inteligência Artificial](../07-IA/Prompts.md) | [Voltar: Services](Services.md)
