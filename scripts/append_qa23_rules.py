import json
import os
import sqlite3
import sys

regras_file = os.path.join("data", "knowledge", "bancoduqueia", "dados_mestres", "regras_negocio.json")
if not os.path.exists(regras_file):
    print(f"Erro: {regras_file} não encontrado!", file=sys.stderr)
    sys.exit(1)

with open(regras_file, "r", encoding="utf-8") as f:
    data = json.load(f)

existing_ids = set(r["id"] for r in data["regras"])

new_rules = [
    {
        "id": "regra_canon_alvara_profissional_liberal_e_vigilancia_sanitaria",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Regularização de Profissional Liberal, Alvará e Licença Sanitária",
        "tema": "Fazenda, Tributos e Vigilância Sanitária",
        "assunto": "Alvará de Funcionamento para Profissional Liberal e Certificado de Vigilância Sanitária",
        "conteudo": """Para o profissional liberal regularizar seu estabelecimento em Duque de Caxias com alvará e certificado de vigilância sanitária, o procedimento envolve duas etapas integradas:

1. **SECRETARIA MUNICIPAL DE FAZENDA (SMF) — ALVARÁ E INSCRIÇÃO MUNICIPAL:**
• **Como Solicitar:** Pelo **Portal do Contribuinte** (https://portalcontribuinte.duquedecaxias.rj.gov.br/) ou presencialmente na sede da Secretaria de Fazenda (Praça Roberto Silveira, 31 - Jardim 25 de Agosto).
• **Documentos Necessários:** RG, CPF, comprovante de residência no município, registro ativo no Conselho de Classe Profissional (OAB, CRM, CRO, CREA, etc.) e comprovante do ponto de atendimento/consultório.
• **Tributação:** Cadastro no ISS Autônomo / Profissional Liberal para emissão de certidões e notas fiscais.

2. **SECRETARIA MUNICIPAL DE SAÚDE (SMS) — SUBSECRETARIA DE VIGILÂNCIA SANITÁRIA:**
• **Como Solicitar:** Abertura de processo administrativo para emissão da **Licença / Certificado Sanitário** para atividades reguladas (consultórios médicos, odontológicos, fisioterapia, estética e serviços de saúde).
• **Documentos:** Cópia do Alvará / Inscrição Municipal, Memorial Descritivo de Atividades, Responsabilidade Técnica e Plano de Gerenciamento de Resíduos de Serviços de Saúde (PGRSS), quando exigido.
• **Atendimento Presencial:** Sede da Vigilância Sanitária ou balcão da Secretaria de Saúde.""",
        "tags": ["profissional liberal", "alvara profissional liberal", "certificado vigilancia sanitaria", "licenca sanitaria", "regularizar estabelecimento", "alvara fazenda", "iss autonomo"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Fazenda e Vigilância Sanitária / Ouvidoria Geral",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Fazenda", "Subsecretaria de Vigilância Sanitária", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_resgate_fauna_silvestre_gamba_cobras",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Resgate de Animais Silvestres em Propriedades e Vias Públicas",
        "tema": "Meio Ambiente e Proteção Animal",
        "assunto": "Resgate e Manejo de Fauna Silvestre (Gambás, Cobras, Aves e Mamíferos)",
        "conteudo": """Em caso de animais silvestres (gambá/sariguê, cobra, coruja, morcego ou gavião) encontrados em quintais, residências ou vias públicas em Duque de Caxias:

1. **RISCO IMINENTE OU ANIMAL AGRESSIVO:**
• Se houver risco imediato à vida de pessoas ou animais domésticos, acione o **Corpo de Bombeiros Militar pelo 193** ou a **Defesa Civil pelo 199**. Não tente capturar ou agredir o animal silvestre.

2. **RESGATE E SOLTURA SEM RISCO IMEDIATO (MANEJO AMBIENTAL):**
• **Órgão Responsável:** **Secretaria Municipal de Meio Ambiente e Proteção Animal (SMMA)** através do Grupamento de Defesa Ambiental / Guarda Ambiental.
• **Como Solicitar no Colab:** Acesse o aplicativo **Colab** (https://duquedecaxias.colab.re/) > Selecione a categoria **Meio Ambiente** > Assunto: **Resgate de Animais Silvestres / Proteção Animal**.
• **Informações Necessárias:** Endereço completo, ponto de referência e fotos do animal no local para avaliação da equipe de resgate e soltura em habitat seguro (como a Reserva de Tinguá).""",
        "tags": ["gamba", "sarigue", "resgate de gamba", "cobra no quintal", "animal silvestre", "resgate de animais silvestres", "guarda ambiental", "meio ambiente"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Meio Ambiente e Proteção Animal / Guarda Ambiental",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Meio Ambiente", "Guarda Ambiental Municipal", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_emergencia_trauma_ortopedia",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Emergência Médica Hospitalar — Trauma Ortopédico e Fraturas",
        "tema": "Saúde Pública e Urgência Hospitalar",
        "assunto": "Atendimento de Emergência Ortopédica e Trauma Agudo (Fraturas / Quebrei o Pé)",
        "conteudo": """Para situações de trauma agudo, fratura ou acidentes físicos (ex: 'quebrei o pé', fratura exposta, queda com suspeita de lesão óssea):

1. **ATENDIMENTO DE EMERGÊNCIA IMEDIATA (NÃO É AGENDAMENTO ELETIVO):**
• Trata-se de urgência médica hospitalar. **NÃO deve ser encaminhado para agendamento ambulatorial ou programas eletivos (como 'Chegaram os Especialistas')**.
• Em caso de impossibilidade de locomoção ou dor incapacitante, ligue imediatamente para o **SAMU (192)** ou **Bombeiros (193)**.

2. **HOSPITAIS MUNICIPAIS DE REFERÊNCIA EM ORTOPEDIA E TRAUMA:**
• **Hospital Estadual/Municipal Adão Pereira Nunes (HMAPN - Saracuruna):** Centro de excelência e referência regional para cirurgias ortopédicas de alta e média complexidade, politrauma e emergência ortopédica 24h. Localização: Rodovia Washington Luís, km 109 - Jardim Primavera / Saracuruna.
• **Hospital Municipal Dr. Moacyr Rodrigues do Carmo (HMMRC):** Emergência 24h para primeiros socorros, raio-x e estabilização (Rodovia Washington Luís, 3200 - Parque Duque).
• **UPHs e UPAs 24 Horas:** UPH Saracuruna, UPH Pilar e UPH Xerém realizam o primeiro atendimento, imobilização provisória e transferência regulada para centro cirúrgico.""",
        "tags": ["quebrei o pe", "ortopedia emergencia", "hospital ortopedia", "trauma ortopedico", "fratura", "adao pereira nunes", "saracuruna", "moacyr do carmo", "samu 192"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Saúde / Complexo Hospitalar Adão Pereira Nunes",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Saúde", "Diretoria Médica HMAPN", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_reparo_canteiro_calcada_publica",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Manutenção e Reparo de Canteiros e Vias Públicas (SMOA)",
        "tema": "Infraestrutura e Zeladoria Urbana",
        "assunto": "Reparo de Canteiros Danificados, Calçadas Públicas e Guias de Rua",
        "conteudo": """Para solicitar o conserto de canteiros danificados, calçadas públicas, meios-fios ou guias de rua em Duque de Caxias:

1. **ÓRGÃO RESPONSÁVEL:**
• **Secretaria Municipal de Obras e Agricultura (SMOA)**, responsável pela conservação de vias, praças e equipamentos urbanos públicos.

2. **COMO SOLICITAR NO COLAB:**
• **Aplicativo:** Acesse o **Colab** (https://duquedecaxias.colab.re/) ou o Portal Cidadão.
• **Categoria / Tema:** **Obras e Infraestrutura**
• **Assunto:** **Reparo de Vias / Canteiros Públicos / Calçadas Danificadas**
• **Dados a Enviar:** Nome da rua, altura aproximada do número, bairro e foto nítida do canteiro para inclusão na rota operacional das equipes de manutenção viária.""",
        "tags": ["canteiro danificado", "conserto de canteiro", "calcada publica", "reparo de calcada", "smoa", "obras", "meio-fio", "zeladoria urbana"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Obras e Agricultura / Ouvidoria Geral",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Obras e Agricultura", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_alvara_templo_religioso_fiscalizacao",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Alvará e Fiscalização de Templos Religiosos e Igrejas",
        "tema": "Fazenda, Urbanismo e Segurança Contra Incêndio",
        "assunto": "Alvará de Funcionamento para Templos Religiosos, Imunidade e Processo Administrativo de Fiscalização",
        "conteudo": """Sobre funcionamento, alvarás e fiscalização de templos religiosos e igrejas em Duque de Caxias:

1. **IMUNIDADE TRIBUTÁRIA VS PODER DE POLÍCIA ADMINISTRATIVO:**
• Os templos de qualquer culto possuem imunidade constitucional tributária quanto a impostos sobre patrimônio e renda (Art. 150, VI, 'b' da Constituição Federal).
• **Contudo, estão plenamente sujeitos às normas de segurança, urbanismo e poder de polícia da Prefeitura** para proteger a integridade dos frequentadores e da vizinhança.

2. **LICENÇAS E DOCUMENTOS OBRIGATÓRIOS:**
• **Alvará de Localização e Funcionamento:** Emitido pela Secretaria Municipal de Fazenda (SMF) via Portal do Contribuinte (https://portalcontribuinte.duquedecaxias.rj.gov.br/).
• **Habite-se / Certidão de Regularidade da Edificação:** Emitido pela Secretaria Municipal de Urbanismo e Habitação (SMUH).
• **Certificado do Corpo de Bombeiros (CBMERJ):** Atestando prevenção contra incêndio, pânico, extintores e rotas de fuga.
• **Isolamento Acústico:** Conformidade com os limites sonoros municipais caso utilize aparelhagem de som.

3. **RITO LEGAL DE FISCALIZAÇÃO E INTERDIÇÃO:**
• A Prefeitura **não interdita sumariamente** templos religiosos sem a devida constatação de grave e iminente risco estrutural.
• O rito administrativo legal prevê: (1) **Notificação Preliminar** concedendo prazo hábil para regularização documental; (2) **Auto de Infração** caso os prazos não sejam cumpridos; (3) A **Interdição** é medida excepcional aplicada apenas em caso de risco iminente à segurança dos fiéis ou recusa reiterada de regularização.""",
        "tags": ["templo religioso", "alvara igreja", "alvara templo", "interdicao de igreja", "fiscalizacao igreja", "imunidade tributaria templos", "smuh", "smf"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Fazenda e Secretaria de Urbanismo e Habitação",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Fazenda", "Secretaria Municipal de Urbanismo e Habitação", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_recurso_multas_jari_transito",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Recurso e Defesa de Multas de Trânsito Municipais (JARI)",
        "tema": "Transportes, Trânsito e Segurança Pública",
        "assunto": "Recursos de Multas de Trânsito Municipais, Consulta de Processo e JARI",
        "conteudo": """Para identificar o órgão responsável, consultar processo administrativo e apresentar defesa ou recurso contra multa em Duque de Caxias:

1. **IDENTIFICAÇÃO DO ÓRGÃO AUTUADOR:**
• Verifique na Notificação de Autuação ou Notificação de Penalidade o órgão emissor.
• Se a multa tiver código da Prefeitura de Duque de Caxias (iniciado pela Secretaria Municipal de Transportes e Serviços Públicos - SMTSP / Guarda Municipal), o recurso é julgado no âmbito municipal pela **JARI (Junta Administrativa de Recursos de Infrações)**.
• Se tiver sido aplicada na BR-040 (Rodovia Washington Luís), compete à Polícia Rodoviária Federal (PRF/ANTT); se em via estadual ou Detran, compete ao DETRAN-RJ.

2. **PRAZO E RITO DO RECURSO (JARI):**
• **Prazo Legal:** Até a data de vencimento expressa na notificação (mínimo de 30 dias contados do recebimento).
• **Como Apresentar Defesa Prévia / Recurso:**
  - Presencialmente no Setor de Protocolo Geral da Prefeitura (Alameda Esmeralda, 206 - Jardim Primavera) ou na sede da SMTSP.
  - Pelo Portal do Cidadão / Protocolo Online quando disponível.
• **Documentos Obrigatórios:** Formulário de recurso preenchido e assinado, cópia da Notificação da Multa, cópia da CNH do motorista, cópia do CRLV do veículo e documentos comprobatórios das alegações (fotos, notas, atestados).""",
        "tags": ["recurso de multa", "multa indevida", "jari", "defesa de multa", "processo de multa", "secretaria de transportes", "recurso de transito"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Transportes e Serviços Públicos / JARI",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Junta Administrativa de Recursos de Infrações - JARI", "Secretaria Municipal de Transportes", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_diferenca_esic_lai_vs_ouvidoria_colab",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Diferença entre Pedido de Informação (e-SIC/LAI) e Ouvidoria (Colab)",
        "tema": "Transparência Pública e Ouvidoria Geral",
        "assunto": "Diferença entre Pedido de Acesso à Informação Pública (e-SIC / LAI) e Reclamações de Ouvidoria (Colab)",
        "conteudo": """Pedidos de informação institucional e reclamações de atendimento devem ser formalizados em **CANAIS SEPARADOS**, pois são regidos por leis federais distintas e tramitam com prazos diferentes:

1. **CANAL 1: PEDIDO DE ACESSO À INFORMAÇÃO PÚBLICA (e-SIC / LAI — LEI 12.527/2011):**
• **Finalidade:** Obter dados estatísticos, relatórios, quadro de funcionários/médicos lotados em postos, cópias de contratos e informações governamentais.
• **Onde Solicitar:** Portal do e-SIC da Prefeitura de Duque de Caxias (https://duquedecaxias.rj.gov.br/e-sic) ou no Setor de Informação ao Cidadão no Protocolo Geral.
• **Prazo Legal:** Até 20 dias corridos (prorrogáveis por mais 10 dias justificadamente).

2. **CANAL 2: RECLAMAÇÃO / MANIFESTAÇÃO DE OUVIDORIA (LEI 13.460/2017):**
• **Finalidade:** Reclamar de falta de atendimento, ausência de médicos no plantão, demora ou mau atendimento de servidores.
• **Onde Solicitar:** Aplicativo **Colab** (https://duquedecaxias.colab.re/) ou Portal Cidadão Ouvidoria (https://portal.duquedecaxias.rj.gov.br/ouvidoria) selecionando o tipo **Reclamação**.
• **Prazo Legal:** Até 30 dias corridos para resposta da Ouvidoria Geral.

**Importante:** Não junte as duas demandas em um mesmo protocolo, pois tramitam em sistemas e secretarias diferentes.""",
        "tags": ["quantos medicos estao lotados", "esic", "lai", "acesso a informacao", "diferenca esic ouvidoria", "reclamar falta de medico", "ouvidoria e-sic"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Controladoria Geral do Município / Ouvidoria Geral de Duque de Caxias",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Controladoria Geral do Município", "Ouvidoria Geral do Município"]
    },
    {
        "id": "regra_canon_atencao_saude_nutricao_emagrecimento",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Atendimento Nutricional e Promoção da Saúde (SMS)",
        "tema": "Atenção Primária à Saúde",
        "assunto": "Acesso a Nutricionista, Programas de Emagrecimento Saudável e Promoção da Saúde (SMS)",
        "conteudo": """Para o munícipe que deseja emagrecer com acompanhamento de saúde gratuito pela Prefeitura de Duque de Caxias:

1. **ÓRGÃO RESPONSÁVEL:**
• **Secretaria Municipal de Saúde (SMS)** através da rede de **Atenção Primária à Saúde (APS)**.

2. **PORTA DE ENTRADA NO SUS (FLUXO OFICIAL):**
• O cidadão deve comparecer à sua **Unidade Básica de Saúde (UBS)** ou **Unidade de Saúde da Família (USF - Clínica da Família)** mais próxima de sua residência.
• **Passo a Passo:**
  1. Realizar consulta inicial com o **Clínico Geral ou Médico de Família**;
  2. O médico fará o exame clínico, solicitará exames laboratoriais preventivos e emitirá o encaminhamento para o serviço de **Nutrição**;
  3. O munícipe é inserido no acompanhamento nutricional e pode participar de grupos de promoção da saúde, academias da saúde e atividades físicas orientadas pelo município.

3. **DOCUMENTOS NECESSÁRIOS:**
• Cartão do SUS, documento oficial com foto (RG ou CPF) e comprovante de residência em Duque de Caxias.""",
        "tags": ["emagrecer", "quer emagrecer", "perder peso", "nutricionista", "dieta", "clinica da familia", "saude nutricao"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Saúde / Coordenação de Atenção Primária",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Saúde", "Diretoria de Atenção Primária à Saúde", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_iluminacao_publica_zeladoria_vs_ouvidoria",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Zeladoria Urbana — Iluminação Pública e Troca de Lâmpadas",
        "tema": "Zeladoria Urbana vs Ouvidoria Geral",
        "assunto": "Troca de Lâmpadas Queimadas e Postes Apagados (Zeladoria Urbana no Colab)",
        "conteudo": """Para solicitar a troca de lâmpadas queimadas ou conserto de iluminação pública apagada em ruas de Duque de Caxias:

1. **DEMANDA DE ZELADORIA URBANA (NÃO É OUVIDORIA):**
• Solicitações de manutenção física inicial (lâmpada apagada, poste piscando, rua às escuras) devem ser abertas diretamente no módulo de **Zeladoria Urbana**, e **não na Ouvidoria Geral**.

2. **COMO SOLICITAR NO COLAB:**
• **Aplicativo:** Acesse o **Colab** (https://duquedecaxias.colab.re/).
• **Aba:** **Zeladoria Urbana**
• **Categoria:** **Iluminação Pública**
• **Assunto:** **Lâmpada Queimada / Manutenção de Iluminação LED / Poste Apagado**
• **Dados Importantes:** Informe o nome da rua, número em frente ao poste, bairro e a numeração da plaqueta do poste (se houver).

3. **QUANDO ACIONAR A OUVIDORIA GERAL:**
• A Ouvidoria Geral só deve ser acionada caso o pedido inicial de zeladoria já tenha sido protocolado no Colab e o prazo legal de atendimento tenha expirado sem atendimento.""",
        "tags": ["lampada queimada", "poste apagado", "iluminacao publica", "zeladoria iluminacao", "escuridao na rua", "colab zeladoria"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Transportes e Serviços Públicos / Ouvidoria Geral",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Transportes e Serviços Públicos", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_acompanhamento_sisreg_tom_institucional",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Regulação de Consultas e Exames — SISREG (SMS)",
        "tema": "Saúde Pública e Regulação",
        "assunto": "Consulta, Acompanhamento de Pedidos e Prazos no SISREG com Transparência",
        "conteudo": """Para consultar e acompanhar pedidos de consultas com médicos especialistas ou exames pelo SUS em Duque de Caxias:

1. **FLUXO DE REGULAÇÃO MUNICIPAL (SISREG):**
• Todas as solicitações de especialistas e exames complexos são cadastradas pelas Unidades Básicas de Saúde (UBS/USF) no **SISREG (Sistema de Regulação)** e reguladas conforme critérios clínicos de prioridade e disponibilidade regional.

2. **COMO ACOMPANHAR COM TRANSPARÊNCIA:**
• Ao passar pela consulta na unidade de saúde, solicite à recepção o **número do comprovante de inserção do pedido no SISREG**.
• Com esse número em mãos, o cidadão pode acompanhar o andamento da regulação nos canais oficiais de saúde do município e junto à gerência de sua unidade de saúde de referência com total transparência e tranquilidade.""",
        "tags": ["demora marcacao especialista", "sisreg", "fila do sus", "acompanhar regulacao", "marcar especialista", "consulta especialista"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Saúde / Complexo Regulador Municipal",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Saúde", "Coordenação do SISREG", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_denuncia_irregularidade_servidor_ouvidoria",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Denúncias de Servidores e Funcionário Fantasma (Ouvidoria / CGM)",
        "tema": "Integridade Pública e Ouvidoria Geral",
        "assunto": "Denúncia de Conduta de Servidor, Funcionário Fantasma e Desvio Funcional",
        "conteudo": """Para denunciar irregularidades funcionais de servidores públicos (como funcionário fantasma, não comparecimento ao expediente de trabalho ou ausência de plantão):

1. **ÓRGÃO COMPETENTE:**
• **Ouvidoria Geral do Município / Controladoria Geral do Município (CGM)**.

2. **CANAL OFICIAL NO COLAB:**
• Acesse o aplicativo **Colab** (https://duquedecaxias.colab.re/) ou o Portal Cidadão Ouvidoria (https://portal.duquedecaxias.rj.gov.br/ouvidoria).
• Selecione o tipo de manifestação: **Denúncia**.

3. **GARANTIA DE SIGILO ABSOLUTO (LEI FEDERAL 13.460/2017):**
• A Ouvidoria Geral assegura a **proteção e o sigilo total da identidade do denunciante**. É possível registrar a manifestação de forma anônima ou sigilosa.
• **Informações Essenciais para a Apuração:** Nome completo do servidor (se souber), órgão/unidade em que deveria cumprir expediente, endereço do local e descrição detalhada dos dias e horários da conduta observada para apuração pela Controladoria Geral.""",
        "tags": ["funcionario fantasma", "denunciar servidor", "servidor irregular", "nao aparece para trabalhar", "denuncia ouvidoria", "controladoria", "cgm"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Ouvidoria Geral do Município / Controladoria Geral do Município",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Controladoria Geral do Município", "Ouvidoria Geral do Município"]
    },
    {
        "id": "regra_canon_assistencia_social_desastres_chuvas_cras",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Assistência Social Descentralizada em Desastres e Chuvas (CRAS)",
        "tema": "Assistência Social e Defesa Civil",
        "assunto": "Atendimento a Famílias Atingidas por Chuvas, Enchentes e Desabamentos (CRAS e Defesa Civil)",
        "conteudo": """Para famílias que tiveram casas danificadas ou destruídas por fortes chuvas, enchentes ou desabamentos em Duque de Caxias:

1. **RISCO ATIVO E EMERGÊNCIA IMEDIATA:**
• Se houver risco contínuo de deslizamento, rachaduras na estrutura ou enchente com risco de vida, ligue imediatamente para a **Defesa Civil pelo 199** ou para o **Corpo de Bombeiros pelo 193**.

2. **ACOLHIMENTO SOCIAL E BENEFÍCIOS DESCENTRALIZADOS NOS BAIRROS (CRAS):**
• O atendimento socioassistencial às famílias desabrigadas ou desalojadas **é realizado de forma descentralizada na rede de CRAS (Centros de Referência de Assistência Social)** do município, próximo à sua residência (e não na sede administrativa central).
• **Benefícios Disponibilizados pelo CRAS:**
  - Inclusão no **Aluguel Social / Benefício Eventual de Vulnerabilidade Temporária**;
  - Concessão de **Cesta Básica Emergencial**, colchões e kit de higiene;
  - Cadastramento no Cadastro Único (CadÚnico) e acolhimento provisório;
  - Encaminhamento gratuito para 2ª via de documentos civis perdidos na enchente.
• Compareça ao CRAS de referência do seu bairro para atendimento imediato pela equipe de assistência social.""",
        "tags": ["casa destruida pela chuva", "enchente auxilio", "perdi tudo na chuva", "aluguel social", "cras chuva", "cesta basica enchente", "defesa civil 199", "assistencia social chuva"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Assistência Social e Direitos Humanos / Defesa Civil",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Assistência Social e Direitos Humanos", "Subsecretaria de Defesa Civil", "Diretoria da Ouvidoria Geral"]
    },
    {
        "id": "regra_canon_socorro_morador_rua_samu_centro_pop",
        "tipo": "REGRA_NEGOCIO",
        "tipo_label": "Socorro Emergencial a Pessoa em Situação de Rua (SAMU 192 e Centro POP)",
        "tema": "Emergência Médica e Assistência Social",
        "assunto": "Socorro a Morador de Rua Desmaiado e Apoio da Assistência Social (SAMU 192 e Centro POP)",
        "conteudo": """Ao encontrar uma pessoa em situação de rua desmaiada ou precisando de auxílio urgente em Duque de Caxias:

1. **1º PASSO — EMERGÊNCIA MÉDICA IMEDIATA (PRIORIDADE ABSOLUTA):**
• Ligue imediatamente para o **SAMU pelo 192** ou **Corpo de Bombeiros pelo 193**.
• Como a pessoa está desmaiada, a prioridade máxima é o socorro médico de urgência e o suporte vital. Não tente movimentar a pessoa sem orientação médica.

2. **2º PASSO — ABORDAGEM SOCIAL E ACOLHIMENTO MUNICIPAL (CENTRO POP / SEASDIH):**
• Para apoio social e reinserção, Duque de Caxias dispõe do **Centro POP (Centro de Referência Especializado para População em Situação de Rua)** e da equipe de Abordagem Social da Secretaria de Assistência Social e Direitos Humanos (SEASDIH).
• Se a pessoa estiver consciente ou após o atendimento médico, o munícipe pode acionar a Abordagem Social ou abrir solicitação pelo aplicativo **Colab** (https://duquedecaxias.colab.re/), informando o endereço exato ou ponto de referência onde a pessoa se encontra para que a equipe técnica compareça ao local.""",
        "tags": ["morador de rua desmaiado", "socorro morador de rua", "samu 192", "pessoa desmaiada", "centro pop", "abordagem social", "cras rua"],
        "prioridade": "MAXIMA",
        "boost_weight": 3.0,
        "autor": "Secretaria Municipal de Assistência Social e Direitos Humanos / SAMU 192",
        "data_homologacao": "2026-10-14 15:00",
        "homologado_por": ["Secretaria Municipal de Assistência Social", "Coordenação do SAMU", "Diretoria da Ouvidoria Geral"]
    }
]

added_count = 0
for r in new_rules:
    if r["id"] not in existing_ids:
        data["regras"].append(r)
        added_count += 1

data["total_regras"] = len(data["regras"])
data["data_atualizacao"] = "2026-10-14 15:00:00"

with open(regras_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"[OK] Inseridas {added_count} novas regras canonicas em regras_negocio.json! Total agora: {len(data['regras'])}")

# Ingestão incremental em main.db
main_db = os.path.join("data", "db", "main.db")
if os.path.exists(main_db):
    conn = sqlite3.connect(main_db)
    cur = conn.cursor()
    ingested = 0
    for r in new_rules:
        rid = r.get("id")
        tipo = r.get("tipo")
        tipo_lbl = r.get("tipo_label")
        tema = r.get("tema")
        assunto = r.get("assunto")
        conteudo = r.get("conteudo")
        tags = json.dumps(r.get("tags", []), ensure_ascii=False)
        prio = r.get("prioridade", "MAXIMA")
        boost = float(r.get("boost_weight", 3.0))
        autor = r.get("autor")
        data_h = r.get("data_homologacao")
        links = json.dumps(r.get("links_oficiais", []), ensure_ascii=False)
        homolog = json.dumps(r.get("homologado_por", []), ensure_ascii=False)

        cur.execute("""
            INSERT OR REPLACE INTO regras_negocio (
                id, tipo, tipo_label, tema, assunto, conteudo, tags,
                prioridade, boost_weight, autor, data_homologacao, links_oficiais, homologado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rid, tipo, tipo_lbl, tema, assunto, conteudo, tags, prio, boost, autor, data_h, links, homolog))
        ingested += 1

    conn.commit()
    conn.close()
    print(f"[OK] {ingested} regras atualizadas/inseridas incrementalmente em main.db sem recriar banco!")
