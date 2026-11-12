# Relatório de Auditoria, Falhas e Otimização do Banco de Dados
**DUQUE IA — Sistema de Informações Municipais de Duque de Caxias**  
**Data da Auditoria e Otimização:** 12 de Novembro de 2026  
**Status da Infraestrutura:** 100% OPERACIONAL E OTIMIZADA  

---

## 1. Sumário Executivo

Foi realizada uma auditoria exaustiva em todo o ecossistema de bancos de dados do DUQUE IA, englobando:
1. **Bancos de dados SQLite**: Integridade física (`PRAGMA integrity_check`), integridade referencial (`PRAGMA foreign_key_check`), contagem e consistência de tabelas, views e índices.
2. **Sincronização 100% da Camada Híbrida (`vector.db`)**: Identificação e resolução de um ponto cego crítico onde 852 chunks vetoriais estavam ausentes do índice lexical FTS5 (BM25). Todos os 2.753 chunks agora possuem paridade exata em `chunks`, `chunks_fts` e `duque_ia_chunks`.
3. **Redução e Controle de Tamanho Físico (< 50 MB)**: O `vector.db` foi otimizado para **45.16 MB** através de FTS5 com conteúdo externo (`content='chunks'`), dispensando Git LFS e garantindo versionamento ágil no Git padrão.
4. **Enriquecimento Estruturado (`main.db`)**: Adição de coluna `titular` na tabela `secretarias` e atualização da view `vw_ia_servicos` com 100% das 22 secretarias mapeadas com seus titulares oficiais (Gestão 2025–2028).
5. **Índices de Cobertura e Desempenho (`cache.db` e `telemetry.db`)**: Criação de índices cobrindo triagem semântica em 0.1ms e consultas executivas do Dashboard de Telemetria.

---

## 2. Diagnóstico Consolidado dos Bancos de Dados

O DUQUE IA opera com 4 instâncias físicas especializadas em `data/db/`, todas em modo **WAL (Write-Ahead Logging)**:

### 2.1. `data/db/main.db` (Dados Estruturados e Ontologia Municipal)
- **Tamanho:** 1,93 MB
- **Integridade Física:** `ok`
- **Foreign Keys Check:** `0 erros`
- **Journal Mode:** `WAL`
- **Tabelas e Registros:**
  | Tabela / View | Tipo | Registros | Descrição |
  | :--- | :---: | :---: | :--- |
  | `services` | TABLE | **644** | Catálogo oficial de serviços municipais (Carta de Serviços + Colab) |
  | `secretaria_unidades` | TABLE | **443** | Equipamentos públicos (CRAS, UBS, UPAs, escolas, secretarias) |
  | `secretarias` | TABLE | **22** | Secretarias municipais catalogadas com titulares oficiais e dados |
  | `service_documents` | TABLE | **1.610** | Documentos e requisitos necessários para cada serviço |
  | `service_steps` | TABLE | **1.294** | Passo a passo de atendimento para os cidadãos |
  | `service_emails` | TABLE | **334** | E-mails de contato setorial |
  | `service_phones` | TABLE | **261** | Telefones diretos dos órgãos municipais |
  | `service_links` | TABLE | **204** | Portais e links de acesso direto (ex: Colab, Web) |
  | `bairros_distritos` | TABLE | **152** | Bairros mapeados nos 4 distritos municipais |
  | `logradouros_enderecos` | TABLE | **400** | Logradouros para resolução geográfica e territorial |
  | `escolas_municipais` | TABLE | **205** | Escolas municipais e creches de Duque de Caxias |
  | `regras_negocio` | TABLE | **85** | Regras canônicas de governança, prioridades e POP |
  | `categories` | TABLE | **41** | Categorias temáticas de atendimento |
  | `leis_municipais` | TABLE | **27** | Legislação municipal indexada |
  | `linhas_tarifa_zero` | TABLE | **21** | Linhas do programa municipal Tarifa Zero |
  | `vw_ia_servicos` | VIEW | **644** | Visão desnormalizada com titulares e dados de alta performance |

### 2.2. `data/db/vector.db` (Busca Semântica e Híbrida)
- **Tamanho:** 45,16 MB (Seguro abaixo do limite de 50 MB do GitHub)
- **Integridade Física:** `ok`
- **Journal Mode:** `WAL`
- **Chunks Indexados:**
  - `duque_ia_chunks`: **2.753** chunks vetoriais com embeddings `gemini-embedding-2` (float32 BLOB, 3.072 dimensões).
  - `chunks`: **2.753** fragmentos unificados sincronizados.
  - `chunks_fts`: **2.753** documentos no índice FTS5 externo com remoção de acentos (`unicode61 remove_diacritics 2`).
- **Gatilhos de Automação:** `chunks_ai`, `chunks_ad`, `chunks_au` para sincronização transacional permanente.

### 2.3. `data/db/cache.db` (Cache Semântico de Triagem)
- **Tamanho:** 0,13 MB
- **Integridade Física:** `ok`
- **Journal Mode:** `WAL`
- **Registros:** **416** decisões de triagem cacheadas (respostas em ~0.1ms).
- **Índices Criados:**
  - `idx_triage_cache_lookup`: Cobrindo `(query_hash, prompt_version, model_version)`.
  - `idx_triage_cache_created`: Otimização de monitoramento e expiração em `(created_at)`.

### 2.4. `data/db/telemetry.db` (Auditoria e Observabilidade)
- **Tamanho:** 1,86 MB
- **Integridade Física:** `ok`
- **Journal Mode:** `WAL`
- **Registros:**
  - `chat_messages`: **1.788** mensagens registradas com isolamento por sessão e índice de turnos.
  - `agent_session_storage`: **193** estados de conversação multiturno persistidos.
  - `chat_feedback`: Registros de CSAT dos munícipes.
- **Índices Criados:**
  - `idx_chat_feedback_created`: Otimização de leitura do Dashboard Executivo (`created_at`).
  - `idx_chat_messages_created`: Otimização de filtros por período temporal (`created_at`).
