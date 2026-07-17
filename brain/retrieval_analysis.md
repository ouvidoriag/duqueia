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

### Oportunidades de Melhoria e Riscos de Overfitting:
* **Risco de Overfitting por Regras Estáticas:** Regras de reescrita estáticas trazem alto retorno rápido, mas geram viés e falham se o cidadão usar expressões sinônimas não previstas. O sistema deve transicionar gradualmente para um modelo LLM Dinâmico de *Query Rewriting* em produção.
* **Filtros de Metadados baseados em Intenção:** Separar dinamicamente os escopos de busca (Secretarias vs. Carta de Serviços vs. Unidades Físicas) impede a contaminação de domínios.

---

## 3. Configuração dos Guardrails de Segurança (Fase 4)

* **Input Guardrail**: Bloqueia injeção de SQL e instruções nocivas diretamente na entrada.
* **Retrieval Guardrail**: Define um limiar dinâmico. Se a melhor correspondência de similaridade for menor que `0.65` (vetorial) ou `0.25` (híbrido significativo), aborta com a mensagem de fallback da Ouvidoria Geral.
* **Output Guardrail**: Valida a conformidade da estrutura JSON da resposta antes de enviá-la ao munícipe.
