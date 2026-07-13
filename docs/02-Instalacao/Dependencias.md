# Dependências do Sistema — Duque IA

O Duque IA separa as dependências da aplicação em duas camadas: Node.js (Servidor Web) e Python (Agente de Inteligência Artificial).

## Layer 1: Node.js (Servidor)
O servidor Node.js utiliza apenas os pacotes nativos da plataforma, sem bibliotecas externas no runtime de produção:
- `child_process`: Para spawn do processo do agente Python.
- `http`: Para gerenciar requisições e respostas HTTP.
- `fs` e `path`: Para leitura e resolução de caminhos de arquivos estáticos.

## Layer 2: Python (Agente RAG)
Gerenciadas no arquivo `requirements.txt`:
- `google-genai` / `google-generativeai`: Comunicação oficial com a API do Google Gemini.
- `pyyaml`: Processamento de configurações de chunking (`embed_config.yml`).
- `python-dotenv`: Carregamento dinâmico de variáveis de ambiente.
- `pypdf`: Extração nativa de textos de arquivos PDF.
- `openpyxl`: Importação de Carta de Serviços e dados de saúde estruturados.

---
[Avançar: Banco de Dados](../03-Banco/Banco.md) | [Voltar: Variáveis](Variaveis.md)
