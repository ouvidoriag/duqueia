# Políticas de Backup — Duque IA

Como o Duque IA armazena todas as informações em banco local SQLite (`agent/duque_ia.db`), o backup torna-se extremamente simples.

## Backup Físico Semanal
Recomenda-se realizar uma cópia fria do arquivo `agent/duque_ia.db` semanalmente e salvar em um local seguro (cloud storage externo ou servidor de backup).

## Backup Lógico (SQL Dump)
Você pode exportar a estrutura e os dados relacionais do banco em formato SQL legível:
```bash
sqlite3 agent/duque_ia.db .dump > backup_duque_ia.sql
```

---
[Avançar: Atualizações](Atualizacoes.md) | [Voltar: Checklist](Checklist.md)
