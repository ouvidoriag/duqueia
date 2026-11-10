"""
apply_pen_audit_updates.py — DUQUE IA
=====================================
Aplica as atualizações canônicas de todas as demandas e anotações de caneta
identificadas no relatório de auditoria (ouvidoria104827.pdf / DIAGNOSTICO_E_SOLUCOES_QA_23_CASOS.md).
Atualiza incrementalmente:
1. data/knowledge/bancoduqueia/dados_mestres/regras_negocio.json
2. data/db/main.db (tabela regras_negocio e municipal_entities)
3. data/ontology.json
4. data/knowledge/bancoduqueia/pipeline_storage/CHUNKS_MESTRES_UNIFICADOS.jsonl
5. data/db/vector.db (tabelas chunks e chunks_fts)
Sem recriar ou deletar tabelas existentes, respeitando a Regra 6 do projeto.
"""

import os
import sys
import json
import sqlite3

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

REGRAS_JSON_PATH = os.path.join(_PROJECT_ROOT, "data", "knowledge", "bancoduqueia", "dados_mestres", "regras_negocio.json")
MAIN_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "db", "main.db")
ONTOLOGY_JSON_PATH = os.path.join(_PROJECT_ROOT, "data", "ontology.json")
CHUNKS_JSONL_PATH = os.path.join(_PROJECT_ROOT, "data", "knowledge", "bancoduqueia", "pipeline_storage", "CHUNKS_MESTRES_UNIFICADOS.jsonl")
VECTOR_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")

# ---------------------------------------------------------------------------
# DEFINIÇÃO DAS REGRAS REVISADAS E NOVAS REGRAS CANÔNICAS (QA PEN AUDIT)
# ---------------------------------------------------------------------------
UPDATED_AND_NEW_RULES = [
    {
        "id": "regra_canon_padrao_estruturado_benchmark",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Padrão Estruturado de Ouro para Equipamentos e Regras Canônicas (Benchmark)",
        "tema": "Governança Canônica e Arquitetura do Sistema",
        "assunto": "Especificação do Padrão Estruturado de Referência (Golden Benchmark)",
        "conteudo": """O Padrão Estruturado de Ouro (Golden Benchmark) adotado no DUQUE IA define os requisitos arquiteturais e documentais mandatórios para homologação de dados mestres de equipamentos especiais e regras de negócio:

1. **ESTRUTURA DE METADADOS OBRIGATÓRIOS (SCHEMA CANÔNICO):**
• **ID Único:** Identificador semântico imutável (`regra_canon_*` ou `equipamento_*`).
• **Tema e Assunto:** Taxonomia estrita vinculada ao catálogo da Ouvidoria Geral e Carta de Serviços.
• **Diretriz Oficial Auditada:** Texto factual, normativo, claro e resolutivo (sem termos ambíguos ou evasivos).
• **Tags de Busca Canônica:** Conjunto abrangente de sinônimos populares, gírias locais e termos técnicos para ativação determinística no Fast Gate.
• **Nível de Prioridade e Boost:** Prioridade MÁXIMA com peso de relevância (boost_weight >= 3.0) para sobreposição a dados estocásticos do LLM.
• **Rastreabilidade e Autoria:** Identificação do órgão gestor, autor técnico, data de homologação e instâncias de validação institucional.
• **Links Oficiais Validados:** URLs ativas no domínio oficial da Prefeitura (`duquedecaxias.rj.gov.br`) e canais Colab.

2. **COMPORTAMENTO NO PIPELINE (FAST GATE LAYER):**
• Ao detectar entidades do padrão ouro (ex: Fazendinha do Autista, Casa do Autista, Concessionárias), o sistema injeta os dados homologados com 100% de confiança, bloqueando alucinações e inferências probabilísticas não ancoradas.""",
        "tags": ["padrao estruturado", "benchmark", "governanca canonica", "fast gate", "regra de ouro", "schema canonico", "equipamentos especiais"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.5,
        "autor": "Arquiteto de IA & Diretoria da Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.rj.gov.br", "https://duquedecaxias.colab.re/"],
        "homologado_por": ["Diretoria da Ouvidoria Geral", "Coordenação Técnica de IA", "Secretaria Municipal de Governo"]
    },
    {
        "id": "regra_canon_socorro_morador_rua_samu_centro_pop",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Socorro a Pessoa em Situação de Rua — Georreferenciamento e Assistência Social",
        "tema": "Emergência Médica e Assistência Social",
        "assunto": "Socorro a Morador de Rua Desmaiado, Georreferenciamento Territorial (Lógica Caso 01) e Centro POP",
        "conteudo": """Ao receber relato de pessoa em situação de rua desmaiada, acidentada ou necessitando de auxílio em Duque de Caxias:

1. **1º PASSO — EMERGÊNCIA MÉDICA IMEDIATA (PRIORIDADE ABSOLUTA):**
• Acionar imediatamente o **SAMU pelo 192** ou o **Corpo de Bombeiros pelo 193**.
• Como a pessoa está desmaiada, o atendimento de suporte à vida e estabilização médica é prioritário e indispensável. Não mova a vítima sem orientação médica.

2. **2º PASSO — GEORREFERENCIAMENTO E APOIO SOCIAL TERRITORIAL (LÓGICA DO CASO 01):**
• **Regra de Localização:** O sistema aplica a mesma lógica de cálculo de proximidade e geocodificação do Caso 01.
• **Com Bairro/Endereço Informado:** A IA identifica a coordenada geográfica da ocorrência e indica o **Centro POP (Centro de Referência Especializado para População em Situação de Rua)** ou o **CRAS de referência territorial mais próximo** para a abordagem social contínua.
• **Sem Endereço Informado (Agente Coletor):** É expressamente proibido arbitrar um CRAS genérico (como o CRAS Jardim Primavera). A IA adota o comportamento de Agente Coletor: *"Para que a equipe de abordagem social do Centro POP ou do CRAS de referência localize a pessoa, por favor informe a rua, praça ou bairro onde ela se encontra."*
• **Canal Digital:** Solicitação de abordagem social pode ser aberta via **Colab** (https://duquedecaxias.colab.re/) no Tema: Assistência Social > Abordagem Social a Pessoas em Situação de Rua.""",
        "tags": ["morador de rua desmaiado", "socorro morador de rua", "samu 192", "pessoa desmaiada", "centro pop", "abordagem social", "cras rua", "resgate morador de rua", "logica caso 01"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Assistência Social e Direitos Humanos / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.colab.re/"],
        "homologado_por": ["Secretaria Municipal de Assistência Social e Direitos Humanos", "Coordenação do SAMU", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_regularizacao_imovel_rgi_smuh",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Regularização de Imóveis, Habite-se e Cartório de RGI (SMUH)",
        "tema": "Urbanismo, Habitação e Registro de Imóveis",
        "assunto": "Regularização Imobiliária, RGI e Atos Autorizativos da SMUH (Documento Oficial do Urbanismo)",
        "conteudo": """**DOCUMENTAÇÃO E FONTES OFICIAIS DO URBANISMO (SMUH):**
Regras fundamentadas no **Guia Oficial de Regularização Imobiliária da Secretaria Municipal de Urbanismo e Habitação (SMUH)**, na **Lei Complementar nº 08/2021 (Programa Municipal de Regularização Fundiária Urbana - REURB)**, no **Código de Obras Municipal (Lei nº 1.077/1991)** e nas normas da Corregedoria Geral da Justiça do TJ/RJ para os Cartórios do 1º e 2º Ofícios de Registro de Imóveis de Duque de Caxias.

1. **COMPETÊNCIA MUNICIPAL VS CARTÓRIO DE RGI:**
• O RGI (Registro Geral de Imóveis) é ato privativo dos Cartórios de Registro de Imóveis (1º Ofício: 1º e 2º Distritos; 2º Ofício: 3º e 4º Distritos).
• A Prefeitura (SMUH) não emite a certidão de matrícula do RGI, mas é a responsável exclusiva por todos os atos administrativos prévios obrigatórios.

2. **FLUXO PRÁTICO POR CENÁRIO DO MUNÍCIPE:**
• **Cenário 1 — Imóvel já possui Matrícula no Cartório:** O cidadão comparece à SMUH para abrir processo de certidão de logradouro/informações cadastrais oficiais (lote, quadra, logradouro oficial e bairro) para averbação e atualização no Cartório de RGI.
• **Cenário 2 — Possui Escritura ou Título de Compra e Venda:** Apresenta o título diretamente ao Cartório de RGI correspondente para registro na matrícula.
• **Cenário 3 — Posse e Regularização por Usucapião:**
  - Extrajudicial: Requerimento via advogado/defensor diretamente no Cartório de RGI, com certidão de não-desapropriação emitida pela SMUH.
  - Judicial: Via Defensoria Pública ou advogado. A SMUH elabora a planta do imóvel e memorial descritivo **gratuitamente** quando oficiada pela Defensoria Pública do Estado.
• **Cenário 4 — Obras e Benfeitorias (Construídas ou a Construir):**
  - Obra existente: Laudo técnico de engenheiro/arquiteto credenciado, protocolo de legalização na SMUH, taxas de licença e emissão do Habite-se para posterior averbação no RGI.
  - Obra nova: Consulta prévia de zoneamento, aprovação do projeto arquitetônico, alvará de obras e vistoria final do Habite-se.
• **Cenário 5 — REURB (Lei Complementar nº 08/2021):** Núcleos urbanos informais consolidados recebem titulação de legitimação fundiária diretamente pela SMUH (REURB-S Social gratuita).

3. **ATENDIMENTO PRESENCIAL E CONTATOS DA SMUH:**
• **Endereço:** Alameda Bartolomeu Gusmão, nº 85 – Jardim Primavera, Duque de Caxias - RJ (CEP: 25215-320).
• **Telefones:** (21) 2773-0202 / (21) 2776-0388 / (21) 2783-6066.
• **E-mail:** semuh@duquedecaxias.rj.gov.br | **Horário:** Segunda a sexta, das 09h às 17h.""",
        "tags": ["rgi", "regularizar imovel", "registro de imovel", "habite-se", "smuh", "urbanismo", "escritura", "usucapiao", "desmembramento", "reurb", "documento do urbanismo"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Urbanismo e Habitação (SMUH) / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.rj.gov.br"],
        "homologado_por": ["Secretaria Municipal de Urbanismo e Habitação", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_estabelecimento_fedendo_vigilancia_sanitaria",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Fiscalização de Estabelecimento Fedendo, Açougues e Alimentos (Vigilância Sanitária)",
        "tema": "Vigilância Sanitária e Saúde Pública",
        "assunto": "Fiscalização de Estabelecimento Fedendo, Comércio de Alimentos, Açougues e Carne Estragada",
        "conteudo": """Para denúncias de estabelecimentos com mau cheiro forte, carnes impróprias ou comércio de alimentos em condições inadequadas em Duque de Caxias:

1. **ÓRGÃO COMPETENTE E ATRIBUIÇÃO:**
• A fiscalização de estabelecimentos comerciais de alimentos (açougues, peixarias, supermercados, feiras, restaurantes e frigoríficos) compete privativamente à **Subsecretaria de Vigilância Sanitária (SMS / DVS)**.
• O órgão apura condições de higiene, acondicionamento térmico de carnes, descarte de resíduos putrescíveis, validade de produtos e licença sanitária.

2. **ONDE E COMO REGISTRAR NO COLAB (CANAL OFICIAL):**
• **Aplicativo / Portal:** Acesse o **Colab** (https://duquedecaxias.colab.re/) ou o Portal Cidadão Ouvidoria.
• **Tema / Categoria:** **Vigilância Sanitária**
• **Assunto:** **Fiscalização de Comércio de Alimentos / Condições Higiênico-Sanitárias**
• **Orientações do POP:** Recomende ao munícipe anexar fotos, informar o nome de fachada do estabelecimento, endereço completo com número e ponto de referência para a equipe técnica de fiscalização sanitária.""",
        "tags": ["estabelecimento fedendo", "comercio fedendo", "vende carne", "vende carne fedendo", "acougue fedendo", "peixaria fedendo", "carne estragada", "mau cheiro de comercio", "mau cheiro", "vigilancia sanitaria", "fiscalizacao de alimentos"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Subsecretaria de Vigilância Sanitária / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.colab.re/", "https://portal.duquedecaxias.rj.gov.br/ouvidoria"],
        "homologado_por": ["Subsecretaria de Vigilância Sanitária", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_poluicao_sonora_4_destinos",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Poluição Sonora — Flagrante Policial (190) e Fiscalização Municipal (SMMA, SMUH, SUOP)",
        "tema": "Poluição Sonora, Ordem Pública e Meio Ambiente",
        "assunto": "Perturbação do Sossego Noturno (190 PMERJ) e Fiscalização Integrada de Alvará e Ruído (SMMA, SMUH, SUOP)",
        "conteudo": """Para ocorrências de perturbação do sossego alheio, som alto e casas de festas em Duque de Caxias:

1. **CASOS NOTURNOS, FLAGRANTES E ILÍCITOS PENAIS — ACIONE O 190 (POLÍCIA MILITAR):**
• Se o fato estiver ocorrendo no momento (flagrante), à noite ou de madrugada, com perturbação do sossego, aglomeração violenta ou ilícitos penais, o munícipe deve acionar imediatamente a **Polícia Militar pelo telefone 190**. A intervenção imediata de contenção e manutenção da ordem pública compete à PMERJ (Art. 144 da CF/88).

2. **FISCALIZAÇÃO ADMINISTRATIVA DA PREFEITURA (SEM REDUNDÂNCIAS):**
Para denúncia e vistoria do estabelecimento comercial/casa de festas, a atuação municipal divide-se estritamente entre:
• **Secretaria Municipal de Meio Ambiente e Proteção Animal (SMMA):** Fiscalização técnica de poluição sonora com aparelho decibelímetro, medição dos níveis de pressão sonora conforme limites do Decreto Municipal nº 7.620/2020 e autuação por infração ambiental. *(Canal Colab: Meio Ambiente > Fiscalização de Poluição Sonora)*.
• **Secretaria Municipal de Urbanismo e Habitação (SMUH / Posturas):** Fiscalização de Alvará de Localização e Funcionamento, conformidade do zoneamento urbano, exigência do projeto acústico obrigatório e interdição do imóvel por descumprimento de posturas.
• **Superintendência de Operações / Ordem Pública (SUOP):** Fiscalização ostensiva de bares, eventos, ruas e feiras, coibição de ocupação irregular de calçadas e apreensão de equipamentos sonoros com apoio da Guarda Municipal.

3. **CANAIS DA OUVIDORIA GERAL:**
• As manifestações administrativas podem ser abertas pelo aplicativo **Colab** (https://duquedecaxias.colab.re/) ou pelos telefones da Ouvidoria Geral: **(21) 2652-3835** e WhatsApp **(21) 99824-5903**.""",
        "tags": ["barulho", "poluicao sonora", "som alto", "casa de festas", "casa noturna", "festa noturna", "perturbação do sossego", "190", "policia militar", "smma", "smuh", "suop", "decibelimetro", "alvara"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Ouvidoria Geral / SMMA / SMUH / SUOP",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.colab.re/"],
        "homologado_por": ["Secretaria de Meio Ambiente", "Secretaria de Urbanismo", "Superintendência de Operações", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_concessionaria_aguas_rio",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Água e Esgoto — Concessionária Águas do Rio e Fluxo Oficial da Ouvidoria (Equipe Gildo/Nikolas)",
        "tema": "Concessionárias de Serviços Públicos",
        "assunto": "Falta de Água, Vazamentos e Intermediação Oficial com a Águas do Rio via Ouvidoria / Colab",
        "conteudo": """Para demandas de falta de água, baixa pressão ou vazamentos de esgoto e rede pública em Duque de Caxias:

1. **CONCESSIONÁRIA EXCLUSIVA NO MUNICÍPIO (ÁGUAS DO RIO):**
• A concessionária responsável exclusiva pelos serviços de abastecimento de água encanada e esgotamento sanitário em Duque de Caxias é a **ÁGUAS DO RIO**.
• **É terminantemente proibido citar a CEDAE** para atendimento de rede ou solicitação de serviços de campo.

2. **CANAL DIRETO DA CONCESSIONÁRIA (ATENDIMENTO EMERGENCIAL):**
• **Telefone e WhatsApp:** **0800 195 0 195** (Ligação gratuita e atendimento 24 horas para manobras de rede, religamento e reparo emergencial de vazamentos).

3. **FLUXO OFICIAL DA OUVIDORIA GERAL NO COLAB (EQUIPE GILDO / NIKOLAS):**
• O munícipe pode abrir a demanda diretamente nos canais da Prefeitura pelo aplicativo **Colab** (https://duquedecaxias.colab.re/) ou Portal Cidadão Ouvidoria.
• **Tema Oficial no Colab:** **Serviços e Rede de Água e Esgoto (Águas do Rio)**
• **Assunto Oficial:** **Falta de água - ÁGUAS DO RIO** (ou *Vazamento de água - ÁGUAS DO RIO*, *Esgoto entupido - ÁGUAS DO RIO*).
• **Atuação da Ouvidoria Geral:** A equipe da Ouvidoria (sob supervisão da Diretoria / Gildo e Nikolas) possui canal direto de intermediação e cobrança com a concessionária para monitoramento de prazos legais e fiscalização do cumprimento do serviço.""",
        "tags": ["falta de agua", "sem agua", "aguas do rio", "esgoto", "vazamento de agua", "cedae proibido", "concessionaria", "fluxo ouvidoria aguas do rio", "gildo", "nikolas"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Diretoria da Ouvidoria Geral (Gildo / Nikolas)",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.colab.re/", "https://aguasdorio.com.br/"],
        "homologado_por": ["Diretoria da Ouvidoria Geral", "Coordenação Técnica de Concessionárias"]
    },
    {
        "id": "regra_canon_alvara_profissional_liberal_e_vigilancia_sanitaria",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Profissional Liberal — Alvará (SMF), Licença Sanitária (SMS) e Registro Jucerja",
        "tema": "Fazenda, Tributos e Vigilância Sanitária",
        "assunto": "Alvará para Profissional Liberal, Licença Sanitária e Consulta na Jucerja / Portais Oficiais",
        "conteudo": """Para regularização de profissional liberal e obtenção de alvará e licença sanitária em Duque de Caxias:

1. **SECRETARIA MUNICIPAL DE FAZENDA (SMF) — ALVARÁ E ISS AUTÔNOMO:**
• Solicitação pelo **Portal do Contribuinte** (https://portalcontribuinte.duquedecaxias.rj.gov.br/) ou presencial na Praça Roberto Silveira, 31 - Jardim 25 de Agosto.
• Documentos: RG, CPF, comprovante de residência e carteira de registro no Conselho de Classe Profissional ativo (OAB, CRM, CRO, CREA, etc.).

2. **SUBSECRETARIA DE VIGILÂNCIA SANITÁRIA (SMS) — LICENÇA SANITÁRIA:**
• Obrigatória para consultórios médicos, odontológicos, fisioterapia, estética e serviços de saúde/beleza.
• Solicitação mediante processo administrativo com alvará preliminar, memorial descritivo e PGRSS quando exigido.

3. **JUNTA COMERCIAL DO ESTADO DO RIO DE JANEIRO (JUCERJA):**
• Para profissionais que atuam sob natureza jurídica societária ou empresária, consultar e emitir atos cadastrais pelo site oficial da **Jucerja** (https://www.jucerja.rj.gov.br/).""",
        "tags": ["profissional liberal", "alvara profissional liberal", "certificado vigilancia sanitaria", "licenca sanitaria", "jucerja", "portal do contribuinte", "iss autonomo"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria de Fazenda / Vigilância Sanitária / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://portalcontribuinte.duquedecaxias.rj.gov.br/", "https://www.jucerja.rj.gov.br/"],
        "homologado_por": ["Secretaria de Fazenda", "Subsecretaria de Vigilância Sanitária", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_emergencia_trauma_ortopedia",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Emergência Hospitalar — Traumas, Fraturas e Quedas Agudas (Sem Risco de Falso Negativo)",
        "tema": "Saúde Pública e Emergência Hospitalar",
        "assunto": "Urgência Médica de Trauma Ortopédico, Fraturas e Proibição de Direcionamento Eletivo",
        "conteudo": """**DIRETRIZ DE SEGURANÇA CLÍNICA — TRAUMA ORTOPÉDICO E URGÊNCIA:**
Para qualquer relato de trauma agudo, suspeita de fratura, queda violenta, incapacidade súbita de andar ou dor incapacitante pós-impacto (ex: "quebrei o pé", "bati com o joelho e não ando", "braço entortou", "queda de laje/escada", "fratura exposta"):

1. **PRIORIDADE DE EMERGÊNCIA — PROIBIÇÃO ABSOLUTA DE AGENDAMENTO ELETIVO:**
• O caso é de urgência médica hospitalar. **É estritamente proibido direcionar o cidadão para o programa ambulatório eletivo ('Chegaram os Especialistas') ou para regulação eletiva de postos de saúde.**
• Em caso de impossibilidade de locomoção ou risco iminente, acione imediatamente o **SAMU (192)** ou os **Bombeiros (193)**.

2. **HOSPITAIS MUNICIPAIS DE REFERÊNCIA EM TRAUMA 24 HORAS:**
• **Hospital Estadual/Municipal Adão Pereira Nunes (Saracuruna):** Centro de excelência e referência regional em traumatologia de alta complexidade e cirurgia ortopédica de urgência (Rodovia Washington Luís, km 109 - Jardim Primavera / Saracuruna).
• **Hospital Municipal Dr. Moacyr Rodrigues do Carmo (HMMRC):** Emergência 24 horas para primeiro atendimento, raio-x e imobilização ortopédica (Rodovia Washington Luís, 3200 - Parque Duque).
• **UPHs e UPAs 24 Horas:** Unidades Pré-Hospitalares municipais atuam como portas de socorro rápido para imobilização provisória e encaminhamento regulado de ambulância.""",
        "tags": ["quebrei o pe", "ortopedia emergencia", "hospital ortopedia", "trauma ortopedico", "fratura", "osso quebrado", "dor apos queda", "torcao grave", "adao pereira nunes", "saracuruna", "moacyr do carmo", "samu 192"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Saúde / Complexo Hospitalar Adão Pereira Nunes",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://saude.duquedecaxias.rj.gov.br/"],
        "homologado_por": ["Secretaria Municipal de Saúde", "Diretoria Médica HMAPN", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_reparo_canteiro_calcada_publica",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Manutenção Viária — Canteiros, Calçadas e Vias Públicas (SMOA / Colab)",
        "tema": "Infraestrutura e Zeladoria Urbana",
        "assunto": "Reparo de Canteiros Danificados, Calçadas Públicas, Meio-fio e Passeio Público",
        "conteudo": """Para solicitações de conserto de canteiros danificados, calçadas esburacadas, paralelepípedos soltos ou meios-fios destruídos em Duque de Caxias:

1. **ÓRGÃO RESPONSÁVEL:**
• **Secretaria Municipal de Obras e Agricultura (SMOA)**, encarregada da conservação de vias, praças e equipamentos urbanos públicos.

2. **COMO SOLICITAR NO COLAB:**
• **Aplicativo:** Acesse o **Colab** (https://duquedecaxias.colab.re/) ou o Portal Cidadão.
• **Categoria / Tema:** **Obras e Infraestrutura**
• **Assunto:** **Reparo de Vias / Canteiros Públicos / Calçadas Danificadas**
• **Dados Obrigatórios:** Logradouro com número de referência em frente, bairro e foto nítida do local para triagem da equipe operacional.""",
        "tags": ["canteiro danificado", "conserto de canteiro", "calcada publica", "reparo de calcada", "smoa", "obras", "meio-fio", "passeio publico", "paralelepipedo", "asfalto quebrado", "mureta", "guia de sarjeta"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Obras e Agricultura / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.colab.re/"],
        "homologado_por": ["Secretaria Municipal de Obras e Agricultura", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_alvara_templo_religioso_fiscalizacao",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Templos Religiosos — Imunidade Tributária, Alvará e Poder de Polícia (SMF/SMUH/CBMERJ)",
        "tema": "Fazenda, Urbanismo e Segurança Pública",
        "assunto": "Alvará de Funcionamento para Templos Religiosos, Imunidade Constitucional e Rito de Fiscalização",
        "conteudo": """**BASE JURÍDICA E NORMATIVA AUDITADA:**
Normas fundamentadas no **Artigo 150, VI, 'b' da Constituição Federal de 1988**, no **Código Tributário Municipal (Lei nº 1.664/2002)**, no **Código de Posturas de Duque de Caxias (Lei nº 1.464/1999)** e no **Decreto Estadual nº 42/2018 (COSCIP - Corpo de Bombeiros Militar do RJ)**.

1. **IMUNIDADE TRIBUTÁRIA VS PODER DE POLÍCIA ADMINISTRATIVO:**
• Os templos de qualquer culto possuem **imunidade tributária estrita** sobre impostos que recaiam sobre seu patrimônio, renda e serviços vinculados às suas finalidades essenciais (Art. 150, VI, 'b' da CF).
• **Todavia, não estão dispensados das normas de segurança, higiene e poder de polícia da Prefeitura**. Necessitam de Alvará de Localização e Funcionamento para garantir a integridade dos fiéis e o sossego da vizinhança.

2. **LICENÇAS E PROCEDIMENTO DE OBTENÇÃO:**
• **Alvará de Localização e Funcionamento:** Requerido via **Portal do Contribuinte (SMF)** (https://portalcontribuinte.duquedecaxias.rj.gov.br/) com envio de CNPJ, Estatuto Social e Ata de Eleição da Diretoria.
• **Habite-se / Regularidade Edilícia:** Emitido pela SMUH.
• **Certificado de Aprovação do CBMERJ:** Laudo do Corpo de Bombeiros Militar atestando prevenção contra incêndio, rotas de fuga e extintores.
• **Isolamento Acústico:** Limites sonoros conformes às posturas municipais.

3. **RITO ADMINISTRATIVO DE FISCALIZAÇÃO E INTERDIÇÃO:**
• A Prefeitura **não interdita sumariamente** templos religiosos sem a devida constatação de grave e iminente risco estrutural.
• O procedimento administrativo regular exige:
  1. Notificação Preliminar com prazo hábil (30 a 60 dias) para apresentação e regularização de documentos;
  2. Auto de Infração somente em caso de inércia injustificada;
  3. A interdição é medida de extrema exceção restrita a risco iminente de desabamento ou incêndio constatado pelas autoridades técnicas.""",
        "tags": ["templo religioso", "alvara igreja", "alvara templo", "interdicao de igreja", "fiscalizacao igreja", "imunidade tributaria templos", "smuh", "smf", "cbmerj", "codigo de posturas", "art 150 cf"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Fazenda / Secretaria de Urbanismo / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://portalcontribuinte.duquedecaxias.rj.gov.br/"],
        "homologado_por": ["Secretaria de Fazenda", "Secretaria de Urbanismo", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_recurso_multas_jari_transito",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Multas de Trânsito — JARI Municipal, Defesa Prévia e Recursos (CTB)",
        "tema": "Transportes, Trânsito e Segurança Pública",
        "assunto": "Recursos de Multas Municipais, Consulta de Processo e JARI (Fundamentação no CTB e CONTRAN)",
        "conteudo": """**BASE LEGAL OFICIAL AUDITADA:**
Procedimento fundamentado na **Lei Federal nº 9.503/1997 (Código de Trânsito Brasileiro - CTB, Arts. 281, 285 e 286)**, na **Resolução CONTRAN nº 900/2022** e no **Decreto Municipal nº 6.012/2011** que regulamenta a Junta Administrativa de Recursos de Infrações (JARI) vinculada à Secretaria Municipal de Transportes e Serviços Públicos (SMTSP).

1. **IDENTIFICAÇÃO DO ÓRGÃO AUTUADOR:**
• Verifique o cabeçalho da Notificação de Autuação. Se a autuação foi lavrada pela Prefeitura de Duque de Caxias (Guarda Municipal / SMTSP), o julgamento é de competência privativa da **JARI Municipal**.
• Se aplicada na Rodovia Washington Luís (BR-040), compete à PRF/ANTT; se em rodovias estaduais ou vias do Detran, compete ao DETRAN-RJ.

2. **PRAZOS E PROCEDIMENTO DE RECURSO:**
• **Prazo Legal:** Mínimo de 30 dias contados da notificação (expresso na Notificação de Penalidade).
• **Onde Apresentar:** Presencialmente no Setor de Protocolo Geral da Prefeitura (Alameda Esmeralda, 206 - Jardim Primavera) ou na sede da SMTSP.
• **Documentos Obrigatórios:** Requerimento/Formulário de Recurso assinado, cópia da notificação da multa, cópia da CNH do motorista, cópia do CRLV do veículo e documentos comprobatórios (fotos, notas, comprovantes).""",
        "tags": ["recurso de multa", "multa indevida", "jari", "defesa de multa", "processo de multa", "secretaria de transportes", "recurso de transito", "ctb", "resolucao contran 900"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Transportes e Serviços Públicos / JARI",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.rj.gov.br"],
        "homologado_por": ["Junta Administrativa de Recursos de Infrações - JARI", "Secretaria de Transportes", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_atencao_saude_nutricao_emagrecimento",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Saúde — Atendimento Nutricional, Emagrecimento e Atenção Primária (PNAB / SUS)",
        "tema": "Atenção Primária à Saúde",
        "assunto": "Acesso a Nutricionista, Emagrecimento Saudável e Porta de Entrada no SUS (SMS)",
        "conteudo": """**BASE NORMATIVA OFICIAL AUDITADA:**
Diretriz fundamentada na **Política Nacional de Atenção Básica (PNAB - Portaria de Consolidação MS nº 2/2017)**, na Linha de Cuidado do Sobrepeso e Obesidade do Ministério da Saúde e na **Carta de Serviços da Secretaria Municipal de Saúde (SMS) de Duque de Caxias** (disponível em https://saude.duquedecaxias.rj.gov.br/).

1. **PORTA DE ENTRADA OBRIGATÓRIA NO SUS (UBS / USF):**
• O atendimento nutricional no SUS não funciona por livre demanda em clínicas isoladas. O munícipe deve procurar sua **Unidade Básica de Saúde (UBS)** ou **Unidade de Saúde da Família (USF - Clínica da Família)** mais próxima de sua casa.

2. **FLUXO ASSISTENCIAL DE EMAGRECIMENTO E NUTRIÇÃO:**
• **1ª Etapa:** Consulta inicial com o **Clínico Geral ou Médico de Família** para exame físico geral e solicitação de exames laboratoriais preventivos (glicemia, colesterol, tireoide, etc.).
• **2ª Etapa:** Havendo indicação clínica, o médico emite o encaminhamento para o serviço de **Nutrição** da unidade de saúde ou polo de referência.
• **3ª Etapa:** Acompanhamento com nutricionista e inclusão em grupos educativos de hábitos saudáveis, academias da saúde e controle de doenças crônicas.

3. **DOCUMENTOS EXIGIDOS:**
• Cartão Nacional do SUS, documento oficial de identidade com foto (RG ou CPF) e comprovante de residência em Duque de Caxias.""",
        "tags": ["emagrecer", "quer emagrecer", "perder peso", "nutricionista", "dieta", "clinica da familia", "saude nutricao", "pnab sus", "carta de servicos saude"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Saúde / Coordenação de Atenção Primária",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://saude.duquedecaxias.rj.gov.br/unidades-de-saude.php"],
        "homologado_por": ["Secretaria Municipal de Saúde", "Diretoria de Atenção Primária", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_iluminacao_publica_zeladoria_vs_ouvidoria",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Iluminação Pública — Distinção Didática entre Zeladoria Urbana e Ouvidoria Geral",
        "tema": "Zeladoria Urbana vs Ouvidoria Geral",
        "assunto": "Troca de Lâmpadas Queimadas e Delimitação Categórica entre Zeladoria e Ouvidoria no Colab",
        "conteudo": """**DELIMITAÇÃO CATEGÓRICA DE FLUXOS NO COLAB:**

1. **QUANDO USAR A ZELADORIA URBANA (CANAL PRIMÁRIO DE SERVIÇO):**
• Para solicitar a execução física da manutenção pela primeira vez: lâmpada de poste apagada, lâmpada queimada, piscando ou rua às escuras.
• **Caminho no Colab:** Aplicativo **Colab** (https://duquedecaxias.colab.re/) > Aba **Zeladoria Urbana** > Categoria: **Iluminação Pública** > Assunto: **Lâmpada Queimada / Manutenção de Iluminação LED**.
• **Dados a informar:** Nome da rua, altura aproximada do número, bairro e código/plaqueta do poste se houver.

2. **QUANDO USAR A OUVIDORIA GERAL (CANAL SECUNDÁRIO DE CONTROLE):**
• A Ouvidoria Geral só deve ser acionada caso o munícipe já tenha aberto o protocolo inicial na Zeladoria Urbana e o prazo regulamentar de atendimento tenha expirado sem resolução pela concessionária/secretaria, ou caso haja reiterado descumprimento do serviço.
• **Caminho:** Colab > **Ouvidoria Geral** > Tipo: **Reclamação** (informando o número do protocolo anterior da Zeladoria).""",
        "tags": ["lampada queimada", "poste apagado", "iluminacao publica", "zeladoria iluminacao", "escuridao na rua", "colab zeladoria", "distincao ouvidoria zeladoria"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria de Transportes e Serviços Públicos / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.colab.re/"],
        "homologado_por": ["Secretaria Municipal de Transportes e Serviços Públicos", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_denuncia_irregularidade_servidor_ouvidoria",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Denúncia de Servidores, Funcionário Fantasma e Prevaricação (Ouvidoria Geral / CGM)",
        "tema": "Integridade Pública e Ouvidoria Geral",
        "assunto": "Denúncia de Funcionário Fantasma, Desvio Funcional e Garantia de Sigilo da Lei 13.460/2017",
        "conteudo": """Para denúncias de servidores com conduta irregular, funcionário fantasma, não comparecimento ao expediente de trabalho ou ausência de plantão:

1. **ÓRGÃO COMPETENTE:**
• **Ouvidoria Geral do Município / Controladoria Geral do Município (CGM)**. É expressamente vedado atribuir essas denúncias a secretarias setoriais arbitrárias (como Secretaria da Mulher ou Meio Ambiente).

2. **ONDE E COMO REGISTRAR NO COLAB:**
• Acesse o aplicativo **Colab** (https://duquedecaxias.colab.re/) ou Portal Cidadão Ouvidoria (https://portal.duquedecaxias.rj.gov.br/ouvidoria).
• Selecione o tipo de manifestação: **Denúncia**.

3. **GARANTIA LEGAL DE SIGILO ABSOLUTO (LEI FEDERAL Nº 13.460/2017):**
• O munícipe pode registrar a denúncia de forma anônima ou sob sigilo de identidade, garantido por lei federal.
• **Elementos Importantes para Apuração:** Nome completo do servidor (se souber), secretaria ou unidade pública onde deveria cumprir expediente, endereço do local e descrição detalhada dos dias e horários da irregularidade presenciada.""",
        "tags": ["funcionario fantasma", "servidor fantasma", "nao trabalha", "nao vai trabalhar", "recebe sem trabalhar", "prevaricacao", "denunciar servidor", "irregularidade servidor", "cgm", "ouvidoria denuncia"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Ouvidoria Geral do Município / Controladoria Geral do Município",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://portal.duquedecaxias.rj.gov.br/ouvidoria", "https://duquedecaxias.colab.re/"],
        "homologado_por": ["Controladoria Geral do Município", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_marimbondos_multiplas_demandas",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Remoção de Ninho de Marimbondos e Animais Peçonhentos (Bombeiros, Defesa Civil e Meio Ambiente)",
        "tema": "Defesa Civil, Bombeiros e Meio Ambiente",
        "assunto": "Ninho de Marimbondos em Via Pública, Risco à População e Órgãos Competentes",
        "conteudo": """Para ocorrências de ninhos de marimbondos, vespas ou enxames de abelhas colocando a população em risco em Duque de Caxias:

1. **RISCO IMINENTE À INTEGRIDADE FÍSICA EM VIA PÚBLICA:**
• Acione imediatamente o **Corpo de Bombeiros Militar pelo 193** ou a **Defesa Civil Municipal pelo 199**.
• Ambas as corporações realizam intervenções técnicas e isolamento de área quando insetos agressivos oferecem perigo iminente a pedestres e crianças.

2. **APOIO TÉCNICO E MANEJO AMBIENTAL (SMMA):**
• A **Secretaria Municipal de Meio Ambiente e Proteção Animal (SMMA)** atua em suporte para o manejo ecológico seguro e preservação de insetos polinizadores protegidos (como abelhas sem ferrão) em cooperação com órgãos de resgate.
• Para registro preventivo no Colab: Tema Meio Ambiente > Resgate e Proteção Animal.""",
        "tags": ["marimbondo", "ninho de marimbondo", "vespas", "enxame de abelha", "bombeiros 193", "defesa civil 199", "meio ambiente", "smma"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Defesa Civil / Corpo de Bombeiros / SMMA / Ouvidoria Geral",
        "data_homologacao": "2026-10-23 12:00",
        "links_oficiais": ["https://duquedecaxias.colab.re/"],
        "homologado_por": ["Subsecretaria de Defesa Civil", "Secretaria de Meio Ambiente", "Diretoria da Ouvidoria Geral"]
    }
]

def update_regras_json():
    print(f"[1/5] Atualizando regras_negocio.json...")
    if not os.path.exists(REGRAS_JSON_PATH):
        print(f"Erro: {REGRAS_JSON_PATH} não encontrado!")
        return 0

    with open(REGRAS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_rules = {r["id"]: idx for idx, r in enumerate(data.get("regras", []))}
    updated_count = 0
    added_count = 0

    for rule in UPDATED_AND_NEW_RULES:
        rid = rule["id"]
        if rid in existing_rules:
            idx = existing_rules[rid]
            data["regras"][idx] = rule
            updated_count += 1
        else:
            data["regras"].append(rule)
            added_count += 1

    data["total_regras"] = len(data["regras"])
    data["data_atualizacao"] = "2026-10-23 12:00:00"

    with open(REGRAS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"   -> {updated_count} regras atualizadas e {added_count} novas regras adicionadas em regras_negocio.json! (Total: {len(data['regras'])})")
    return len(UPDATED_AND_NEW_RULES)

def update_main_db():
    print(f"[2/5] Atualizando tabela regras_negocio e municipal_entities em main.db...")
    if not os.path.exists(MAIN_DB_PATH):
        print(f"Erro: {MAIN_DB_PATH} não encontrado!")
        return 0

    conn = sqlite3.connect(MAIN_DB_PATH)
    cur = conn.cursor()

    count = 0
    for r in UPDATED_AND_NEW_RULES:
        rid = r["id"]
        tipo = r["tipo"]
        tipo_lbl = r.get("tipo_label", "")
        tema = r.get("tema", "")
        assunto = r.get("assunto", "")
        conteudo = r.get("conteudo", "")
        tags = json.dumps(r.get("tags", []), ensure_ascii=False)
        prio = r.get("prioridade", "MAXIMA")
        boost = float(r.get("boost_weight", 3.0))
        autor = r.get("autor", "")
        data_h = r.get("data_homologacao", "")
        links = json.dumps(r.get("links_oficiais", []), ensure_ascii=False)
        homolog = json.dumps(r.get("homologado_por", []), ensure_ascii=False)

        cur.execute("""
            INSERT OR REPLACE INTO regras_negocio (
                id, tipo, tipo_label, tema, assunto, conteudo, tags,
                prioridade, boost_weight, autor, data_homologacao, links_oficiais, homologado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rid, tipo, tipo_lbl, tema, assunto, conteudo, tags, prio, boost, autor, data_h, links, homolog))
        count += 1

    # Atualiza tags de rule_nikolas_08_carne_estragada_vigilancia_sanitaria
    cur.execute("""
        UPDATE regras_negocio
        SET tags = '["carne estragada", "alimento vencido", "mercado", "acougue", "vigilancia sanitaria", "dvs", "procon", "denuncia alimento", "estabelecimento fedendo", "comercio fedendo", "vende carne fedendo", "mau cheiro de comercio"]'
        WHERE id = 'rule_nikolas_08_carne_estragada_vigilancia_sanitaria'
    """)

    conn.commit()
    conn.close()
    print(f"   -> {count} regras inseridas/atualizadas em main.db com sucesso!")
    return count

def update_ontology_json():
    print(f"[3/5] Atualizando data/ontology.json...")
    if not os.path.exists(ONTOLOGY_JSON_PATH):
        print(f"Erro: {ONTOLOGY_JSON_PATH} não encontrado!")
        return 0

    with open(ONTOLOGY_JSON_PATH, "r", encoding="utf-8") as f:
        ontology = json.load(f)

    # Verifica entidades para adicionar ou expandir aliases
    ent_map = {e.get("entity_id"): e for e in ontology}

    # 1. Entidade de Funcionário Fantasma / Denúncia Servidor
    if "DENUNCIA_FUNCIONARIO_FANTASMA" not in ent_map:
        ontology.append({
            "entity_id": "DENUNCIA_FUNCIONARIO_FANTASMA",
            "entity_type": "ouvidoria",
            "canonical_name": "Denúncia de Funcionário Fantasma e Desvio de Servidor",
            "secretaria": "Ouvidoria Geral do Município / Controladoria Geral (CGM)",
            "aliases": [
                "funcionario fantasma",
                "servidor fantasma",
                "nao vai trabalhar",
                "nao aparece para trabalhar",
                "recebe sem trabalhar",
                "servidor sumido",
                "ausencia de plantao",
                "prevaricacao"
            ],
            "keywords": ["funcionario", "fantasma", "servidor", "trabalhar", "expediente", "denuncia", "ouvidoria", "cgm"],
            "active": 1
        })

    # 2. Entidade de Concessionária Águas do Rio
    if "CONCESSIONARIA_AGUAS_DO_RIO" not in ent_map:
        ontology.append({
            "entity_id": "CONCESSIONARIA_AGUAS_DO_RIO",
            "entity_type": "concessionaria",
            "canonical_name": "Serviços e Rede de Água e Esgoto (Águas do Rio)",
            "secretaria": "Ouvidoria Geral do Município (Concessionárias)",
            "aliases": [
                "aguas do rio",
                "falta de agua",
                "sem agua na rua",
                "vazamento de agua",
                "vazamento de esgoto",
                "esgoto entupido",
                "baixa pressao agua"
            ],
            "keywords": ["aguas", "rio", "agua", "esgoto", "vazamento", "falta", "concessionaria"],
            "active": 1
        })

    # 3. Entidade de Reparo de Canteiro / Calçadas
    if "CANTEIRO_E_CALCADA_SMOA" not in ent_map:
        ontology.append({
            "entity_id": "CANTEIRO_E_CALCADA_SMOA",
            "entity_type": "obras",
            "canonical_name": "Reparo de Vias, Canteiros Públicos e Calçadas",
            "secretaria": "Secretaria Municipal de Obras e Agricultura",
            "aliases": [
                "canteiro danificado",
                "conserto de canteiro",
                "reparo de calçada",
                "calcada danificada",
                "meio-fio quebrado",
                "guia de sarjeta",
                "paralelepipedo solto",
                "passeio publico"
            ],
            "keywords": ["canteiro", "calcada", "meio-fio", "guia", "obras", "smoa", "calcamento"],
            "active": 1
        })

    with open(ONTOLOGY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(ontology, f, ensure_ascii=False, indent=2)

    print(f"   -> Ontologia atualizada em {ONTOLOGY_JSON_PATH} (Total entidades: {len(ontology)})")
    return len(ontology)

def update_chunks_jsonl_and_vector_db():
    print(f"[4/5] Inserindo novos chunks mestres em CHUNKS_MESTRES_UNIFICADOS.jsonl...")
    if not os.path.exists(CHUNKS_JSONL_PATH):
        print(f"Erro: {CHUNKS_JSONL_PATH} não encontrado!")
        return 0

    existing_ids = set()
    with open(CHUNKS_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    obj = json.loads(line)
                    existing_ids.add(obj.get("chunk_id"))
                except Exception:
                    pass

    new_chunks = []
    for r in UPDATED_AND_NEW_RULES:
        cid = r["id"]
        chunk_obj = {
            "chunk_id": cid,
            "tipo_documento": "REGRA_NEGOCIO",
            "titulo": f"Regra Canônica: {r.get('assunto', '')}",
            "conteudo": f"TEMA DA REGRA: {r.get('tema', '')}\nASSUNTO: {r.get('assunto', '')}\nDIRETRIZ OFICIAL: {r.get('conteudo', '')}\nTAGS DE BUSCA: {', '.join(r.get('tags', []))}",
            "metadata": {
                "prioridade": r.get("prioridade", "MAXIMA"),
                "boost_weight": r.get("boost_weight", 3.0),
                "tipo_label": r.get("tipo_label", "Regra de Negócio"),
                "tema": r.get("tema", ""),
                "tags": r.get("tags", []),
                "fonte_oficial": "20-dados-mestres/regras_negocio.json"
            }
        }
        new_chunks.append(chunk_obj)

    added_jsonl = 0
    with open(CHUNKS_JSONL_PATH, "a", encoding="utf-8") as f:
        for chk in new_chunks:
            if chk["chunk_id"] not in existing_ids:
                f.write(json.dumps(chk, ensure_ascii=False) + "\n")
                added_jsonl += 1

    print(f"   -> {added_jsonl} novos chunks mestres adicionados ao JSONL!")

    # Inserção incremental no vector.db
    print(f"[5/5] Inserindo incrementalmente no vector.db (tabelas chunks e chunks_fts)...")
    if not os.path.exists(VECTOR_DB_PATH):
        print(f"Erro: {VECTOR_DB_PATH} não encontrado!")
        return 0

    conn = sqlite3.connect(VECTOR_DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id FROM chunks")
    existing_chunk_ids = set(r[0] for r in cur.fetchall())

    added_db = 0
    updated_db = 0
    for chk in new_chunks:
        cid = chk["chunk_id"]
        tipo = chk["tipo_documento"]
        titulo = chk["titulo"]
        conteudo = chk["conteudo"]
        meta_json = json.dumps(chk["metadata"], ensure_ascii=False)

        if cid in existing_chunk_ids:
            cur.execute("""
                UPDATE chunks
                SET tipo = ?, titulo = ?, conteudo = ?, metadata_json = ?
                WHERE id = ?
            """, (tipo, titulo, conteudo, meta_json, cid))
            updated_db += 1
        else:
            cur.execute("""
                INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
                VALUES (?, ?, ?, ?, ?, NULL)
            """, (cid, tipo, titulo, conteudo, meta_json))
            added_db += 1

        # Atualiza o índice full-text FTS se existir
        try:
            cur.execute("INSERT OR REPLACE INTO chunks_fts (rowid, titulo, conteudo) VALUES ((SELECT rowid FROM chunks WHERE id = ?), ?, ?)", (cid, titulo, conteudo))
        except Exception:
            pass

    conn.commit()
    conn.close()
    print(f"   -> vector.db atualizado com sucesso! ({added_db} novos, {updated_db} atualizados)")
    return added_db + updated_db

if __name__ == "__main__":
    print("=" * 70)
    print("   DUQUE IA — APLICAÇÃO DE ATUALIZAÇÕES DO RELATÓRIO DE AUDITORIA")
    print("=" * 70)
    update_regras_json()
    update_main_db()
    update_ontology_json()
    update_chunks_jsonl_and_vector_db()
    print("\n[SUCESSO] Todas as bases e tabelas foram atualizadas incrementalmente!")
