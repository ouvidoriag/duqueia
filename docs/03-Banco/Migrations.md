# Migrations e Seeds — Duque IA

As definições e sementes do banco de dados são controladas via scripts Python automatizados.

## Migrations
O banco de dados é inicializado por meio do script `scripts/setup/setup_supabase.py` (ou localmente). Ele cria a estrutura de tabelas relacionais caso ela ainda não exista.

## Seeds (Alimentação Inicial)
A carga de dados (seeds) é realizada por meio dos parsers e indexadores:
1. **Dados Institucionais**: Inseridos a partir dos arquivos estruturados Excel e planilhas na pasta `data/raw/` e `data/knowledge/` durante a importação.
2. **Embeddings Vetoriais**: O pipeline de embedding (`ingestion/embed/main.py`) insere e calcula vetores dinamicamente com base nas fontes brutas.

---
[Avançar: API](../04-API/Endpoints.md) | [Voltar: Estrutura](Estrutura.md)
