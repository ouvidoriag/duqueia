# Carga de Sementes (Seeds) e Ingestão de Dados — Duque IA

Diferente de frameworks tradicionais (como Laravel ou Rails), o Duque IA não utiliza arquivos SQL estáticos para seeds. A alimentação e atualização do banco de dados são baseadas em pipelines de leitura e processamento dinâmico.

## 1. Origem das Sementes
As sementes que populam o banco de dados provêm das seguintes pastas:
- **`data/knowledge/`**: Contém arquivos Markdown estruturados que formam a base de conhecimento (Ex: `ouvidoria_geral_info.md`, `colab.md`).
- **`data/raw/`**: Contém planilhas Excel, tabelas CSV e arquivos PDF de referência (Ex: lista de bairros, endereços de postos de saúde).

## 2. Processo de Alimentação (Ingestão)
- **Etapa 1 (Parsing)**: O script `ingestion/parser/parse_pdfs.py` lê os documentos brutos, normaliza o conteúdo e gera arquivos JSON prontos para indexação na pasta `data/processed/`.
- **Etapa 2 (Vetorização)**: O pipeline `ingestion/embed/main.py` consome os JSONs, gera os vetores de embeddings através da API do Gemini e grava os dados de forma incremental na tabela `duque_ia_chunks`.

## 3. Comandos Importantes
Para atualizar ou recarregar as sementes do banco de dados local:
```bash
# Executa todos os parsers
python ingestion/parser/parse_pdfs.py

# Roda o gerador de embeddings e atualiza a base de dados
python ingestion/embed/main.py --config ingestion/embed/embed_config.yml
```

---
[Voltar: Migrations](Migrations.md) | [Voltar ao Sumário](../README.md)
