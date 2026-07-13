# Central de Documentação — Duque IA

Bem-vindo à documentação oficial do **DUQUE IA**, a plataforma e assistente virtual inteligente da Prefeitura de Duque Caxias — RJ.

Este espaço centraliza todos os aspectos técnicos, funcionais, de arquitetura e infraestrutura do projeto, servindo como a **Única Fonte da Verdade (Single Source of Truth - SSOT)**.

## Estrutura da Documentação

Navegue pelos módulos usando os links abaixo:

### 1. [Módulo 01 - Projeto](01-Projeto/Visao-Geral.md)
- [Visão Geral](01-Projeto/Visao-Geral.md) — Escopo, regras e objetivos.
- [Arquitetura](01-Projeto/Arquitetura.md) — Diagrama e componentes do sistema RAG.
- [Fluxo de Dados](01-Projeto/Fluxo.md) — Como a informação é recebida, processada e respondida.

### 2. [Módulo 02 - Instalação](02-Instalacao/Instalacao.md)
- [Guia de Instalação](02-Instalacao/Instalacao.md) — Configuração rápida do ambiente.
- [Configuração de Ambiente](02-Instalacao/Ambiente.md) — Variáveis e arquivos `.env`.
- [Variáveis de Ambiente](02-Instalacao/Variaveis.md) — Detalhamento de cada chave.
- [Dependências](02-Instalacao/Dependencias.md) — Módulos do Node.js e bibliotecas Python.

### 3. [Módulo 03 - Banco de Dados](03-Banco/Banco.md)
- [Visão Geral do Banco](03-Banco/Banco.md) — SQLite local.
- [Diagrama Entidade-Relacionamento](03-Banco/DER.md) — Modelo e relacionamentos.
- [Dicionário de Dados](03-Banco/Dicionario.md) — Tabelas e campos.
- [Estrutura Física](03-Banco/Estrutura.md) — Índices, Constraints e Chaves.
- [Migrations e Seeds](03-Banco/Migrations.md) — Estrutura de inicialização.

### 4. [Módulo 04 - API](04-API/Endpoints.md)
- [Endpoints](04-API/Endpoints.md) — Rotas HTTP.
- [Autenticação](04-API/Autenticacao.md) — Segurança e Sessões.
- [Exemplos de Requisição](04-API/Exemplos.md) — Testando integrações.

### 5. [Módulo 05 - Frontend](05-Frontend/Estrutura.md)
- [Estrutura do Frontend](05-Frontend/Estrutura.md) — Arquivos e assets estáticos.
- [Componentes](05-Frontend/Componentes.md) — CSS vanilla e scripts de Chat.
- [Rotas do Cliente](05-Frontend/Rotas.md) — Páginas html estáticas.

### 6. [Módulo 06 - Backend](06-Backend/Controllers.md)
- [Controllers](06-Backend/Controllers.md) — Gerenciamento do servidor Node.js.
- [Services](06-Backend/Services.md) — Spawner de processos do Agente Python.
- [Middlewares](06-Backend/Middlewares.md) — Tratamento de erros e timeout.

### 7. [Módulo 07 - Inteligência Artificial](07-IA/Prompts.md)
- [Prompts e Instruções](07-IA/Prompts.md) — Engenharia de prompts para o RAG.
- [Fluxos de IA](07-IA/Fluxos.md) — Triagem e Roteamento de intenções.
- [Agentes Autónomos](07-IA/Agentes.md) — Agente Coletor e RAG Handler.

### 8. [Módulo 08 - Deploy](08-Deploy/Produção.md)
- [Manual de Produção](08-Deploy/Produção.md) — Passos de deploy.
- [Configuração Docker](08-Deploy/Docker.md) — Orquestração de containers.
- [Hospedagem no Render/VPS](08-Deploy/Render.md) — Passos recomendados.

### 9. [Módulo 09 - Testes](09-Testes/Testes.md)
- [Suíte de Testes](09-Testes/Testes.md) — Como executar.
- [Casos de Teste](09-Testes/Casos.md) — Cobertura e validações.

### 10. [Módulo 10 - Manutenção](10-Manutencao/Checklist.md)
- [Checklist Operacional](10-Manutencao/Checklist.md) — Rotinas diárias.
- [Políticas de Backup](10-Manutencao/Backup.md) — Segurança de dados.
- [Atualizações](10-Manutencao/Atualizacoes.md) — Manutenção corretiva.

---
[Voltar ao Início](../README.md)
