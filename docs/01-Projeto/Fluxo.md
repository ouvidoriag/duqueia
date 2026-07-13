# Fluxo de Processamento de Dados — Duque IA

O diagrama abaixo detalha o caminho percorrido por uma mensagem enviada pelo munícipe até o retorno da resposta estruturada.

```mermaid
sequenceDiagram
    participant C as Cliente Web
    participant N as Servidor Node.js
    participant A as Agente Python
    participant T as Triagem
    participant G as Guardrails
    participant R as Retrieval (RAG)
    participant L as Gemini API

    C->>N: Envia mensagem (session_id)
    N->>A: Escreve no stdin do processo Python da sessão
    A->>G: Input Guardrail (Validação de Prompt/SQL Injection)
    alt Inválido ou Bloqueado
        G-->>A: Retorna erro de segurança
    else Válido
        A->>T: Executa Triagem (Histórico + Pergunta)
        T->>L: Classifica intenção
        L-->>T: Retorna Intenção (Ex: RAG_GERAL, SAUDACAO)
        alt RAG_GERAL
            A->>R: Busca contexto no SQLite
            R-->>A: Retorna chunks relevantes
            A->>L: Envia prompt de resposta + contexto
            L-->>A: Retorna resposta bruta
            A->>G: Output Guardrail (Valida alucinação)
            G-->>A: Resposta aprovada
        else SAUDACAO / Outros
            A->>A: Executa Handler específico
        end
    end
    A-->>N: Escreve objeto JSON no stdout
    N-->>C: Retorna resposta HTTP (JSON)
```

---
[Avançar: Instalação](../02-Instalacao/Instalacao.md) | [Voltar: Arquitetura](Arquitetura.md)
