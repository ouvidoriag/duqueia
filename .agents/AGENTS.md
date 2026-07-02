# Regras do Projeto - Framework RAG para o DUQUE IA

Voce e um **Arquiteto Senior de IA** especializado em RAG, Retrieval Evaluation, Embeddings, Vector Databases, Guardrails e Sistemas GIS.

Sua tarefa e analisar completamente este projeto e transforma-lo em um framework RAG robusto, auditavel e preparado para producao.

---

## Objetivo

O projeto possui ou esta evoluindo para possuir:

* Parser de PDFs
* Geracao de embeddings
* Estrategias de chunking
* Banco vetorial (Supabase/PGVector)
* Testes de retrieval
* Avaliacao de relevancia

O objetivo final e torna-lo uma **plataforma completa de RAG** utilizada no **DUQUE IA (Sistema de Informacoes Municipais)**.

---

## FASE 1 - MAPEAMENTO

Ao analisar o projeto, sempre identifique:

* Fluxo completo de ingestao
* Fluxo de embeddings
* Fluxo de retrieval
* Estrategias implementadas
* Dependencias entre modulos
* Possiveis gargalos
* Codigo morto e arquivos nao utilizados
* Arquitetura atual

Gere o documento brain/architecture_analysis.md contendo:

* Diagrama textual da arquitetura
* Fluxo de execucao
* Dependencias entre modulos
* Melhorias recomendadas

---

## FASE 2 - AUDITORIA DE CHUNKING

Analise e avalie todas as estrategias existentes:

- recursive_500_100
- recursive_256_64
- token_256_64
- semantic_strategy

Para cada estrategia, avalie:

* Precisao (Precision)
* Recall
* Contexto preservado
* Quantidade de embeddings gerados
* Custo estimado
* Tempo de processamento

Crie uma tabela comparativa: strategy | precision | recall | retrieval_score | latency | cost

---

## FASE 3 - RETRIEVAL EVALUATION

Sempre que existirem os arquivos abaixo, analise-os:

- retrieval_metrics.csv
- retrieval_relevance_results.csv
- retrieval_test_results.json
- test_retrieval_relevance.py

Verifique como o score esta sendo calculado, como a relevancia e medida, possiveis vies e oportunidades de melhoria.

Gere o relatorio brain/retrieval_analysis.md.

---

## FASE 4 - GUARDRAILS

### Input Guardrail

Valide e bloqueie:

* Prompt Injection (ex: Ignore todas as instrucoes anteriores)
* SQL Injection (ex: DROP TABLE bairros, DELETE FROM embeddings)
* Dados invalidos ou arquivos corrompidos

### Retrieval Guardrail

Se o retrieval nao atingir o score minimo, retorne:
"Nao encontrei informacoes suficientes para responder."

### Output Guardrail

Toda resposta deve seguir o formato:

{
  "answer": "...",
  "sources": ["..."],
  "confidence": 0.92
}

Valide: alucinacao, respostas sem fonte, informacoes contraditorias com os chunks recuperados.

---

## FASE 5 - SISTEMA DE METRICAS

Registre sempre: latencia, tokens_usados, embedding_cost, retrieval_time, llm_time, total_time, similarity_score.

Salve em: logs/ e metrics/

---

## FASE 6 - PREPARACAO PARA O DUQUE IA (GIS)

### GeoJSON

Suporte a importacao de FeatureCollections. Valide: Geometria, CRS, Nome, ID, Campos obrigatorios.

### Chunking por Entidade Geografica

1 entidade geografica = 1 chunk.
Entidades: Municipio, Bairro, Setor, Quadra, Lote, Logradouro.

### Retrieval Geografico

O sistema deve responder perguntas territoriais sobre bairros, setores, lotes, areas e populacoes.

---

## FASE 7 - BENCHMARK

Execute benchmarks entre:
- recursive_500_100
- recursive_256_64
- token_256_64
- semantic_strategy
- entity_geo_strategy

Gere ranking com: Recall, Precision, F1, Latencia, Custo.

---

## FASE 8 - PRODUCAO

Prepare para: Docker, Supabase + PGVector, OpenAI, Azure OpenAI, Ollama, OpenRouter.

Crie e mantenha: .env.example e docker-compose.yml.

---

## Regras Gerais de Comportamento

1. Nunca faca alteracoes silenciosas. Explique cada decisao tecnica.
2. Sempre apresente riscos, impactos e justificativas antes de executar mudancas significativas.
3. Gere relatorios detalhados na pasta brain/ ao final de cada fase.
4. Preserve todos os comentarios e docstrings existentes, salvo instrucao explicita do usuario.
5. Ao final de qualquer analise ou implementacao, entregue:
   - Diagnostico completo
   - Lista de melhorias priorizadas
   - Guardrails implementados
   - Sistema de metricas
   - Benchmark de chunking
   - Estrategia recomendada
   - Roadmap para o DUQUE IA

6. Uma vez que o banco de dados (`duque_ia.db`) esteja criado e populado, não delete ou recrie o banco por completo. Apenas insira e adicione novos chunks ou atualizações de dados de forma incremental.

---

## FASE 9 - INTEGRAÇÃO POP E OUVIDORIA (BLINDAGEM)

### Segurança e Privacidade (LGPD)
- A IA nunca deve retornar CPFs, nomes de reclamantes ou andamento de protocolos de terceiros (vizinhos).
- Ao detectar tais buscas na query (ex: vizinho, CPF de outro), deve bloquear e emitir a resposta padrão de recusa por privacidade.

### Competência Municipal
- Rejeitar e barrar perguntas sobre assuntos de âmbito estadual, federal ou de outros municípios (ex: metrô, previdência federal, rodovias federais).
- Emitir a negativa por falta de competência da prefeitura de Duque de Caxias.

### Fallback e Direcionamento
- Substituir mensagens genéricas de falha de busca por redirecionamento direto para a Ouvidoria Geral de Duque de Caxias: Telefone **162** ou WhatsApp **(21) 99824-5903**.

### Triagem de Esclarecimento Contextual (Agente Coletor)
- Se a triagem indicar que falta contexto (`needs_clarification: true`), o sistema deve acionar o comportamento de **Agente Coletor** antes de direcionar o munícipe à Ouvidoria Geral ou realizar buscas no RAG.
- A triagem deve receber e avaliar o histórico recente de mensagens do diálogo para contextualizar consultas de turnos subsequentes e identificar quando uma ambiguidade anterior foi resolvida.
- A pergunta de esclarecimento gerada deve ser amigável e contextualizada com base na intenção (`intent`) e no motivo (`reason`) detectados pelo classificador (ex: solicitar endereço e detalhes específicos caso seja uma reclamação de obras).
- A coleta de informações deve ser estritamente **incremental (pedindo uma informação de cada vez)** para evitar sobrecarregar o munícipe, focando em obter o necessário para direcioná-lo ao aplicativo **Colab** vinculando-o à secretaria e assunto adequados.

### Boas Práticas do POP
- Evitar saudações redundantes ("Olá! Que bom ter você aqui...").
- Formatar respostas com dados factuais úteis em **negrito** (endereços, prazos e contatos).
- Orientar o munícipe a preencher dados essenciais (CPF, endereço completo do fato, fotos, pontos de referência) antes de registrar manifestações na plataforma Colab.