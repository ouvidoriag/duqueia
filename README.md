# Duque IA — Assistente Virtual da Prefeitura de Duque de Caxias

> Sistema de IA Conversacional com RAG Híbrido para atendimento ao munícipe via canais digitais da Prefeitura de Duque de Caxias — RJ.

---

## Arquitetura

```
Node.js (server.js)  →  stdin/stdout pipe  →  Python (agent/main.py)
        │                                              │
   HTTP REST API                              RAG + Guardrails
   Static Files                             SQLite (duque_ia.db)
   Session Manager                        Gemini API (embeddings + LLM)
```

---

## Pré-requisitos

| Componente | Versão Mínima |
|---|---|
| Node.js | 18.x |
| Python | 3.10+ |
| pip | 23+ |

---

## Instalação Local

```bash
# 1. Clonar o repositório
git clone https://github.com/<seu-usuario>/duqueia.git
cd duqueia

# 2. Instalar dependências Python
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves do Gemini

# 4. Iniciar o servidor
node server.js
# ou
npm start
```

Acesse em: **http://localhost:3000**

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Chaves do Gemini (separe múltiplas chaves por vírgula para rotação)
GEMINI_API_KEYS=AIzaSy...,AQ.Ab8RN...

# Modelos
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2

# Habilitar camada de triagem
USE_TRIAGE_LAYER=true

# Ambiente
ENVIRONMENT=production
LOG_LEVEL=info
```

> ⚠️ **NUNCA** commite o arquivo `.env` no Git. Ele já está no `.gitignore`.

---

## Deploy no Render

### 1. Criar Web Service

No painel do Render, crie um **Web Service** apontando para este repositório.

### 2. Configurações do Render

| Campo | Valor |
|---|---|
| **Runtime** | Node |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `node server.js` |
| **Node Version** | 18 |

### 3. Variáveis de Ambiente no Render

Adicione todas as variáveis do `.env.example` no painel **Environment** do serviço.

> 🔴 Nunca use o arquivo `.env` em produção — use apenas as variáveis do dashboard do Render.

### 4. Health Check

O servidor expõe o endpoint `/health` que o Render utiliza para monitoramento de disponibilidade:

```
GET /health → { "status": "ok", "sessions": <N> }
```

---

## Estrutura do Projeto

```
/
├── server.js              ← Gateway HTTP + Gerenciador de sessões Python
├── package.json           ← Dependências Node.js e scripts
├── requirements.txt       ← Dependências Python
├── .env.example           ← Template de configuração de ambiente
├── .gitignore
│
├── agent/                 ← Núcleo cognitivo do RAG
│   ├── main.py            ← Entry point Python (stdin/stdout, UTF-8)
│   ├── agent.py           ← Orquestrador principal (DuqueIAAgent)
│   ├── triage.py          ← Triagem de intenção em 3 camadas
│   ├── retrieval.py       ← Busca híbrida vetorial + estruturada
│   ├── guardrails.py      ← Segurança: injeção, LGPD, competência
│   ├── handlers.py        ← Handlers por intenção (RAG, Coletor, Segurança)
│   ├── router.py          ← Roteamento semântico
│   ├── fallback.py        ← Respostas de fallback e redirecionamento
│   ├── scoring.py         ← Funções de similaridade e palavras-chave
│   ├── config.py          ← Configurações e constantes
│   └── duque_ia.db        ← Banco SQLite (embeddings 3072d + dados estruturados)
│
├── ingestion/             ← Pipeline de ingestão de dados
│   ├── parser/            ← Parsers (PDF, CSV, Excel, Web, OCR)
│   └── embed/             ← Geração de embeddings e indexação
│
├── utils/
│   └── gemini_client.py   ← Cliente Gemini com rotação de chaves
│
├── public/                ← Frontend estático
│   └── chat.html          ← Interface do munícipe
│
├── bancoia/               ← Fontes de conhecimento brutas (Markdowns e PDFs)
├── eusoulindo/            ← Documentação técnica do banco (DDL, schemas, seeds)
├── brain/                 ← Relatórios de arquitetura e métricas
├── logs/                  ← Logs de execução do agente
└── metrics/               ← Métricas de retrieval (CSV)
```

---

## Pipeline de Ingestão

Para adicionar novos documentos à base de conhecimento:

```bash
# 1. Copie o arquivo para a pasta correta:
#    - .md, .txt → bancoia/CRIADO/<secretaria>/
#    - .pdf      → raw_pdf_files/
#    - .xlsx     → raw_excel_files/
#    - .csv      → raw_csv_files/

# 2. Execute o pipeline de embedding
python ingestion/embed/main.py

# Os embeddings são adicionados INCREMENTALMENTE ao banco (nunca apaga dados existentes)
```

---

## Guardrails de Segurança

| Tipo | Descrição |
|---|---|
| **Input** | Bloqueia SQL Injection e Prompt Injection |
| **LGPD/Privacidade** | Bloqueia consultas sobre dados de terceiros (CPF, protocolos alheios) |
| **Competência** | Bloqueia temas fora da alçada municipal (INSS, Detran, Metrô, BR-xxx) |
| **Jurídico** | Bloqueia solicitações de elaboração de peças processuais |
| **Retrieval** | Só responde se a similaridade mínima for atingida |
| **Output** | Valida resposta gerada contra as fontes oficiais (anti-alucinação) |

---

## Contatos de Suporte

**Ouvidoria Geral de Duque de Caxias**
- Telefone: **(21) 2652-3835** / **162**
- E-mail: ouvidoria@duquedecaxias.rj.gov.br
- WhatsApp: **(21) 99824-5903**
- Presencial: Alameda Esmeralda, 206 — Jardim Primavera
