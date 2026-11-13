# 🏛️ Auditoria Arquitetural e Diagnóstico de Falhas e Melhorias — Duque IA

**Data da Auditoria:** 13 de Novembro de 2026  
**Perfil do Auditor:** Arquiteto Sênior de IA (RAG, Vector Databases, Guardrails e Sistemas de Governo)  
**Escopo:** Código-fonte Python (`/agent`, `/scripts`, `/utils`), Servidor Gateway (`server.js`), 4 Bases de Dados SQLite (`main.db`, `vector.db`, `cache.db`, `telemetry.db`), Webhook GSE/OGM e Frontend.

---

## Executive Summary (Resumo Executivo)

A auditoria profunda de integridade e arquitetura revelou que o núcleo da Duque IA está em estado avançado de maturidade:
* **Sintaxe & Compilação:** 100% dos 116 arquivos Python compilam com sucesso.
* **Integridade de Bases:** Todas as 4 bases de dados SQLite passam em `PRAGMA integrity_check` e `PRAGMA foreign_key_check` com **0 erros**.
* **Banco Vetorial:** O `vector.db` está em **45,29 MB**, perfeitamente abaixo do limite de 50 MB do GitHub sem dependência de Git LFS.
* **Rotas Relativas:** 100% dos endpoints consumidos pelo frontend (`chat.html` e `dashboard.html`) são estritamente relativos, garantindo compatibilidade com proxy reverso Nginx.

No entanto, a auditoria identificou **5 pontos críticos (falhas e inconsistências de negócio)** e **3 melhorias de arquitetura** que requerem atenção imediata.

---

## 🔍 Falhas e Divergências Detectadas (Diagnóstico)

### 🔴 1. Divergência Crítica de Gabinete (2025–2028 vs `main.db`)
* **Problema:** O arquivo `agent/authorities_catalog.py` foi atualizado para o secretariado oficial da Gestão 2025–2028 (**Jonathas Monteiro Porto Neto / Netinho Reis**, **Aline do Aureo**, **Valber Rodrigues Januario** na SMOA, **Marcus Vinícius / Boquinha** na SMASDH). No entanto, a coluna `titular` da tabela `secretarias` no `main.db` ainda preserva o secretariado da gestão anterior (**Wilson Miguel dos Reis**, **Valdecy da Saúde**, **Janyr Menezes**).
* **Impacto no Cidadão:** 
  - Se perguntar *"quem é o prefeito"*, o `AuthorityHandler` responde **Netinho Reis**.
  - Mas se perguntar *"onde fica a prefeitura"* ou pedir dados de uma secretaria, o cartão determinístico (`GoldenSourceResolver`) exibe **Wilson Miguel dos Reis** ou o titular antigo de 2024.
* **Correção Necessária:** Atualizar a coluna `titular` de todas as secretarias em `main.db` para sincronizar 100% com o catálogo canônico da gestão 2025–2028.

---

### 🔴 2. Resíduo de WhatsApp Fictício em Registro Ativo de Iluminação Pública
* **Problema:** Na tabela `services` do `main.db`, no registro **ID 1802** (*Serviços de iluminação pública*), o campo `how_to_access` ainda contém o número proibido:
  `"...por meio do disque iluminação via zap 21 99824-5903 ou 21 2676-9099..."`
* **Impacto no Cidadão:** Em consultas sobre lâmpada queimada ou troca de poste, esse trecho pode ser recuperado pelo RAG e expor o número inexistente.
* **Correção Necessária:** Atualizar o registro 1802 no `main.db`, mantendo apenas o canal oficial: **Disque Iluminação (21) 2676-9099** e o aplicativo **Colab**.

---

### 🟡 3. Falta de Invalidação de Cache de Memória dos Workers após Webhook
* **Problema:** Quando a API do GSE/OGM envia um webhook de atualização cadastral (`/api/webhook/gse`), o `scripts/webhook_processor.py` atualiza o `main.db` e o `vector.db`. Porém, os 4 workers Python gerenciados pelo `server.js` mantêm a lista de unidades físicas em memória RAM (`GoldenSourceResolver._UNIDADES_CACHE`).
* **Impacto:** Os workers continuam respondendo com os telefones ou horários antigos até que o servidor Node seja reiniciado ou o endpoint administrativo `/api/admin/reload-workers` seja acionado manualmente.
* **Melhoria Necessária:** 
  1. No `server.js`, disparar o reload gracioso do pool de workers (`reloadPythonWorkers()`) assim que o processador do webhook concluir com código 0.
  2. No `GoldenSourceResolver`, verificar o timestamp de modificação do arquivo do banco de dados antes de usar o cache em RAM.

---

### 🟡 4. Falso Positivo Temático na Busca Estruturada de Unidades (RAG)
* **Problema:** Em `agent/retrieval.py` (linha 940), qualquer unidade cujo nome ou endereço contenha uma das palavras-chave da busca é adicionada como candidata. Quando o munícipe perguntou:
  *"Minha mãe tá passando mal e mora em Jardim Primavera. Onde fica a unidade de saúde mais próxima..."*
  O sistema casou *"Jardim Primavera"* e injetou o **CRAS Jardim Primavera** (Assistência Social) como fonte estruturada para uma emergência médica da Saúde!
* **Melhoria Necessária:** Quando a consulta for estritamente de saúde (`saúde`, `passando mal`, `médico`, `posto de saúde`, `hospital`), filtrar e priorizar unidades da **Secretaria Municipal de Saúde (SMS)**, impedindo que CRAS/CREAS poluam o contexto clínico.

---

### 🟢 5. Otimização do Tamanho de `authorities_catalog.py` (De 45.000 para < 500 Linhas)
* **Problema:** O arquivo `agent/authorities_catalog.py` possui **45.291 linhas (1,75 MB)** porque foi gerado repetindo exaustivamente centenas de permutações sintáticas de perguntas (*"voce sabe qual o nome do..."*). Como o `AuthorityHandler` já implementa limpeza de prefixos em tempo de execução via regex/strip, 95% desse arquivo é redundante.
* **Melhoria Necessária:** Consolidar o catálogo apenas com as 28 autoridades únicas e seus apelidos/sinônimos essenciais. Isso economizará memória RAM e tempo de inicialização em cada um dos 4 workers Python.

---

## 📋 Tabela Comparativa de Autoridades (Diagnóstico 2025–2028)

| Pasta / Órgão | Titular Atual no `main.db` (Antigo) | Titular Oficial 2025–2028 (`authorities_catalog.py`) | Situação |
| :--- | :--- | :--- | :---: |
| **CONS (Executivo)** | Wilson Miguel dos Reis / Roseli Duarte | **Jonathas Monteiro Porto Neto (Netinho Reis)** / **Aline do Aureo** | ❌ Divergente |
| **SMOA (Obras)** | Valdecy da Saúde | **Valber Rodrigues Januario** | ❌ Divergente |
| **SMASDH (Assistência)** | Janyr Menezes | **Marcus Vinícius de Moraes (Boquinha)** | ❌ Divergente |
| **SMG (Governo)** | Douglas Ribeiro | **Luciana R. Bertella** | ❌ Divergente |
| **SMA (Administração)** | Paulo Cesar dos Santos | **Fabrício Abílio** | ❌ Divergente |
| **SMMA (Meio Ambiente)**| Marcos Silva | **Vinicius Thomaz** | ❌ Divergente |
| **SMTSP (Transportes)** | Marco Oliveira | **Sandro Lellis** | ❌ Divergente |
| **SMSP (Segurança)** | José Carlos | **Vinícius Carvalho** | ❌ Divergente |
| **SMDC (Defesa Civil)** | Cel. André Xavier | **Ten.-Cel. Kaline Marcelino (CBMERJ)** | ❌ Divergente |
| **SMCT (Cultura)** | Simone Siqueira | **Aroldo Cândido de Brito** | ❌ Divergente |
| **SMEL (Esporte)** | Sérgio Corrêa | **Leandro Guimarães** | ❌ Divergente |
| **SMPA (Prot. Animal)** | Paulo Fernando de Souza | **Nadja Rissi (Naná)** | ❌ Divergente |
| **FUNDEC** | Jonas Santana Alves | **Roseli Duarte** | ❌ Divergente |
| **IPMDC** | Maria de Fátima Sanches | **Ana Carolina Freire Klojda** | ❌ Divergente |
| **CGM (Controle Int.)** | Sandra Regina Gaspar da Silva | **Patrícia Lucia Coll** | ❌ Divergente |
| **SME (Educação)** | Iracy Firmino dos Reis | **Iracema Medeiros da Costa Silva** | ⚠️ Grafia |
| **SMS (Saúde)** | Dra. Célia Serrano | **Dra. Célia Serrano da Silva** | ✅ Alinhado |
| **PGM (Procuradoria)** | Dr. Fabrício Gaspar Rodrigues | **Dr. Fabrício Gaspar Rodrigues** | ✅ Alinhado |

---

## 🎯 Plano de Ação Recomendado (Roadmap de Execução)

1. **Ação 1 (Imediata):** Sincronizar a tabela `secretarias` do `main.db` com o gabinete oficial 2025–2028.
2. **Ação 2 (Imediata):** Purgar o resíduo do WhatsApp `99824` no registro 1802 de iluminação pública.
3. **Ação 3 (Arquitetural):** Integrar o auto-reload de workers no `server.js` após eventos bem-sucedidos do Webhook.
4. **Ação 4 (Qualidade RAG):** Refinar o seletor estruturado de unidades em `retrieval.py` para isolar unidades de saúde de unidades de assistência social em perguntas clínicas.
5. **Ação 5 (Otimização):** Compactar `authorities_catalog.py` preservando 100% da acurácia com redução de 90% do tamanho do arquivo.

