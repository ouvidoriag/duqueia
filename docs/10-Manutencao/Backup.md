# Políticas de Backup — Duque IA

Como o Duque IA armazena todas as informações em bancos locais SQLite em `data/db/` (`main.db`, `vector.db`, `cache.db`, `telemetry.db`), o backup torna-se extremamente simples e seguro.

## Backup Físico
Recomenda-se realizar uma cópia fria do diretório `data/db/` periodicamente e salvar em local seguro (cloud storage externo ou servidor de backup).

## Backup Lógico (SQL Dump)
Você pode exportar a estrutura e os dados relacionais do banco principal em formato SQL legível:
```bash
sqlite3 data/db/main.db .dump > backup_main.sql
sqlite3 data/db/vector.db .dump > backup_vector.sql
```

---
[Avançar: Atualizações](Atualizacoes.md) | [Voltar: Checklist](Checklist.md)
