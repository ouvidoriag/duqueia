# Relatório de Código Morto e Módulos Obsoletos — DUQUE IA

> **Auditoria do Projeto — Etapa 2**  
> **Data:** 2026-07-28 | **Sistema:** DUQUE IA (Prefeitura de Duque de Caxias — RJ)

---

## 🔍 Mapeamento de Código Morto e Módulos Descontinuados

A auditoria identificou módulos e scripts que não possuem mais chamadas ativas no runtime do agente (`agent/main.py`), no gateway Node.js (`server.js`) ou na suíte automatizada de testes (`scripts/run_all_tests.py`).

---

## 📋 Lista de Itens Identificados e Arquivados

| Arquivo / Componente | Motivo da Obsolecência | Destino no Archive | Status |
| :--- | :--- | :--- | :--- |
| `parse_csv.py` e `parse_excel.py` | Parsers de CSV e Excel legados. | [archive/legacy_parsers/](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/archive/legacy_parsers) | **ARQUIVADO** |
| `Documentacao_Relatorio_30_Perguntas_Impressao.html` e outros | Relatórios HTML de testes na raiz. | [archive/html_reports/](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/archive/html_reports) | **ARQUIVADO** |
| `setup_supabase.py` e `production_schema_supabase.sql` | Scripts de setup Supabase/Postgres não utilizados. | [archive/legacy_scripts/](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/archive/legacy_scripts) | **ARQUIVADO** |
| `inspect_db_carta.py`, `test_terreno_query.py`, etc. | Scripts pontuais de debug em `scripts/`. | [archive/legacy_scripts/](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/archive/legacy_scripts) | **ARQUIVADO** |
| Scripts em `scratch/` (30 arquivos) | Experimentos e geradores de relatórios temporários. | [archive/scratch_experiments/](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/archive/scratch_experiments) | **ARQUIVADO** |
| `logs/` (na raiz) | Log legados da estrutura monolítica. | Removida da raiz (mantida em `data/logs/`). | **EXCLUÍDO** |

---

## 🛡️ Validação de Segurança Antes da Remoção

* **Execução dos Testes:** Todos os itens arquivados foram verificados contra a suíte de testes (`python scripts/run_all_tests.py`) para confirmar que nenhum import ou dependência quebrou.
* **Preservação de Dados:** Nenhum schema do banco relacional ou vetorial foi alterado ou excluído.

