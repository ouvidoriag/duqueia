# Manual de Deploy com Docker — Duque IA

O Duque IA fornece arquivos estruturados para dockerização de produção.

## Arquivos
Consulte o arquivo `docker-compose.yml` e `Dockerfile` (caso criados) na raiz do projeto.

## Execução
Para buildar e iniciar a aplicação em container:
```bash
docker-compose up --build -d
```
Este container encapsula o Node.js e instala o ambiente Python necessário automaticamente.

---
[Avançar: Render](Render.md) | [Voltar: Produção](Produção.md)
