# Diagrama Entidade-Relacionamento (DER) — Duque IA

```mermaid
erDiagram
    secretarias ||--o{ secretaria_unidades : "possui"
    secretarias ||--o{ users : "pertence"
    secretarias ||--o{ categories : "classifica"
    secretarias ||--o{ services : "oferece"
    categories ||--o{ services : "contém"
    services ||--o{ service_phones : "possui"
    services ||--o{ service_emails : "possui"
    services ||--o{ service_links : "possui"
    services ||--o{ service_steps : "possui"
    services ||--o{ service_documents : "requer"
    services ||--o{ service_priorities : "define"
    services ||--o{ service_categories : "associa"
    services ||--o{ service_history : "registra"
    users ||--o{ service_history : "altera"
    chat_sessions ||--o{ chat_messages : "contém"
    chat_messages ||--o{ chat_feedback : "recebe"
    chat_messages ||--o{ rag_queries : "mapeia"
    core_documents ||--o{ chunks_metadata : "origina"
```

## Relacionamentos Principais
- **1:N (Secretarias para Serviços)**: Uma secretaria gerencia diversos serviços públicos.
- **1:N (Serviços para Telefones/E-mails/Passos)**: Cada serviço municipal detalhado na Carta de Serviços possui múltiplos meios de contato e etapas de solicitação.
- **1:N (Sessões para Mensagens)**: Cada sessão de chat possui o histórico de diálogos do munícipe.

---
[Avançar: Dicionário](Dicionario.md) | [Voltar: Banco](Banco.md)
