# eusoulindo — Duque IA · Infraestrutura de Dados

> **Ambiente completo e autossuficiente** para documentação, manutenção e reconstrução do banco de dados do sistema **Duque IA** — Prefeitura de Duque de Caxias / RJ.

---

## O que é este diretório?

Esta pasta centraliza tudo o que é necessário para entender, manter e recriar integralmente a base de dados do Duque IA:

- 📄 Documentação HTML interativa do schema
- 🗄️ DDL completo (CREATE TABLE / CREATE VIEW)  
- 🔄 Histórico de migrações aplicadas  
- 🌱 Seeds com dados iniciais  
- 📊 Datasets originais (planilhas e CSVs da Prefeitura)  
- 📁 PDFs das Secretarias Municipais  
- 🔧 Scripts de reconstrução e sincronização  

---

## Estado Atual do Banco (gerado em 2026-06-30 12:07)

| Item | Quantidade |
|------|-----------|
| Tabelas | 22 |
| Views | 1 |
| Chunks de conhecimento | 685 |
| Serviços municipais indexados | 363 |

---

## Estrutura

```
eusoulindo/
├── database/
│   ├── schema/
│   │   ├── schema_full.sql              ← DDL completo do banco (auto-sincronizado)
│   │   ├── schema.json                  ← Inventário JSON do banco (auto-sincronizado)
│   │   └── production_schema_supabase.sql  ← Schema para Supabase/PGVector (produção)
│   ├── migrations/
│   │   ├── 0001_initial_schema.sql      ← Criação inicial do banco
│   │   └── 0002_add_message_id.sql      ← FK message_id em rag_queries
│   ├── seeds/
│   │   └── seed_01_secretarias_categories.sql  ← Dados de secretarias e categorias
│   ├── scripts/
│   │   └── rebuild_db.py               ← Recria o banco do zero a partir do schema
│   └── backups/                         ← Backups manuais ou automáticos do .db
│
├── documentation/
│   ├── html/
│   │   └── duque_ia_database_schema.html  ← Documentação interativa do banco
│   ├── pdf/                             ← PDFs oficiais das Secretarias (OFICIOS/)
│   ├── diagrams/                        ← Diagramas ERD e arquitetura
│   └── manuals/                         ← Manuais técnicos
│
├── datasets/
│   ├── csv/
│   │   ├── assuntoXsecretaria.csv       ← Mapeamento assunto × secretaria
│   │   ├── bairros_caxias.csv           ← Bairros de Duque de Caxias
│   │   ├── retrieval_metrics.csv        ← Métricas de retrieval do RAG
│   │   └── retrieval_performance.csv    ← Performance histórica do retrieval
│   ├── excel/
│   │   ├── CARTA_DE_SERVICO_AJUSTE_23.05.26.xlsx  ← Carta de Serviços oficial
│   │   └── postos_saude_caxias.xlsx     ← Postos de saúde do município
│   └── text/
│       └── *.md                         ← Markdowns por secretaria municipal
│
├── assets/
│   └── .env.example                     ← Variáveis de ambiente necessárias
│
├── sync.py                              ← Sincroniza automaticamente com o projeto
└── README.md                           ← Este arquivo
```

---

## Como Recriar o Banco do Zero

```bash
# 1. Entrar na pasta eusoulindo
cd eusoulindo

# 2. Executar o script de reconstrução
python database/scripts/rebuild_db.py

# 3. (Opcional) Especificar caminho de saída
python database/scripts/rebuild_db.py --output ../agent/duque_ia.db
```

---

## Como Sincronizar com o Projeto

```bash
# Sincronização real
python eusoulindo/sync.py

# Simulação (sem copiar arquivos)
python eusoulindo/sync.py --dry-run
```

O script `sync.py`:
- Detecta arquivos modificados por timestamp e os atualiza
- Regenera automaticamente `schema_full.sql` e `schema.json` a partir do banco atual
- Copia novos PDFs adicionados à pasta `bancoia/OFICIOS/`

---

## Pipeline de Ingestão de Dados

```
FONTES BRUTAS                  SCRIPT DE INGESTÃO             BANCO (duque_ia.db)
─────────────────────────────────────────────────────────────────────────────────
CARTA_DE_SERVICO.xlsx    →  parse_carta_servico.py      →  services, service_*
bancoia/OFICIOS/*.pdf    →  parse_pdfs.py + embed/main  →  core_documents + duque_ia_chunks
bancoia/CRIADO/*.md      →  embed/main.py               →  duque_ia_chunks
assuntoXsecretaria.csv   →  populate_structured_services →  secretarias, categories
Interações em runtime    →  agent/agent.py              →  chat_sessions, chat_messages
Perguntas/RAG runtime    →  agent/handlers.py           →  rag_queries, chat_feedback
```

---

## Tecnologias

| Componente | Tecnologia |
|---|---|
| Banco local | SQLite 3 |
| Banco produção | Supabase + PGVector |
| Embeddings | Google Gemini text-embedding-004 |
| LLM | Gemini / OpenRouter / Groq |
| API | Node.js + Express |
| Pipeline RAG | Python 3.14 |

---

*Gerado automaticamente por `build_eusoulindo.py` em 30/06/2026 às 12:07.*
*Para atualizar, execute: `python eusoulindo/sync.py`*
