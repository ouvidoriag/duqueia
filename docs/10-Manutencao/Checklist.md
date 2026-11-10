# Checklist Operacional de Manutenção — Duque IA

Siga este checklist semanalmente para garantir o bom funcionamento do Duque IA:

- [ ] Verificar se as chaves da API do Gemini estão ativas e válidas no arquivo `.env`.
- [ ] Analisar os logs em `logs/` para monitorar erros ou falhas de comunicação Python/Node.js.
- [ ] Checar a integridade física dos bancos de dados em `data/db/` usando `python scripts/check_db.py`.
- [ ] Executar o diagnóstico automatizado de infraestrutura: `python setup_and_run.py --health`.
- [ ] Limpar logs obsoletos ou duplicados com mais de 30 dias de criação.

---
[Avançar: Backup](Backup.md) | [Voltar ao Sumário](../README.md)
