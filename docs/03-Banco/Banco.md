# Banco de Dados — Duque IA

O Duque IA armazena suas informações em quatro bancos de dados locais **SQLite** em modo WAL localizados em `data/db/`:

## Arquitetura Segregada do Banco
O banco foi planejado em instâncias segregadas para alta concorrência e isolamento:
1. **`data/db/main.db` (Gestão Operacional e Ontologia)**: Estrutura relacional contendo 644 serviços municipais, 443 unidades (CRAS, postos), 20 secretarias, 152 bairros, 400 logradouros, telefones, links e regras de negócio.
2. **`data/db/vector.db` (Banco Vetorial RAG)**: Armazena 2.427 chunks de documentos com embeddings de 3.072 dimensões (`gemini-embedding-2`) e índice lexical FTS5 (`chunks_fts`) para busca híbrida RRF.
3. **`data/db/cache.db` (Cache Semântico)**: Armazena respostas e triagens de perguntas frequentes para latência sub-segundo.
4. **`data/db/telemetry.db` (Métricas e Auditoria)**: Registro detalhado de tempos de resposta e uso de tokens por nó do LangGraph.

---
[Avançar: DER](DER.md) | [Voltar ao Sumário](../README.md)
