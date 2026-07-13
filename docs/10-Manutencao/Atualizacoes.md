# Guia de Atualizações e Ingestão de Dados — Duque IA

Para atualizar a base de conhecimento ou adicionar novas informações factuais ao assistente virtual:

1. **Adicionar novos arquivos**: Adicione documentos Markdown (.md) em `data/knowledge/` ou PDFs em `data/raw/raw_pdf_files/`.
2. **Rodar o Parser**:
   ```bash
   python ingestion/parser/parse_pdfs.py
   ```
3. **Rodar a Vetorização**:
   ```bash
   python ingestion/embed/main.py --config ingestion/embed/embed_config.yml
   ```
O pipeline detecta novos trechos de conhecimento, calcula os vetores de embeddings utilizando a API do Gemini e adiciona-os ao banco de forma incremental.

---
[Voltar ao Início](../README.md)
