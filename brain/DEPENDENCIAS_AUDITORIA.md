# Relatório de Auditoria de Dependências — DUQUE IA

> **Auditoria do Projeto — Etapa 7**  
> **Data:** 2026-07-28 | **Sistema:** DUQUE IA (Prefeitura de Duque de Caxias — RJ)

---

## 📦 Visão Geral das Dependências

O **DUQUE IA** utiliza uma arquitetura enxuta baseada em Python para a engine cognitiva e Node.js como servidor de gateway.

---

## 🐍 Dependências Python (`requirements.txt`)

| Pacote | Versão Mínima | Uso no Projeto | Status |
| :--- | :--- | :--- | :--- |
| `python-dotenv` | `>=1.0.0` | Carregamento de variáveis de ambiente do `.env`. | **ATIVO** |
| `google-genai` | `>=1.0.0` | SDK oficial da Google Gemini API para embeddings e respostas. | **ATIVO** |
| `google-generativeai` | `>=0.8.0` | SDK legado/compatibilidade com a Gemini API. | **ATIVO** |
| `requests` | `>=2.31.0` | Requisições HTTP para busca web e fallbacks. | **ATIVO** |
| `openpyxl` | `>=3.1.0` | Leitura de planilhas de dados na ingestão. | **ATIVO** |
| `pypdf` | `>=4.0.0` | Parsing e extração de texto de documentos PDF. | **ATIVO** |
| `pandas` | `>=2.0.0` | Processamento tabular de datasets e métricas. | **ATIVO** |
| `PyYAML` | `>=6.0.0` | Leitura dos arquivos de configuração YAML (`embed_config.yml`). | **ATIVO** |
| `gTTS` | `>=2.5.0` | Síntese de voz para a interface de áudio. | **ATIVO** |

---

## 🟢 Dependências Node.js (`package.json`)

* **Node.js Runtime:** `>=18.0.0`
* **Dependências npm externas:** Nenhuma (utiliza apenas módulos nativos do Node.js: `http`, `fs`, `path`, `child_process`).

---

## 💡 Recomendações e Conclusão

1. As dependências encontram-se extremamente enxutas e sem vulnerabilidades conhecidas ou inchaço de pacotes.
2. Não há dependências duplicadas no Node.js.
