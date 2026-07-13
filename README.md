# Duque IA — Assistente Virtual da Prefeitura de Duque de Caxias

> Sistema de Inteligência Artificial Conversacional baseado em **RAG Híbrido** e **Triagem Semântica** para atendimento ao munícipe dos canais oficiais da Prefeitura de Duque de Caxias — RJ.

---

## 🏛️ Sobre o Projeto
O **Duque IA** é a plataforma de atendimento virtual que ajuda os cidadãos a localizarem serviços urbanos, secretarias, endereços públicos, orientações sobre o IPTU, alvarás, cronogramas de saúde e assistência social, além de triagem incremental para denúncias e sugestões direcionadas para a Ouvidoria Geral.

---

## 🛠️ Tecnologias e Dependências
- **Frontend**: HTML5, CSS3 Vanilla, JavaScript (com suporte a micro-animações, design premium e responsividade mobile).
- **Backend**: Node.js (Runtime do Servidor, proxy HTTP, isolamento de subprocessos por sessionId).
- **RAG & IA**: Python 3.10+ (agente principal, indexador de PDF/Excel, gerador de embeddings e triagem de intenções).
- **Banco de Dados**: SQLite local (`duque_ia.db`) atuando de forma relacional e vetorial.
- **LLM**: Google Gemini API (modelos `gemini-3.1-flash-lite`, `gemini-2.5-flash` e embeddings `gemini-embedding-2`).

---

## 📐 Arquitetura Simplificada
```
  Navegador (HTML/CSS/JS)
            │  (HTTP / POST /api/chat)
            ▼
   Servidor Node.js (server.js)
            │  (Process Spawn / IPC)
            ▼
    Agente Python (agent/main.py)
      ├── Triagem Semântica (triage.py)
      ├── Guardrails (LGPD/Competência)
      └── RAG Local (SQLite: duque_ia_chunks)
```

---

## 📂 Estrutura de Pastas e Projetos
- `/agent` — Arquivos do agente conversacional Python, guardrails, triage e o banco SQLite.
- `/docs` — Documentação técnica completa organizada em módulos (SSOT).
- `/data` — Fontes de dados de conhecimento brutas (`raw`), processadas (`processed`) e indexadas.
- `/ingestion` — Scripts e parsers de leitura para PDFs, planilhas e páginas da web.
- `/public` — Assets estáticos do frontend (chat, arquitetura, prompts, organograma).
- `/scripts` — Utilitários de setup, execução e baterias de testes.

---

## 🚀 Como Instalar e Configurar
Acesse a [Documentação de Instalação](docs/02-Instalacao/Instalacao.md) para ver o passo a passo detalhado. 

### Instalação Rápida:
```bash
# Instalar dependências python
npm run build

# Configurar variáveis de ambiente
cp .env.example .env
# Adicione sua GEMINI_API_KEY no arquivo .env

# Popular e vetorizar o banco
python ingestion/parser/parse_pdfs.py
python ingestion/embed/main.py --config ingestion/embed/embed_config.yml

# Iniciar em ambiente de desenvolvimento
npm run dev
```

---

## 📝 Variáveis de Ambiente
Crie um arquivo `.env` contendo:
```env
GEMINI_API_KEY=sua_chave_aqui
USE_TRIAGE_LAYER=true
SQLITE_DB_PATH=agent/duque_ia.db
```
Mais informações sobre variáveis avançadas estão na [Documentação de Variáveis](docs/02-Instalacao/Variaveis.md).

---

## 📚 Central de Documentação (docs/)
Acesse as subpastas da pasta [/docs](docs/README.md) para documentações completas:
- 📂 **[01-Projeto - Visão Geral e Arquitetura](docs/01-Projeto/Visao-Geral.md)**
- 📂 **[02-Instalação - Guias e Dependências](docs/02-Instalacao/Instalacao.md)**
- 📂 **[03-Banco - DER e Dicionário de Dados](docs/03-Banco/Banco.md)**
- 📂 **[04-API - Endpoints e Exemplos HTTP](docs/04-API/Endpoints.md)**
- 📂 **[05-Frontend - Telas e Estilização](docs/05-Frontend/Estrutura.md)**
- 📂 **[06-Backend - Servidor Node.js](docs/06-Backend/Controllers.md)**
- 📂 **[07-IA - Engenharia de Prompts e Agentes](docs/07-IA/Prompts.md)**
- 📂 **[08-Deploy - Docker, Render e VPS](docs/08-Deploy/Produção.md)**
- 📂 **[09-Testes - Execução e Casos de Teste](docs/09-Testes/Testes.md)**
- 📂 **[10-Manutenção - Backup e Checklist](docs/10-Manutencao/Checklist.md)**

---

## 🧪 Como Rodar Testes
O projeto conta com 47 testes integrados e unitários:
```bash
python scripts/run_all_tests.py
```
Veja os casos de testes documentados em [Casos de Teste](docs/09-Testes/Casos.md).

---

## 🛠️ Solução de Problemas (Troubleshooting)
- **Erro `Invalid API Key`**: Verifique se o arquivo `.env` está na raiz do projeto e se a chave `GEMINI_API_KEY` foi configurada sem aspas ou espaços extras.
- **Erro de SQLite Lock**: Certifique-se de que nenhum outro processo está mantendo o arquivo `agent/duque_ia.db` aberto para escrita.
- **Saudações Duplicadas**: O sistema implementa blindagem via histórico. Certifique-se de passar o `sessionId` idêntico nas chamadas subsequentes para manter a sessão ativa.

---

## 📋 Checklist Inicial para Deploy
- [ ] Chave de API ativa.
- [ ] Banco local indexado e vetorizado.
- [ ] Testes automatizados passando (`make test_suite`).
- [ ] Firewall permitindo tráfego nas portas de proxy.
