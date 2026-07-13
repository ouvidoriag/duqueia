# Banco de Dados — Duque IA

O Duque IA armazena suas informações em um banco de dados local **SQLite** (`agent/duque_ia.db`).

## Arquitetura do Banco
O banco foi planejado para servir a dois propósitos distintos:
1. **Banco Vetorial RAG**: Armazena chunks de documentos e seus respectivos embeddings em formato de vetor serializado em texto (para compatibilidade offline rápida).
2. **Gestão Operacional de Serviços (CMS)**: Estrutura relacional para gerenciar secretarias, serviços municipais, telefones, e-mails, logs de atendimento, histórico de interações e sessões dos munícipes.

---
[Avançar: DER](DER.md) | [Voltar ao Sumário](../README.md)
