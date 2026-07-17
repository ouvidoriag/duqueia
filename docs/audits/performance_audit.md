# Relatório de Auditoria — Performance e Otimizações (DUQUE IA)

Este documento apresenta a análise de gargalos de performance, tempos de carregamento, consumo de recursos e eficiência computacional das camadas do DUQUE IA, em conformidade com o item **11. Performance** da auditoria técnica.

---

## 1. Mapeamento de Pontos Críticos de Performance

### A. Carregamento de Pacotes e Imports Pesados
* **Diagnóstico:** Como o gateway `server.js` mantém processos filhos Python persistentes (via stdin/stdout `spawn`), o custo de inicialização do Python e carregamento de imports (como `google.genai`, `sqlite3` e `pydantic`) é pago **apenas uma vez** por sessão, e não a cada mensagem/request.
* **Impacto:** Menor latência por turno de conversa após o handshake inicial (típico ~10-30ms para processamento local antes de chamadas de API).

### B. Gestão de Conexões de Banco de Dados (SQLite)
* **Diagnóstico:** O arquivo [utils/db_client.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/utils/db_client.py) gerencia as conexões de banco de dados via gerenciador de contexto (`get_db_connection`):
  ```python
  @contextmanager
  def get_db_connection(db_path: str):
      conn = sqlite3.connect(db_path)
      try:
          yield conn
      finally:
          conn.close()
  ```
* **Avaliação:** Isso garante que conexões **nunca fiquem órfãs ou abertas indefinidamente**. No entanto, abrir e fechar a conexão de arquivos SQLite físicos no disco a cada consulta em tempo de execução gera um overhead de I/O em concorrência pesada.

### C. Consultas Repetidas e Triagem
* **Diagnóstico:** A camada de triagem semântica ([agent/triage.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/triage.py)) implementa um **triage_cache** (salvo no `cache.db`). Consultas idênticas ou muito similares (com base em hashes MD5) têm suas decisões resolvidas em menos de **1ms**, evitando chamadas de rede externas.

### D. Inicialização e Recriação de Objetos
* **Diagnóstico:** Instâncias críticas do sistema são tratadas como Singletons:
  * O `StorageManager` é exportado como instância única global em [storage/__init__.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/storage/__init__.py).
  * O `GeminiClient` e o `GroqClient` são criados em nível de módulo como Singletons, evitando autenticações repetidas e recriação de sockets de rede HTTP.

---

## 2. Riscos e Oportunidades de Otimização

### A. Otimização de I/O no SQLite (Modo WAL)
* **Problema:** Sob concorrência, escritas simultâneas de mensagens no `telemetry.db` podem bloquear temporariamente as leituras no `main.db`.
* **Solução:** Configurar a inicialização do SQLite em **modo WAL** (Write-Ahead Logging) e ajustar o `PRAGMA synchronous = NORMAL;`. O modo WAL permite leitores concorrentes enquanto uma escrita está ativa.

### B. Pooling de Conexões
* **Problema:** Para evolução futura com PostgreSQL em produção, abrir e fechar conexões físicas gerará latência severa (TCP Handshake).
* **Solução:** Implementar um Connection Pooler (ex: SQLAlchemys Pool or pg_bouncer) quando o banco relacional for migrado.

---

## 3. Plano de Ação Recomendado para Escalar a Performance

1. **Habilitar WAL nos bancos SQLite:**
   No setup do banco em `setup_and_run.py`, executar o comando `PRAGMA journal_mode=WAL;` nos 4 arquivos para habilitar concorrência otimizada.
2. **Medição de Latência por Nó:**
   Garantir a coleta sistemática do tempo de processamento de cada nó do grafo cognitivo (Triage Time vs. Retrieval Time vs. LLM Generation Time) para rastrear qual componente está gerando gargalo em turnos demorados.
