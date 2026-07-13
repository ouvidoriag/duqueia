# Guia de Instalação — Duque IA

Siga os passos abaixo para configurar e executar a plataforma Duque IA localmente em poucos minutos.

## Requisitos Prévios
- Node.js (versão `>= 18.0.0`)
- Python 3.10 ou superior
- Pip (gerenciador de pacotes do Python)

## Passo a Passo
1. **Clone o repositório** para a sua máquina local.
2. **Instale as dependências de desenvolvimento**:
   ```bash
   npm run build
   ```
   Este comando instalará todas as dependências Python a partir do arquivo `requirements.txt`.
3. **Configure as Variáveis de Ambiente**:
   Crie um arquivo `.env` na raiz do projeto (veja detalhes em [Ambiente](Ambiente.md)).
4. **Alimente o Banco de Dados (Embeddings)**:
   ```bash
   python ingestion/parser/parse_pdfs.py
   python ingestion/embed/main.py --config ingestion/embed/embed_config.yml
   ```
5. **Inicie o Servidor**:
   ```bash
   npm run dev
   ```
   O servidor estará disponível em `http://localhost:3000`.

---
[Avançar: Ambiente](Ambiente.md) | [Voltar ao Sumário](../README.md)
