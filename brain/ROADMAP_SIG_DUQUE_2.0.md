# Arquitetura e Roadmap da Versão 2.0 — SIG Duque & IA Geoespacial

> **Documento de Arquitetura de Governança — SIG Duque 2.0**  
> **Data:** 2026-07-28 | **Sistema:** SIG Duque & DUQUE IA (Prefeitura de Duque de Caxias — RJ)

---

## 🏛️ 1. Visão Geral da Versão 2.0

O projeto **DUQUE IA** evoluiu de um assistente virtual conversacional base RAG para uma **Plataforma Integrada de Inteligência Territorial e Governança Municipal (SIG Duque)**.

A Versão 2.0 estabelece a **Modularização de Domínios**, separando o motor de Inteligência Artificial Conversacional do ecossistema de gestão governamental e introduzindo a camada de **GIS Geoespacial Completo**.

---

## 📐 2. Estrutura de Diretórios Proposta (`src/`)

```text
src/
├── ai/                         # Motor Cognitivo de IA Conversacional (RAG)
│   ├── agent/                  # Grafo de Estados, Memory e CLI Entrypoint
│   ├── retrieval/              # Retriever Híbrido e Scoring (SQL + Vetores 768d)
│   ├── guardrails/             # Guardrails Anti-alucinação, LGPD e Competência Municipal
│   └── llm/                    # Prompts, Cross-Encoder e LLM Router
│
├── sig_duque/                  # Ecossistema de Governança e Inteligência Municipal
│   ├── sync/                   # Pipeline Incremental de Sincronização do Colab
│   ├── ouvidoria/              # Agente Coletor e Gestão de Manifestações
│   ├── esic/                   # Atendimento à Lei de Acesso à Informação (LAI)
│   ├── indicadores/            # Métricas e Indicadores de Desempenho Por Secretaria
│   ├── dashboards/             # Servidor de Painéis Analíticos e Visualização
│   └── gis/                    # Módulo GIS Geoespacial Completo
│       ├── geojson/            # Polígonos de Distritos, Bairros e Setores Censitários
│       ├── geocoder/           # Geocodificação (Lat/Lng) via Nominatim / Google Maps
│       ├── spatial_queries/    # Consultas Espaciais SpatiaLite / PostGIS
│       └── heatmaps/           # Mapas de Calor de Demandas Urbanas por Raio (km)
│
├── integrations/               # Adaptadores de Serviços Externos (Adapter Pattern)
│   ├── gemini/                 # SDK e Embeddings da Google Gemini API
│   ├── groq/                   # Provedor Fallback Groq Llama 3
│   ├── colab/                  # Client de Sincronização API Colab
│   ├── mysql/                  # Conexão com Banco Relacional de Produção
│   ├── sqlite/                 # Conexão com Bases Locais em Modo WAL
│   └── whatsapp/               # Gateway de Integração com WhatsApp Municipal
│
└── services/                   # Camada de Serviços e Regras de Negócio
    ├── sync_service.py         # Sincronização Incremental Colab em ~2 segundos
    ├── retrieval_service.py    # Orquestrador do Pipeline de Busca RAG
    ├── embedding_service.py    # Gerenciador de Chunks e Embeddings
    ├── protocol_service.py     # Gestão de Protocolos da Ouvidoria
    ├── esic_service.py         # Serviços da LAI / e-SIC
    └── telemetry_service.py    # Telemetria de Desempenho e Latência de Nós
```

---

## ⚡ 3. Sincronização Incremental do Colab (`sync_service.py`)

Para eliminar o reprocessamento massivo de 31 mil protocolos históricos, a Versão 2.0 introduz o serviço de sincronização permanente:

```text
  Event-driven / Cron (Cada 5 min)
                │
                ▼
   POST /api/sync/colab
                │
                ▼
      [sync_service.py]  ──(Filtro por data/timestamp)──► Busca apenas novos protocolos
                │
                ▼
        [MySQL / SQLite] ──► [Dashboard & Embeddings Incrementais]
```

### Principais Benefícios:
1. **Tempo de Execução:** Atualização concluída em **~2 segundos**.
2. **Consumo de Banda e Custo:** Zero requisições redundantes de dados passados.
3. **Auditabilidade:** Registro de telemetria de sincronização com timestamp em `data/db/telemetry.db`.

---

## 🗺️ 4. Evolução do SIG Duque: Do SIG Semântico ao GIS Geoespacial

### A. Diagnóstico Atual (SIG Nível 1 — Semântico)
- Mapeamento por texto de distritos (1º ao 4º distrito) e bairros ([agent/entity_resolver.py](file:///c:/Users/501379.PMDC/Desktop/PRODUCAO/agent/entity_resolver.py)).
- Unidades físicas cadastradas na tabela `secretaria_unidades`.
- Resolução de intenção geográfica `QueryIntent.GIS`.

### B. Especificação da Versão 2.0 (GIS Nível 2/3 — Geoespacial Completo)
1. **Camada GeoJSON Operacional:** Importação dos arquivos de limites oficiais da Prefeitura de Duque de Caxias:
   - Polígonos dos 4 Distritos Administrativos.
   - Polígonos dos Bairros e Setores Censitários do IBGE.
2. **Spatial Database Engine (SpatiaLite / PostGIS):**
   - Suporte a geometrias `POINT`, `POLYGON`, `MULTIPOLYGON`.
   - Execução de funções espaciais nativas:
     - `ST_Contains(distrito_polygon, point)`: Valida se a demanda está dentro do distrito.
     - `ST_DWithin(location, target_point, distance)`: Retorna demandas em um raio específico de X metros/km.
3. **Geocodificação Automática (Lat/Lng):**
   - Transforma endereços informados pelos munícipes (ex: *"Rua Piratini, 123 - Jardim Primavera"*) em coordenadas geográficas `(Latitude, Longitude)`.
4. **Painel de Heatmaps e Densidade Urbana:**
   - Visualização no Dashboard de manchas de calor de demandas de tapa-buracos, troca de lâmpadas e vazamentos de água agregadas por bairro e por período (últimos 15, 30 e 90 dias).

---

## 📋 5. Matriz de Componentes Mestre do SIG Duque 2.0

| Domínio | Componente | Responsabilidade | Tecnologias |
| :--- | :--- | :--- | :--- |
| **`ai`** | Motor Conversacional | RAG Híbrido, Guardrails LGPD, Re-ranker | Python, Gemini API, SQLite Vector |
| **`sig_duque/sync`** | Sync Colab | Sincronização incremental em ~2s | Python, REST API, MySQL/SQLite |
| **`sig_duque/ouvidoria`**| Agente Coletor | Triagem conversacional e formulários | Python, Colab Protocol API |
| **`sig_duque/gis`** | SIG Geoespacial | GeoJSON, Geocodificação e Spatial SQL | SpatiaLite / PostGIS, Leaflet.js |
| **`integrations`** | Adaptadores de APIs | Comunicação isolada com Gemini, Groq, WhatsApp | Requests, HTTP Clients |
| **`services`** | Regras de Negócio | Lógica de sincronização, RAG e telemetria | Python Clean Services |

---

## 🚀 6. Conclusão

Com a Versão 2.0, o **SIG Duque** consolida-se como um produto municipal completo, unindo **IA Conversacional RAG**, **Inteligência Territorial GIS** e **Governança de Ouvidoria** em uma arquitetura modular de alto desempenho.
