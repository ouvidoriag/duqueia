# Guia de Deploy em Produção — Duque IA

Antes de mover a aplicação para produção, garanta as seguintes validações:

## 1. Banco de Dados Local
Certifique-se de copiar o banco SQLite `agent/duque_ia.db` completo e com os embeddings já gerados para o servidor.

## 2. Instalação e Execução
Execute o comando de inicialização automática de produção:
```bash
npm start
```
Isto fará a chamada para `setup_and_run.py`, que valida os pacotes Python e executa o servidor web Node.js.

---
[Avançar: Docker](Docker.md) | [Voltar ao Sumário](../README.md)
