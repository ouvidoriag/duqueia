# Deploy no Render ou VPS — Duque IA

Para deploy em serviços como **Render**, **Heroku** ou **VPS Dedicada (DigitalOcean/AWS)**:

## Passos para VPS (Ubuntu/Debian)
1. Instale o Node.js e o Python3:
   ```bash
   sudo apt update
   sudo apt install nodejs npm python3 python3-pip -y
   ```
2. Clone o repositório e configure as chaves no arquivo `.env`.
3. Execute o setup e utilize o gerenciador de processos `pm2` para manter o Node.js rodando em background:
   ```bash
   npm run build
   sudo npm install pm2 -g
   pm2 start server.js --name "duqueia"
   ```

---
[Avançar: Testes](../09-Testes/Testes.md) | [Voltar: Docker](Docker.md)
