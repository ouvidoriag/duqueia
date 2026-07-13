# Relacionamentos do Banco de Dados — Duque IA

O banco de dados SQLite (`agent/duque_ia.db`) implementa uma estrutura de dados relacional clássica para gerenciar o conteúdo estático, logs de conversas, triagem e sessões.

## Relacionamentos 1:1 (Um para Um)
- **`chat_messages` para `rag_queries`**: Cada log de consulta RAG está associado a exatamente uma mensagem específica na sessão de chat (`message_id` em `rag_queries` é único ou chave primária virtual apontando para `chat_messages.id`).

## Relacionamentos 1:N (Um para Vários)
- **`secretarias` para `secretaria_unidades`**: Uma secretaria contém múltiplas unidades de atendimento (Ex: SMS possui diversas UPAs e Postos de Saúde).
- **`secretarias` para `users`**: Uma secretaria possui múltiplos usuários associados (Editores, Revisores).
- **`secretarias` para `services`**: Uma secretaria é responsável por gerenciar e oferecer vários serviços municipais.
- **`services` para `service_phones` / `service_emails` / `service_links`**: Cada serviço possui diversos telefones de contato, endereços de e-mail alternativos e links úteis.
- **`services` para `service_steps`**: Cada serviço possui um fluxo sequencial contendo múltiplas etapas (`step_number`).
- **`services` para `service_documents` / `service_priorities`**: Cada serviço pode exigir múltiplos documentos e aceitar variados tipos de prioridades de atendimento.
- **`chat_sessions` para `chat_messages`**: Uma sessão de conversação armazena o histórico completo com múltiplas mensagens do cidadão e respostas do assistente.

## Relacionamentos N:N (Muitos para Muitos)
- **`services` para `categories` via `service_categories`**: Um serviço pode estar enquadrado em múltiplas categorias de atendimento, assim como uma categoria pode englobar múltiplos serviços. Esse mapeamento N:N é controlado pela tabela associativa `service_categories`.

---
[Voltar: DER](DER.md) | [Voltar ao Sumário](../README.md)
