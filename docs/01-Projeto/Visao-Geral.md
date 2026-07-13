# Visão Geral do Projeto — Duque IA

O **Duque IA** é o assistente virtual oficial e plataforma RAG da Prefeitura Municipal de Duque de Caxias — RJ. 

## Objetivos do Sistema
- Facilitar o atendimento ao munícipe por meio de IA generativa de alta fidelidade baseada em dados reais e oficiais.
- Sanar dúvidas comuns sobre secretarias municipais, localizações de postos de saúde, CRAS, escolas, Carta de Serviços, e IPTU.
- Coletar informações de forma incremental para reclamações, denúncias e elogios que serão direcionados para a Ouvidoria Geral.

## Diretrizes de Atendimento Conversacional (POP)
- **Blindagem Conversacional**: A IA cumprimenta o munícipe com "Olá!" apenas na primeira interação. Respostas subsequentes são diretas, curtas, variadas e naturais, sem saudações repetidas.
- **Competência Municipal**: Perguntas fora da competência municipal (como metrô ou rodovias federais) são bloqueadas de forma preventiva.
- **Segurança e Privacidade (LGPD)**: O sistema proíbe o fornecimento de CPFs, nomes de reclamantes e andamentos de protocolos de terceiros.
- **Redirecionamento Claro**: Se as informações não forem encontradas, o sistema redireciona o munícipe diretamente para os canais da Ouvidoria Geral:
  - Telefone: **(21) 2652-3835**
  - WhatsApp: **(21) 99824-5903**
  - E-mail: **ouvidoria@duquedecaxias.rj.gov.br**

---
[Avançar: Arquitetura](Arquitetura.md) | [Voltar ao Sumário](../README.md)
