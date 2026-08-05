# Guia de Instalação — Duque IA

Siga os passos abaixo para configurar e executar a plataforma Duque IA localmente em poucos minutos.

## Requisitos Prévios
- Node.js (versão `>= 18.0.0`)
- Python 3.10 ou superior
- Pip (gerenciador de pacotes do Python)

## Passo a Passo
1. **Clone o repositório** para a sua máquina local.
2. **Crie e ative o ambiente virtual (Recomendado)**:
   ```bash
   python3 -m venv .venv
   # No Linux/macOS:
   source .venv/bin/activate
   # No Windows (PowerShell):
   # .venv\Scripts\Activate.ps1
   ```
3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   npm install
   ```
4. **Configure as Variáveis de Ambiente**:
   Crie um arquivo `.env` na raiz do projeto (veja detalhes em [Ambiente](Ambiente.md)).
5. **Alimente o Banco de Dados (Embeddings)**:
   ```bash
   python ingestion/parser/parse_pdfs.py
   python ingestion/embed/main.py --config ingestion/embed/embed_config.yml
   ```
6. **Inicie o Servidor**:
   ```bash
   npm start
   ```
   O servidor estará disponível em `http://localhost:3000`.

---
[Avançar: Ambiente](Ambiente.md) | [Voltar ao Sumário](../README.md)
