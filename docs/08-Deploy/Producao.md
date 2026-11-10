# Guia de Deploy em Produção — Duque IA

Antes de mover a aplicação para produção, garanta as seguintes validações:

## 1. Banco de Dados e Cache
- Certifique-se de manter os quatro bancos SQLite (`data/db/main.db`, `data/db/vector.db`, `data/db/cache.db`, `data/db/telemetry.db`) no servidor.
- O sistema habilita automaticamente o modo WAL (`PRAGMA journal_mode = WAL;`) e a camada de **Cache L1 RAM** (<0.01ms) para triagens frequentes.

## 2. Variáveis de Ambiente (.env)
Configurar as chaves Gemini de produção e os parâmetros do agente:
```env
GEMINI_API_KEYS=sua_chave_gemini_aqui
USE_TRIAGE_LAYER=true
DATABASE_MAIN=data/db/main.db
DATABASE_VECTOR=data/db/vector.db
```

## 3. Instalação e Execução em Produção
Execute o servidor Gateway HTTP Node.js:
```bash
# Instalar dependências e validar ambiente
npm run build

# Iniciar o servidor Node.js
npm run dev
```

---
[Avançar: Docker](Docker.md) | [Voltar ao Sumário](../README.md)

