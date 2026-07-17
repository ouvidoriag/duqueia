# 📄 Duque IA — Documentação de Modelos de IA e Chaves de API

Este documento explica em detalhes quais APIs de Inteligência Artificial o **Duque IA** utiliza, quais são os modelos selecionados para cada tarefa (geração de texto e embeddings), como eles são chamados internamente no código e como funciona o sistema de gerenciamento e rotação de chaves.

---

## 1. APIs e Provedores de IA Utilizados

O framework RAG do Duque IA foi projetado com flexibilidade e redundância em mente, suportando os seguintes provedores:

### 🚀 Google Gemini API (Provedor Principal)
*   **Finalidade**: Geração de texto (respostas aos munícipes, triagem inteligente de intenções, classificação de relevância) e geração de representações vetoriais (embeddings).
*   **SDK**: Utiliza preferencialmente o novo SDK oficial do Google (`google.genai`), com uma camada de compatibilidade para o SDK legado (`google.generativeai`) caso o ambiente exija.
*   **Diferencial**: Suporta rotação automática de chaves em caso de falha de limite de cota (Rate Limits) ou erros de conexão.

### 🧪 OpenAI API (Provedor Alternativo)
*   **Finalidade**: Backend alternativo para geração de texto ou embeddings caso configurado pelo administrador.
*   **Configuração**: Habilitado mediante definição da variável `OPENAI_API_KEY` no ambiente.

---

## 2. Modelos Utilizados e Suas Aplicações

O Duque IA segmenta o uso de IA em tarefas específicas para garantir eficiência, baixa latência e custos otimizados:

| Modelo | Tipo / Provedor | Função no Sistema | Configuração |
| :--- | :--- | :--- | :--- |
| **`gemini-2.5-flash`** | LLM / Google | Geração de texto, Triagem de intenções, Classificação e formulação final de respostas. | `GEMINI_MODEL` |
| **`gemini-embedding-2`** | Embeddings / Google | Conversão de chunks de texto (PDFs, dados públicos) em vetores de 3072 dimensões. | `GEMINI_EMBEDDING_MODEL` |

### 🛠️ Estratégias de Fallback de Modelos de Embeddings
Se o modelo principal (`gemini-embedding-2`) não estiver disponível no endpoint da chave ativa, o sistema tenta automaticamente os seguintes modelos em ordem de prioridade:
1. `gemini-embedding-2`
2. `gemini-embedding-2-preview`
3. `gemini-embedding-001`

---

## 3. Como o Código Utiliza as IAs

### A. Triagem Inteligente (Triage Layer)
Antes de buscar no banco vetorial (RAG), o Duque IA submete a query do usuário à **Camada de Triagem (`triage.py`)**. 
- O modelo classifica a intenção em uma categoria: `GIS` (perguntas territoriais/geográficas), `INSTITUTIONAL` (informações sobre secretarias), `GENERAL` (informações de Duque de Caxias) ou `LIST` (listagem de serviços).
- Identifica se a pergunta exige esclarecimento (`needs_clarification`) ou se viola alguma regra de segurança (como LGPD ou escopo extra-municipal).

### B. Recuperação Semântica (RAG)
1. **Geração de Embedding**: A query do usuário é convertida em um vetor pelo `GeminiClient` usando o modelo de embedding ativo.
2. **Busca Vetorial**: O sistema realiza uma busca de similaridade de cosseno no banco de dados SQLite (`vector.db` localmente) ou Supabase (PGVector em produção) para recuperar os chunks mais relevantes.
3. **Prompt Final**: O LLM (`gemini-2.5-flash`) recebe a pergunta original acompanhada exclusivamente dos chunks retornados e formata a resposta no padrão exigido.

---

## 4. Gerenciamento e Rotação de Chaves de API

Para evitar interrupções de serviço por limites de cota (*Rate Limits* / *TPM* / *RPM*), o Duque IA implementa um sistema robusto de gerenciamento de chaves em `utils/gemini_client.py`:

### Configuração no `.env`
As chaves de API são configuradas na variável `GEMINI_API_KEYS`, aceitando múltiplas chaves separadas por vírgula:
```bash
GEMINI_API_KEYS=AIzaSy_chave1_aqui,AIzaSy_chave2_aqui,AQ.Ab8RN_token_aqui
```
*   **Chaves do AI Studio**: Começam com `AIzaSy`.
*   **Tokens do Vertex AI**: Começam com `AQ.`.

### 🔄 Funcionamento da Rotação Automática
1. **Leitura e Filtragem**: O cliente inicializa lendo `GEMINI_API_KEYS` e descarta chaves inválidas.
2. **Chave Ativa**: Começa utilizando a primeira chave da lista (`index 0`).
3. **Mecanismo de Retentativa (Retry & Rotate)**: 
   - Se uma chamada à API falhar devido a erro de cota (ex: HTTP 429) ou expiração, o `GeminiClient` marca a chave atual como indisponível (coloca em *cooldown*) e rotaciona para a próxima chave válida da lista (`index 1`).
   - O processo se repete de forma transparente para o usuário final, aumentando muito a resiliência do sistema em produção.
4. **Modo de Teste**: Se a variável `DUQUE_IA_TEST_MODE=1` estiver ativa, o sistema intercepta as chamadas e utiliza respostas mockadas para poupar saldo e evitar dependência de rede durante suítes de testes automatizados.
