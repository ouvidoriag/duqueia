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

## 3. Instalação e Ambiente Virtual (.venv)
Em distribuições Linux com Python 3.13+ (Ubuntu 23+/Debian 12+), o Python protege o ambiente do sistema (PEP 668). É mandatório utilizar um ambiente virtual:

```bash
# Instalar suporte a venv no sistema
sudo apt install python3-venv python3-full -y

# Criar e ativar o ambiente virtual na pasta do projeto
python3 -m venv .venv
source .venv/bin/activate

# Atualizar pip e instalar dependências Python
pip install --upgrade pip
pip install -r requirements.txt

# Instalar dependências Node.js
npm install
```

Alimente o banco de dados (se for a primeira execução e você não trouxe o banco já populado):

```bash
python3 ingestion/parser/parse_pdfs.py
python3 ingestion/embed/main.py --config ingestion/embed/embed_config.yml
```

## 4. Gerenciamento do Processo com PM2
Para manter o servidor executando continuamente em segundo plano com suporte automático ao intérprete `.venv`:

```bash
sudo npm install -g pm2

# Opção 1: Utilizando o arquivo de ecossistema (Recomendado - auto-detecta .venv)
pm2 start ecosystem.config.js

# Opção 2: Especificando explicitamente o Python do ambiente virtual
pm2 start setup_and_run.py --name "duqueia" --interpreter .venv/bin/python

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
