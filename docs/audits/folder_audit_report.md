# Relatório de Auditoria de Pastas — DUQUE IA

Este documento apresenta a análise de todas as pastas e subpastas existentes na raiz do projeto **PRODUCAO** do DUQUE IA, classificando cada uma por nível de relevância, uso e necessidade de preservação em produção.

---

## Tabela Comparativa de Pastas

| Caminho da Pasta | Classificação | Descrição / Justificativa | Ação Recomendada |
| :--- | :--- | :--- | :--- |
| `.agents/` | **Necessária** | Contém regras de comportamento do agente e configurações de skills. | **Preservar** |
| `.gemini/` | **Temporária / Interna** | Metadados internos e caches do IDE. | **Ignorar no controle de versão** |
| `.git/` | **Necessária** | Diretório padrão de controle de versão Git. | **Preservar** |
| `__pycache__/` (Várias) | **Temporária / Pode ser removida** | Arquivos binários compilados de bytecodes Python. | **Remover ou ignorar** |
| `agent/` | **Necessária** | Core do sistema: modelos, roteador, handlers de contexto, grafos cognitivos e guardrails. | **Preservar** |
| `archive/` | **Obsoleta / Pode ser removida** | Repositório de arquivos legados de questionários e módulos antigos movidos da raiz. | **Remover ou manter compactado** |
| `brain/` | **Necessária** | Armazena análises arquiteturais, auditorias de dados e relatórios técnicos. | **Preservar** |
| `data/` | **Necessária** | Armazena a base de conhecimento (planilhas de serviços e PDFs raw/processados) e os arquivos SQLite segregados. | **Preservar** |
| `data/db/` | **Necessária** | Diretório oficial dos novos bancos de dados independentes (`main.db`, `vector.db`, `cache.db`, `telemetry.db`). | **Preservar** |
| `data/logs/` | **Necessária** | Pasta ativa de escrita dos arquivos `execution.log` sob a nova estrutura. | **Preservar** |
| `data/metrics/` | **Necessária** | Pasta ativa de escrita de dados de performance da nova estrutura. | **Preservar** |
| `docs/` | **Necessária** | Contém arquivos auxiliares de documentação e manuais operacionais. | **Preservar** |
| `ingestion/` | **Necessária** | Contém a suíte do pipeline de dados (parsers de PDFs/Excel/Web e indexadores de embeddings). | **Preservar** |
| `logs/` (Raiz) | **Obsoleta / Pode ser removida** | Logs legados de quando o banco de dados e os handlers rodavam a partir da pasta raiz. | **Pode ser removida** |
| `metrics/` (Raiz) | **Necessária / Temporária** | Contém os scripts python de telemetria (`collector.py`, `dashboard.py`) e relatórios JSON/CSV de testes executados na raiz. | **Preservar** |
| `public/` | **Necessária** | Frontend web estático da interface de chat do DUQUE IA. | **Preservar** |
| `scripts/` | **Necessária** | Ferramentas de suporte administrative (`db_stats.py`), indexação manual e orquestradores de testes. | **Preservar** |
| `scripts/tests/` | **Necessária** | Suíte completa de 17 testes funcionais e integrados de regressão. | **Preservar** |
| `utils/` | **Necessária** | Módulos utilitários unificados: conexões do SQLite (`db_client.py`), StorageManager (`storage.py`) e APIs do Gemini. | **Preservar** |

---

## 🛑 Limpezas Efetuadas Durante as Auditorias

Durante as fases de auditoria e saneamento do projeto, as seguintes remoções físicas foram executadas para evitar códigos duplicados ou mortos na raiz do workspace:
1.  **Arquivos Legados na Raiz:** Arquivos como `test_openai.py`, `test_xai.py` e `find_keys.py` foram movidos para a pasta `archive/`.
2.  **Diretórios Mortos na Raiz:** As pastas `portalcidadao` e `questionario` foram arquivadas por estarem fora do escopo funcional ativo do RAG.
3.  **Banco de Dados Legado:** O monólito `duque_ia.db` foi renomeado de forma segura para `duque_ia.db.bak` para evitar qualquer concorrência ou colisão física.
