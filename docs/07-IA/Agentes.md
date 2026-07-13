# Agentes Autónomos do Duque IA

A arquitetura do Duque IA implementa múltiplos Handlers inteligentes que agem como micro-agentes focados em tarefas:

1. **Agente Triador (`triage.py`)**: Classifica a intenção e avalia se há ambiguidades contextuais no diálogo.
2. **Agente Coletor (`CollectorHandler`)**: Atua na triagem incremental para Ouvidoria, coletando apenas um dado de cada vez com base nas respostas do munícipe.
3. **Agente RAG Handler (`RagHandler`)**: Realiza busca híbrida local e consolida dados de secretarias ou canais de atendimento.

---
[Avançar: Deploy](../08-Deploy/Produção.md) | [Voltar: Fluxos](Fluxos.md)
