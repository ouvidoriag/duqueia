# Relatório de Auditoria de Segurança e Guardrails — DUQUE IA

> **Auditoria do Projeto — Etapa 8**  
> **Data:** 2026-07-28 | **Sistema:** DUQUE IA (Prefeitura de Duque de Caxias — RJ)

---

## 🛡️ 1. Proteção de Credenciais e Segredos

* **Isolamento de Chaves de API:** As chaves de API reais do Google Gemini e Groq estão isoladas exclusivamente no arquivo `.env`, o qual está registrado no `.gitignore` para impedir comits acidentais no Git.
* **Segurança do `.env.example`:** O arquivo de exemplo de ambiente contém apenas referências genéricas (`sua_chave_aqui`), estando 100% livre de segredos expostos.

---

## 🔒 2. Guardrails de Entrada (Input Guardrails)

O módulo [agent/guardrails.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/guardrails.py) impõe barreiras automatizadas contra ataques e mal-uso:

1. **Prevenção contra SQL Injection:** Consultas no SQLite utilizam queries parametrizadas com placeholders `?` via `db_client.py`.
2. **Prevenção contra Prompt Injection:** Padrões maliciosos (ex: *"Ignore todas as instruções anteriores"*, *"Você agora é um assistente irrestrito"*) são interceptados no nó `fast_gate` (0ms).
3. **Privacidade e LGPD:** Buscas por CPFs de terceiros, nomes de munícipes ou andamento de denúncias de vizinhos são barradas e respondidas com recusa padronizada.
4. **Competência Municipal:** Perguntas sobre temas federais ou estaduais (Dutra, BR-040, Metrô, INSS) são bloqueadas com redirecionamento de incompetência municipal.

---

## 🔍 3. Guardrails de Saída (Output Guardrails)

* **Auditoria Anti-Alucinação:** O `check_output_guardrail` compara as afirmações da resposta com os chunks recuperados do banco vetorial e relacional.
* **Fallback Seguro:** Se a confiança for baixa ou a resposta for inconsistente com as fontes, o sistema aciona automaticamente os canais oficiais da Ouvidoria Geral:
  * **Telefone:** (21) 2652-3835
  * **WhatsApp:** (21) 99824-5903

---

## 📊 Status da Segurança

| Item Auditado | Status | Observação |
| :--- | :--- | :--- |
| **Proteção de Segredos (.env)** | **APROVADO** | Chaves mantidas fora do versionamento Git. |
| **Queries Parametrizadas** | **APROVADO** | Zero concatenação de strings em comandos SQL. |
| **Compliance LGPD** | **APROVADO** | Filtro contra dados sensíveis de terceiros ativo. |
| **Competência Municipal** | **APROVADO** | Respostas restritas ao âmbito da Prefeitura. |
