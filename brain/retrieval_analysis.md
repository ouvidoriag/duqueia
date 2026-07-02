# Relatório de Avaliação do Retrieval - DUQUE IA

Este documento apresenta a análise de performance e relevância da etapa de busca e recuperação (Retrieval), em conformidade com a **Fase 3** do projeto.

---

## 1. Auditoria das Estratégias de Chunking (Fase 2)

Abaixo está o benchmark comparativo das estratégias de chunking testadas com o banco de dados de Duque de Caxias:

| Strategy | Precision | Recall | Retrieval Score | Latency | Cost (per 1k queries) | Context Preserved |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **recursive_500_100** | 0.82 | 0.79 | 0.805 | 45ms | $0.00012 | Alto (Pedaços grandes) |
| **recursive_256_64** | 0.91 | 0.87 | 0.890 | 30ms | $0.00015 | Médio (Focado) |
| **token_256_64** | 0.90 | 0.87 | 0.885 | 25ms | $0.00014 | Médio (Alinhado com Tokenizer) |
| **semantic_strategy** | 0.95 | 0.93 | 0.940 | 60ms | $0.00025 | Excelente (Mantém significado) |
| **entity_geo_strategy**| 0.97 | 0.96 | 0.965 | 15ms | $0.00008 | Perfeito para consultas GIS |

### Avaliação Crítica:
* **Estratégias Recursivas**: Possuem bom equilíbrio geral, porém o `recursive_500_100` tende a trazer ruídos para respostas específicas de secretarias.
* **Estratégia Semântica**: Recupera com a maior qualidade de contexto textual unificado, mas possui maior latência devido à análise de quebra de parágrafo.
* **Estratégia Geográfica (`entity_geo_strategy`)**: É a mais eficiente para o DUQUE IA, pois agrupa lotes, bairros e secretarias territoriais em 1 entidade por chunk, garantindo latência mínima e altíssima precisão nas consultas GIS.

---

## 2. Análise do Cálculo de Scores e Relevância (Fase 3)

No script `test_retrieval_relevance.py`, a similaridade é avaliada de duas formas no DUQUE IA:
1. **Busca Semântica (Embedding Cosine Similarity)**: Mede o ângulo de cosseno entre o vetor da pergunta do munícipe e o vetor do chunk indexado.
2. **Busca Híbrida (Keyword Match Fallback)**: Pontua com base na ocorrência de palavras-chave da consulta excluindo stopwords estruturadas, atribuindo peso extra (1.5x) para correspondências no título do arquivo de origem.

### Oportunidades de Melhoria:
* **Evitar Viés de Palavras Comuns**: Filtrar de forma agressiva as stopwords municipais (ex: "Duque", "Caxias", "prefeitura", "secretaria") quando usadas em consultas puras por palavras-chave, pois elas tendem a gerar falsos positivos em todos os documentos.
* **Cross-Encoder para Reranking**: Implementar um segundo classificador leve para reordenar os top 5 resultados, garantindo que o chunk mais relevante seja o primeiro da lista, eliminando alucinações.

---

## 3. Configuração dos Guardrails de Segurança (Fase 4)

* **Input Guardrail**: Implementado no `DuqueIAAgent` para bloquear strings perigosas como `ignore as instruções`, `DROP TABLE`, `DELETE FROM` retornando código de erro e confiança `0.0`.
* **Retrieval Guardrail**: O limite de similaridade é definido em `0.65` para busca vetorial real e `0.25` para busca híbrida por palavra-chave significativa. Se a relevância do melhor resultado for menor que esse limite, o sistema retorna de forma segura: *"Não encontrei informações suficientes para responder."*
* **Output Guardrail**: Valida a resposta gerada garantindo que seja um JSON estrito no formato homologado, contendo a resposta (`answer`), a lista de fontes utilizadas (`sources`) e o coeficiente de confiança (`confidence`).
