# Configuração de Ambiente — Duque IA

Para que o sistema RAG funcione de maneira adequada (especialmente a geração de embeddings e as interações com os modelos do Gemini), é obrigatório configurar as chaves de API correspondentes.

## Arquivo `.env`
Crie um arquivo `.env` na raiz do projeto contendo as seguintes definições básicas:

```env
# Configurações do Agente
USE_TRIAGE_LAYER=true
SQLITE_DB_PATH=agent/duque_ia.db

# Chaves de API das LLMs
GEMINI_API_KEY=sua_chave_do_gemini_aqui
```

Para mais detalhes sobre variáveis avançadas suportadas no projeto, consulte o arquivo [Variáveis](Variaveis.md).

---
[Avançar: Variáveis](Variaveis.md) | [Voltar: Instalação](Instalacao.md)
