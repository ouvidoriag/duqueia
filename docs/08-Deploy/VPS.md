# Deploy em Servidor VPS — Duque IA

Este guia descreve como realizar o deploy da plataforma Duque IA em um servidor virtual privado (VPS) rodando Ubuntu/Debian.

## 1. Instalação das Dependências do Sistema
Conecte-se ao seu servidor VPS via SSH e execute a atualização dos pacotes:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install nodejs npm python3 python3-pip python3-venv git -y
```

## 2. Clonagem do Repositório e Configuração
Clone o projeto na pasta `/var/www/`:

```bash
cd /var/www
git clone <url_do_repositorio> duqueia
cd duqueia
```

Crie o arquivo de ambiente `.env` e configure sua `GEMINI_API_KEY`:

```env
GEMINI_API_KEY=sua_chave_aqui
USE_TRIAGE_LAYER=true
SQLITE_DB_PATH=agent/duque_ia.db
```

## 3. Instalação e Inicialização
Instale as dependências Node.js e Python:

```bash
npm run build
```

Alimente o banco de dados (se for a primeira execução e você não trouxe o banco já populado):

```bash
python3 ingestion/parser/parse_pdfs.py
python3 ingestion/embed/main.py --config ingestion/embed/embed_config.yml
```

## 4. Gerenciamento do Processo com PM2
Para manter o servidor Node.js executando continuamente em segundo plano, utilize o gerenciador de processos PM2:

```bash
sudo npm install -g pm2
pm2 start server.js --name "duqueia"
pm2 save
pm2 startup
```

## 5. Configuração do Reverse Proxy (Nginx)
Recomenda-se usar o Nginx como proxy reverso para apontar o tráfego da porta 80/443 para a porta 3000 do Node:

```bash
sudo apt install nginx -y
```

Crie uma configuração em `/etc/nginx/sites-available/duqueia`:

```nginx
server {
    listen 80;
    server_name seu_dominio.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Habilite o site e reinicie o Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/duqueia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---
[Voltar: Render](Render.md) | [Voltar ao Sumário](../README.md)
