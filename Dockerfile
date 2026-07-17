# Dockerfile para Produção — DUQUE IA
# Combina ambiente Python 3.11 (para o Agente Cognitivo) e Node.js (para o Servidor Web)

FROM python:3.11-slim

# Instala curl, nodejs, npm e ferramentas essenciais do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia os arquivos de dependência do Python e instala
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia os pacotes de dependência do Node.js e instala em modo de produção
COPY package.json package-lock.json* ./
RUN npm ci || npm install --omit=dev

# Copia todo o código da aplicação
COPY . .

# Cria os diretórios de persistência de dados para garantir permissões corretas
RUN mkdir -p data/db logs metrics

# Expõe a porta padrão do servidor web Node.js
EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

# Comando padrão que executa o setup e inicia o servidor
CMD ["python", "setup_and_run.py"]
