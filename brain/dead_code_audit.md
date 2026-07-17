# Relatório de Auditoria — Código Morto (DUQUE IA)

Este documento apresenta a análise de código morto, redundâncias, arquivos abandonados, imports não utilizados e variáveis/tabelas sem uso, em conformidade com o item **13. Código Morto** da auditoria técnica.

---

## 1. Mapeamento de Arquivos e Scripts Abandonados

Durante a varredura física do workspace, identificamos os seguintes arquivos que não fazem parte do fluxo ativo de execução ou dos testes de regressão:

| Arquivo / Caminho | Função Original | Status | Ação Recomendada |
| :--- | :--- | :--- | :--- |
| `ingestion/parser/parse_csv.py` | Leitor e parser de tabelas CSV | **Morto** | Remover ou mover para pasta de arquivo histórico. |
| `ingestion/parser/parse_excel.py` | Parser genérico de arquivos XLSX | **Morto** | Remover ou mover para pasta de arquivo histórico. |
| `scripts/search_main.py` | Utilitário CLI local para buscas em strings | **Morto** | *Já removido em etapas anteriores.* |
| `utils/storage.py` | Abstração antiga de escrita em banco SQLite | **Morto** | *Já removido e substituído por `storage/manager.py`.* |
| `agent/config.py` | Configurações antigas do agente | **Morto** | *Já removido e substituído por `config/settings.py`.* |

---

## 2. Auditoria de Rotas (server.js)

Analisamos todas as rotas registradas no servidor gateway HTTP Node.js ([server.js](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/server.js)):
* **Rotas Ativas:**
  * `GET /health`: Utilizada pelo Render/CI para monitoramento de saúde do contêiner.
  * `POST /api/chat`: Rota principal de processamento de mensagens.
  * `GET /api/metrics`: Consome e expõe dados unificados de telemetria dos requests (`requests.jsonl` e `retrieval_performance.csv`).
  * `GET /*` (estáticos): Serve páginas da interface sob a pasta `/public`.
* **Rotas Mortas:** **Nenhuma rota morta detectada**. Todo o escopo de rotas declaradas no Express/HTTP nativo está ativamente associado a funcionalidades do sistema.

---

## 3. Variáveis e Tabelas Mortas (Banco de Dados)

Conforme detalhado no *Relatório de Governança de Dados*, o DDL atual ([schema_main.sql](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/database/schema_main.sql)) contém tabelas com diferentes níveis de utilização. Propomos a seguinte categorização conservadora para evitar retrabalho em evoluções futuras:

| Tabela | Status / Utilização | Ação Recomendada | Justificativa |
| :--- | :--- | :--- | :--- |
| **`users`** | Não utilizada atualmente | **🔴 Manter** | Crítica para futura implementação de autenticação, painel administrativo e controle de permissões de operadores. |
| **`service_history`** | Sem fluxo de log ativo | **🟡 Avaliar** | Pode ser útil em auditorias futuras de modificações nos serviços públicos. |
| **`service_priorities`** | Sem queries ativas | **🟡 Avaliar** | Mapeamento de prioridades de atendimento legal que podem ser reinseridas em refinamentos de RAG. |
| **`service_categories`** | Sem queries ativas | **🟡 Avaliar** | Relacionamento relacional pivot. |
| **`rag_queries`** | Substituída | **✅ Remover** | Completamente redundante, uma vez que a telemetria e o histórico agora são centralizados em `requests.jsonl` e `telemetry.db`. |

---

## 4. Recomendações e Saneamento Seguro

* **Validação dos Scripts `parse_csv.py` e `parse_excel.py`:**
  Antes de realizar qualquer deleção física, deve-se auditar via regex/grep se não existem referências operacionais, scripts administrativos secundários, subprocessos de carga ou menções nos manuais (README/docs) que utilizam estes parsers de forma indireta para manutenção offline das planilhas.
* **Remoção Segura de `rag_queries`:**
  A remoção no schema DDL deve ser feita apenas após a confirmação via testes de carga de que nenhuma migração ou ferramenta de reflexão do ORM está executando mapeamentos dinâmicos nesta tabela.
* **Higiene Contínua de Imports e Código Duplicado:**
  Implementar na esteira de CI/CD ferramentas automáticas como `ruff` e `vulture` para identificar imports mortos e `jscpd` para rastrear duplicação lógica antes que novos códigos cheguem à produção.

