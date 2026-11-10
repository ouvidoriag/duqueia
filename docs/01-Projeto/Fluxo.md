# Fluxo de Processamento de Dados — Duque IA

O diagrama abaixo detalha o caminho percorrido por uma mensagem enviada pelo munícipe até o retorno da resposta estruturada.

```mermaid
sequenceDiagram
    participant C as Cliente Web / App
    participant N as Servidor Node.js
    participant P as Worker Python (Pool)
    participant F as Fast Gate (Regras Locais 0ms)
    participant GS as Golden Source (443 Unidades)
    participant T as Triagem (Cache / LLM)
    participant R as Retrieval Híbrido (RRF)
    participant L as Gemini API (LLM)
    participant G as Output Guardrail

    C->>N: POST /api/chat { message, sessionId }
    N->>P: Envia JSON com request_id via stdin
    P->>F: Camada 0: Fast Gate (Segurança LGPD / Autoridades)
    alt Bloqueio de Segurança / LGPD / Escopo
        F-->>P: Retorna recusa padrão ou encaminhamento Ouvidoria
    else Consulta Direta de Equipamento / Endereço
        P->>GS: Camada 0.5: GoldenSourceResolver (SQL main.db)
        alt Unidade / Secretaria Encontrada (Sub-10ms)
            GS-->>P: Retorna resposta determinística (100% Grounded, 0 tokens)
        else Pergunta de Serviço / RAG Geral
            P->>T: Camada 1: Triagem (Cache SQLite L1 ou Gemini)
            T-->>P: Intenção classificada (ex: RAG_GERAL, COLETA, AMBIGUIDADE)
            alt RAG_GERAL
                P->>R: Busca Híbrida (Vetor 3072 dim + FTS5)
                R-->>P: Top Chunks relevantes (RRF Fusion)
                P->>L: Envia prompt com chunks recuperados
                L-->>P: Retorna resposta gerada
                P->>G: Output Guardrail (Anti-Alucinação)
                G-->>P: Resposta validada com fontes
            else AGENTE_COLETOR / OUTROS
                P->>P: Dispara Handler especializado (Coleta incremental)
            end
        end
    end
    P-->>N: Resposta JSON via stdout (com telemetria e cronometria)
    N-->>C: Retorna resposta HTTP 200 (JSON estruturado)
```

---
[Avançar: Instalação](../02-Instalacao/Instalacao.md) | [Voltar: Arquitetura](Arquitetura.md)

