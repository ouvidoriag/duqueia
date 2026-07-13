# Casos de Teste e Validações — Duque IA

A cobertura de testes automatizados do Duque IA abrange os seguintes cenários:

- **Triagem (`test_triage.py`)**: Valida o classificador de intenções sob diferentes insumos e diálogos.
- **Guardrails (`test_guardrails.py`)**: Valida bloqueio de CPFs, dados de terceiros (LGPD) e fora de competência municipal.
- **Turnos de Conversa (`test_conversation_turn.py`)**: Valida se saudações são omitidas no segundo turno de mensagens.
- **Busca Híbrida (`test_retrieval.py`)**: Testa a fidelidade da busca vetorial local contra chaves lexicais.

---
[Avançar: Manutenção](../10-Manutencao/Checklist.md) | [Voltar: Testes](Testes.md)
