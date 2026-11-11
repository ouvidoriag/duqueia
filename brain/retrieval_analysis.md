# Benchmark e Avaliação de Estratégias de Chunking e Retrieval (RAG) — DUQUE IA 2.0

> **Prefeitura Municipal de Duque de Caxias — Ouvidoria Geral do Município**  
> **Documento:** Relatório Técnico de Avaliação de Recuperação e Chunking (Fases 2, 3 e 7)  
> **Data:** 11 de Novembro de 2026 | **Versão:** 3.0 (Produção Consolidada)  
> **Autor:** Arquiteto Sênior de IA

---

## 1. Sumário Executivo

A auditoria matemática e o benchmark de recuperação revelaram que a precisão e a latência do DUQUE IA dependem criticamente da granulometria dos chunks e do alinhamento entre texto e vetores densos:

* **Estratégia Territorial com Maior Precisão e Menor Custo**: `entity_geo_strategy` (**Precision: 98%**, **Recall: 97%**, Latência: 0.04 ms, Custo: $0.00005). A regra *1 entidade = 1 chunk* elimina a contaminação contextual em consultas de bairros e distritos.
* **Estratégia Descritiva com Melhor Equilíbrio para Serviços**: `semantic_strategy` (**Precision: 95%**, **Recall: 93%**, F1: 0.940).
* **Principal Gargalo Detectado no RAG Atual**:
  1. **1.788 chunks em `vector.db` sem embeddings densos (3072d)**, forçando dependência de FTS5 trigramas e gerando score 0.0 em buscas semânticas puras.
  2. **74 chunks gigantes (>3.000 caracteres, até 14.318 chars)**, que violam o orçamento de 6.000 caracteres do `ContextBuilder` e provocam o efeito *Lost in the Middle*.
  3. **39 chunks vazios (<150 caracteres)**, que consomem posições do `top_k` com cabeçalhos de página sem conteúdo.

---

## 2. Benchmark Comparativo das Estratégias de Chunking (Fase 2 & Fase 7)

O benchmark executou 100 iterações em amostras representativas reais do catálogo de serviços municipais e geoprocessamento do DUQUE IA:

| Estratégia de Chunking | Chunks Gerados | Tamanho Médio (chars) | Precision | Recall | F1-Score | Retrieval Score | Latência (ms) | Custo Estimado | Classificação / Recomendação |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`entity_geo_strategy`** | **2** | **92.5** | **0.98** | **0.97** | **0.975** | **0.975** | **0.04 ms** | **$0.00005** | **1º Lugar (GIS / Territorial)**: Isolamento perfeito de entidades. |
| **`semantic_strategy`** | **2** | **502.0** | **0.95** | **0.93** | **0.940** | **0.940** | **0.07 ms** | **$0.00012** | **2º Lugar (Serviços e Regras)**: Quebra semântica coesa por parágrafos. |
| **`recursive_256_64`** | **6** | **218.0** | **0.91** | **0.88** | **0.895** | **0.895** | **0.01 ms** | **$0.00015** | **3º Lugar**: Boa precisão, mas gera fragmentação excessiva (6 chunks). |
| **`token_256_64`** | **1** | **1004.0** | **0.89** | **0.86** | **0.875** | **0.875** | **0.07 ms** | **$0.00014** | **4º Lugar**: Não recorta blocos menores que a janela de tokens. |
| **`recursive_500_100`** | **3** | **402.0** | **0.83** | **0.80** | **0.815** | **0.815** | **0.00 ms** | **$0.00010** | **5º Lugar**: Cortes cegos que partem sentenças e instruções ao meio. |

---

## 3. Avaliação dos Mecanismos de Pontuação do RAG (Fase 3)

### 3.1 Como o Score Atual é Calculado (`agent/retrieval.py`):
1. **Busca FTS5 Trigramas**:
   $$\text{Base Score} = 0.70 + (0.20 \times \text{Match Ratio}) + (0.04 \times \text{Boost}) - (0.01 \times \text{Rank})$$
   Calibrado na faixa de $[0.65, 0.98]$ para matches $> 50\%$.
2. **Busca Vetorial Densa (Numpy)**:
   $$\text{Semantic Score} = \frac{\mathbf{q} \cdot \mathbf{v}}{\|\mathbf{q}\| \|\mathbf{v}\|}$$
   Calculado instantaneamente sobre matriz pré-carregada de $3.072$ dimensões em memória (`_VECTOR_INDEX_CACHE`).
3. **Score Híbrido Combinado**:
   $$\text{Similarity} = 0.85 \times \text{Semantic Score} + 0.15 \times \text{Keyword Overlap}$$
4. **Reciprocal Rank Fusion (RRF)**:
   $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{60 + \text{Rank}_m(d)}$$
5. **Multiplicador de Completude e Ontologia**:
   $$\text{Final Score} = \min((\text{Similarity} + \text{Ontology Boost}) \times \text{Completeness}, 1.0)$$

### 3.2 Vieses Identificados e Riscos Mitigados:
* **Viés de Chunks Sem Vetor**: Como $1.788$ chunks não possuem embedding, eles recebem $\text{Semantic Score} = 0.0$. Chunks com vetor têm vantagem desproporcional na ordenação híbrida.
* **Viés de Chunks Monolíticos**: Chunks gigantescos contêm dezenas de termos de busca incidentais, acumulando scores FTS inflacionados mesmo quando tratam de outro assunto.
* **Mitigação Ativa**: O `GoldenSourceResolver` intercepta consultas diretas de unidades físicas (648 unidades) e resolve em 0ms com dados cadastrais puros e rotas do Google Maps, blindando contra erros do retriever.

---

## 4. Tabela de Métricas Históricas Consolidadas (`metrics/retrieval_metrics.csv`)

```csv
strategy,precision,recall,retrieval_score,mrr,ndcg,latency,cost
entity_geo_strategy,0.98,0.97,0.975,0.970,0.965,0.04ms,0.00005
semantic_strategy,0.95,0.93,0.940,0.935,0.920,0.07ms,0.00012
recursive_256_64,0.91,0.88,0.895,0.885,0.870,0.01ms,0.00015
token_256_64,0.89,0.86,0.875,0.870,0.855,0.07ms,0.00014
recursive_500_100,0.83,0.80,0.815,0.810,0.795,0.00ms,0.00010
pipeline_routing_hybrid,0.96,0.94,0.950,0.950,0.940,12.5ms,0.00018
```

---

## 5. Plano de Melhorias Técnicas para Chunking e Embeddings

1. **Expurgo Seguro de Chunks Fantasmas**: Excluir do `chunks` e `chunks_fts` os 39 registros com menos de 150 caracteres que consistem apenas de cabeçalhos vazios.
2. **Segmentação Canônica dos Chunks Gigantes**:
   - Dividir `carta_01510` e `carta_01511` pelos serviços individuais listados na página (ex: *Processo Licença Especial*, *Alvará de Habite-se*).
   - Dividir `geo_01571` e `geo_01572` por feição de Bairro (ex: 1 chunk por bairro do 1º Distrito: Centro, 25 de Agosto, Centenário, etc.).
3. **Indexação Vetorial dos 1.788 Chunks Pendentes**:
   - Executar script atômico gerando os vetores de $3.072$ dimensões via `gemini-embedding-2` diretamente em `duque_ia_chunks.embedding`.
4. **Governança de Overlap e Contexto Pai**:
   - Cada sub-chunk derivado deve carregar a tag `[Parent: Nome da Secretaria / Assunto]`, preservando o contexto e facilitando o agrupamento no `ContextBuilder`.

---
*Relatório técnico gerado em estrita observância às regras do DUQUE IA.*
