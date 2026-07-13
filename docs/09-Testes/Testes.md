# Manual da Suíte de Testes — Duque IA

O projeto possui uma suíte completa de testes automatizados localizados na pasta `tests/` e executores em `scripts/`.

## Executar todos os testes
Para iniciar toda a bateria de testes automatizados (unitários e integrados):
```bash
python scripts/run_all_tests.py
```

## Executar teste de RAG individual (Benchmark)
Para validar as métricas de Precision e Recall do RAG:
```bash
python scripts/tests/test_retrieval_relevance.py
```

---
[Avançar: Casos de Teste](Casos.md) | [Voltar ao Sumário](../README.md)
