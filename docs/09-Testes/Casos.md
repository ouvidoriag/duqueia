# Casos de Teste e Validações — Duque IA

A cobertura de testes automatizados do Duque IA é estruturada em camadas, garantindo conformidade funcional, segurança jurídica e performance extrema:

---

## 1. Camada Golden Source & Resolução Determinística (`test_entity_resolver.py`)
- **Cobertura de 443 Unidades Físicas:** Valida busca e formatação de endereços com CEP, telefones oficiais, horário de atendimento e secretaria vinculada para CRAS, CREAS, UPAs 24h, UPHs 24h, Hospitais, Clínicas da Família, Escolas, Creches, Polos FUNDEC, Conselhos Tutelares e Defesa Civil.
- **Detecção de 152 Bairros & Apelidos:** Valida tolerância fonética e correspondência de nomes populares locais (*"Dr. Laureano"*, *"25 de Agosto"*, *"Pantanal"*).
- **Listagens Consolidadas:** Valida consultas agregadas por tipo de equipamento (*"Quais as UPAs de Caxias?"*, *"Onde tem CRAS?"*).
- **Blindagem Procedimental:** Assegura que perguntas de serviços (*"como solicitar poda"*, *"como pagar IPTU"*) **não** sejam interceptadas como locais físicos, sendo encaminhadas com 100% de integridade ao RAG.
- **Critério de Latência:** Assegura que 100 consultas executadas em série mantenham tempo médio `< 10 ms` (meta superada com média de 0,79ms).

---

## 2. Integridade de Banco & Recuperação Semântica (`test_structured_db.py`, `test_bancoduqueia_retrieval.py`)
- **Validação de Esquema Relacional:** Checagem da integridade de chaves estrangeiras e índices das 23 tabelas do `data/db/main.db` e view `vw_ia_servicos`.
- **Top 5 Consultas Canônicas:** Validação de FTS5 com peso de boost para:
  1. Castração de cães / Petzap (SMPA)
  2. Quebra-molas (SMSP / SMOAG)
  3. Procuradoria Geral do Município (PGM)
  4. Guarda Municipal e Segurança Pública
  5. Ônibus Tarifa Zero (Linhas Municipais Gratuitas)

---

## 3. Autoridades Públicas e Segurança Legal (`test_autoridade_publica.py`, `test_audit_regression_complete.py`)
- **Autoridades Municipais:** Respostas canônicas instantâneas sobre quem é o Prefeito, Vice-Prefeito, Secretários e Ouvidor Geral.
- **Proteção e Privacidade LGPD:** Bloqueio de consultas sobre CPFs, andamento de protocolos e dados pessoais de terceiros/vizinhos.
- **Competência Municipal:** Rejeição fundamentada de perguntas sobre metrô, previdência federal, rodovias federais ou outros municípios.

---

## 4. Contexto Multi-Turno e Agente Coletor (`test_barulho_multiturn.py`, `test_conversation_turn.py`, `test_ambiguity.py`)
- **Janela de 3 Turnos:** Valida persistência de memória de diálogo sem perda de intenção em casos de poluição sonora (*som alto*).
- **Coleta Incremental:** Valida o comportamento de pedir apenas uma informação por vez ao munícipe antes de direcioná-lo à plataforma Colab.
- **Desambiguação Contextual:** Identificação de quando uma ambiguidade anterior foi respondida pelo munícipe no turno subsequente.

---

## 5. RAG Híbrido e RRF (`test_retrieval_relevance.py`, `test_rrf_fusion.py`)
- **Acurácia RRF:** Fusão balanceada entre a similaridade de cosseno densa (vetor 3072 dim) e a busca textual esparsa BM25/FTS5.
- **Recall e Precisão:** Manutenção contínua de Recall `>= 95%` e Taxa de Falso Negativo `<= 3%`.

---
[Avançar: Manutenção](../10-Manutencao/Checklist.md) | [Voltar: Testes](Testes.md)

