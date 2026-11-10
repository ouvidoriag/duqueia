# Casos de Teste e Validações — Duque IA

A cobertura de testes automatizados do Duque IA abrange os seguintes cenários:

- **Triagem e Fallbacks (`test_triage_fallback.py`, `test_stateful_triage.py`)**: Valida o classificador de intenções sob diferentes insumos e diálogos com memória de estado.
- **Regressão Completa e Blindagem (`test_audit_regression_complete.py`)**: Valida bloqueio de CPFs, dados de terceiros (LGPD), fora de competência municipal, fast gate e anti-alucinação.
- **Fluxos Multi-Turno e Barulho (`test_barulho_multiturn.py`, `test_conversation_turn.py`)**: Valida manutenção de contexto em 3 turnos para reclamações de poluição sonora e transição suave para a Ouvidoria sem repetições.
- **Busca Híbrida e Relevância (`test_retrieval_relevance.py`, `test_rrf_fusion.py`)**: Testa a fidelidade da busca vetorial (cosseno) combinada com BM25/FTS5 via Reciprocal Rank Fusion.
- **Ontologia e Completude (`test_ontology.py`, `test_ontology_benchmark.py`, `test_completeness.py`)**: Valida a resolução de entidades municipais e acurácia ontológica de 100%.

---
[Avançar: Manutenção](../10-Manutencao/Checklist.md) | [Voltar: Testes](Testes.md)
