# Relatório de Auditoria — Governança dos Dados

> **Status:** Concluído | **Objetivo:** Analisar a utilidade prática das tabelas do banco de dados, detectar tabelas/campos mortos sem consultas no runtime e mapear a rastreabilidade das fontes de dados do DUQUE IA.

---

## 1. Mapeamento de Utilização Real das Tabelas

Analisamos todas as queries SQL executadas pelo orquestrador e handlers cognitivos sob a pasta `/agent` e no servidor web do Node.js (`server.js`):

### A. Tabelas Ativas em Produção (Frequentes no Runtime)
*   **`duque_ia_chunks`**: Contém os embeddings semânticos. Acessada a cada requisição RAG para buscar chunks relevantes.
*   **`triage_cache`**: Utilizada para guardar e consultar decisões semânticas passadas e diminuir custos de chamadas de LLM.
*   **`secretarias`**: Consulta informações estruturadas de endereços, e-mails e contatos oficiais.
*   **`secretaria_unidades`**: Utilizada de forma ativa para recuperar endereços físicos e contatos de unidades como CRAS.
*   **`services` (e tabelas filhas `service_phones`, `service_emails`, `service_links`, `service_steps`, `service_documents`)**: Utilizadas para busca e estruturação do passo a passo e documentações de serviços via SQL estruturado.
*   **`embedding_metadata`**: Usada na inicialização do agente para carregar metadados do provedor e modelo de embedding utilizado.
*   **`vw_ia_servicos` (SQL View)**: View utilizada para consolidar dados combinados de secretarias e serviços na busca.

---

### B. Tabelas Mortas (Zero Consultas ou Inserções no Runtime)
Estas tabelas constam no schema DDL de criação inicial, porém **nunca** são lidas ou escritas pelo código ativo do agente Python ou do backend Node.js:

1.  **`users`**: Projetada para controle administrativo, mas sem fluxo ativo no backend.
2.  **`service_priorities`**: Sem referências ou uso prático nas lógicas de processamento de respostas.
3.  **`service_categories`**: Tabela pivot muitos-para-muitos. Os serviços hoje são filtrados diretamente pelo ID da secretaria e categoria textual, deixando essa pivot morta.
4.  **`service_history`**: Sem qualquer fluxo de auditoria ativo registrando alterações de dados.
5.  **`rag_queries`**: Tabela projetada de auditoria de telemetria sem inserções ativas no runtime de produção.
6.  **`chat_sessions`**, **`chat_messages`** e **`chat_feedback`**: Projetadas para manter sessões e avaliações dos munícipes, mas o histórico hoje é gerido de forma stateless ou na memória da sessão, sem persistência relacional nestas tabelas.

---

## 2. Rastreabilidade das Fontes (Lineage)

A rastreabilidade segue um caminho de 4 elos lineares:

1.  **Documento de Origem (Raw):** Localizado sob `data/raw/` (ex: PDF ou Carta de Serviços Excel).
2.  **Chunk Processado (Intermediate JSON):** Arquivo sob `data/processed/` identificando o nome exato da fonte (ex: `"source": "assistencia_social_direitos_humanos.md"`).
3.  **Registro de Banco (SQLite):** O campo `source` na tabela `duque_ia_chunks` associa o vetor gerado à string identificadora.
4.  **Resposta ao Munícipe (Frontend):** O agente expõe a chave `sources` no JSON de retorno, que é renderizado em blocos no chat (como exibido no rodapé dos prints com o nome dos arquivos MD).

---

## 3. Plano de Ação Recomendado para Governança

1.  **Remoção de Tabelas Mortas (Clean DDL):** Simplificar o DDL oficial excluindo tabelas não utilizadas (`users`, `service_priorities`, `service_history`, etc.) para reduzir o tamanho do banco e complexidade lógica do DER (Diagrama Entidade-Relacionamento).
2.  **Substituição do Histórico Stateless por Sessões Relacionais:** Integrar o uso real das tabelas `chat_sessions` e `chat_messages` para armazenar os diálogos, permitindo análises ricas de uso e retenção em produção.
3.  **Auditoria Automatizada de Chunks Órfãos:** Criar uma rotina em `ingestion/embed/main.py` para listar chaves no banco que não possuem mais arquivos correspondentes sob `data/processed/`, removendo-os (garbage collector vetorial).
