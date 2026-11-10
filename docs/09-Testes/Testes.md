# Manual da Suíte de Testes — Duque IA

O projeto possui uma infraestrutura de testes automatizados e ferramentas de diagnóstico localizadas na pasta `scripts/tests/`, cobrindo desde a integridade física do SQLite até a resolução determinística sub-10ms e guardrails de segurança.

---

## 1. Diagnóstico e Verificação de Saúde (Health Check)
Para verificar a integridade operacional dos 4 bancos SQLite, modo WAL, runtime e variáveis de ambiente:
```bash
python setup_and_run.py --health
```

---

## 2. Testes da Camada Golden Source (443 Unidades)
Valida a resolução determinística instantânea de todas as categorias de equipamentos públicos (CRAS, UPAs, Hospitais, Escolas, FUNDEC), além da blindagem procedimental e latência sub-10ms:
```bash
python scripts/tests/test_entity_resolver.py
```
*(Executa 26 testes unitários em ~0.15s com 100% de aprovação)*

---

## 3. Testes de Banco Estruturado e Recuperação Canônica
Valida as 23 tabelas do `main.db`, a view `vw_ia_servicos` e as 5 consultas canônicas do banco unificado:
```bash
# Validação estrutural das tabelas e views
python scripts/tests/test_structured_db.py

# Teste de recuperação semântica FTS5 / Boost de regras
python scripts/tests/test_bancoduqueia_retrieval.py
```

---

## 4. Testes de Autoridades Públicas e LGPD
Valida se as consultas de autoridades políticas (Prefeito, Vice, Secretários) são respondidas com exatidão:
```bash
python scripts/tests/test_autoridade_publica.py
```

---

## 5. Bateria Geral Automatizada
Para executar a suíte de testes consolidados da aplicação:
```bash
python scripts/run_all_tests.py
```

---
[Avançar: Casos de Teste](Casos.md) | [Voltar ao Sumário](../README.md)

