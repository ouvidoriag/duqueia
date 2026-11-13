"""
Configuração Declarativa do Motor de Regras de Ranking (Ranking Rules Engine)
Permite adicionar novos domínios da prefeitura (ex: Educação, Iluminação, Saúde, Finanças, Governo)
sem modificar nenhuma linha do código de ranking.
"""

BOOST_WEIGHTS = {
    "STRUCTURED_STRONG_MATCH": 0.20,
    "LOCALITY": 0.25,
    "DOMAIN_MATCH": 0.35,
    "SPECIALTY": 0.30,
    "CARTA_SERVICOS_PENALTY": -0.25,
    "SPECIALTY_PENALTY": -0.40
}

BOOST_RULES = [
    {
        "name": "governance_and_city_info",
        "description": "Boost de informações da cidade, prefeito, distritos e história",
        "query_terms": ["distrito", "prefeito", "historia", "origem", "fundacao", "censo", "populacao"],
        "source_contains": ["a_cidade", "prefeito", "lacunas_dados_resolvidas"],
        "category_match": ["general"],
        "boost": BOOST_WEIGHTS["DOMAIN_MATCH"],
        "penalty_rules": [
            {"category": "carta_servicos", "penalty": BOOST_WEIGHTS["CARTA_SERVICOS_PENALTY"]}
        ]
    },
    {
        "name": "education_and_nursery",
        "description": "Boost de matrícula escolar, creche e vagas municipais",
        "query_terms": ["creche", "creches", "matricula", "matricular", "vaga escolar", "escola municipal", "ensino fundamental"],
        "source_contains": ["lacunas_dados_resolvidas", "educacao", "escola"],
        "category_match": ["educacao"],
        "boost": BOOST_WEIGHTS["DOMAIN_MATCH"],
        "penalty_rules": [
            {"category": "transportes", "penalty": -0.30}
        ]
    },
    {
        "name": "transport_and_permits",
        "description": "Boost para concessões e permissões de transporte (transporte escolar, táxi, ônibus e vistorias)",
        "query_terms": ["transporte escolar", "transporte por taxi", "transporte por táxi", "onibus", "ônibus", "tarifa zero", "permissao", "permissão", "vistoria anual", "legalizacao", "legalização"],
        "source_contains": ["transporte", "vw_ia_servicos"],
        "category_match": ["transporte", "transportes", "servicos_publicos", "carta_servicos"],
        "boost": 0.40,
        "penalty_rules": [
            {"category": "educacao", "penalty": -0.40}
        ]
    },
    {
        "name": "public_lighting",
        "description": "Boost de iluminação pública, reparo de postes e lâmpadas",
        "query_terms": ["poste", "lampada", "iluminacao", "ilumina", "luz"],
        "source_contains": ["lampada", "iluminacao", "lacunas_dados_resolvidas"],
        "category_match": ["iluminacao"],
        "boost": BOOST_WEIGHTS["DOMAIN_MATCH"]
    },
    {
      "name": "health_and_emergencies",
      "description": "Boost para UPAs, hospitais e emergências de saúde",
      "query_terms": ["hospital", "upa", "upas", "uph", "emergencia", "emergência", "dor", "medico", "médico", "posto", "gravidez", "exame"],
      "source_contains": ["saude.md", "saude.json", "postos_saude_caxias", "lacunas_dados_resolvidas"],
      "category_match": ["saude"],
      "boost": BOOST_WEIGHTS["DOMAIN_MATCH"]
    },
    {
        "name": "tax_and_finance",
        "description": "Boost de IPTU, alvará, ISS e tributos",
        "query_terms": ["iptu", "alvara", "iss", "fazenda", "tributo", "imposto", "carne"],
        "source_contains": ["fazenda", "tributos", "lacunas_dados_resolvidas"],
        "boost": BOOST_WEIGHTS["DOMAIN_MATCH"]
    },
    {
        "name": "iptu_2a_via_and_carne",
        "description": "Boost prioritário para guias, 2ª via e emissão de carnê do IPTU",
        "query_terms": ["2a via", "2ª via", "segunda via", "emitir", "emissao", "emissão", "carne", "carnê"],
        "source_contains": ["lacunas_dados_resolvidas"],
        "boost": 0.45
    },
    {
        "name": "fundec_and_courses",
        "description": "Boost para cursos gratuitos e qualificação da FUNDEC",
        "query_terms": ["fundec", "curso", "cursos", "gratuitos", "qualificacao", "barbeiro", "ingles", "espanhol"],
        "source_contains": ["lacunas_dados_resolvidas", "fundec"],
        "boost": BOOST_WEIGHTS["DOMAIN_MATCH"]
    },
    {
        "name": "social_assistance_and_disasters",
        "description": "Boost de acolhimento social, chuvas, enchentes, CRAS e benefícios eventuais da SMASDH",
        "query_terms": ["chuva", "chuvas", "enchente", "enchentes", "desabamento", "desastre", "cras", "assistencia social", "aluguel social", "perdi tudo", "destruida", "destruido", "calamidade"],
        "source_contains": ["assistencia_social_desastres_chuvas_cras", "smasdh", "cras", "regras_negocio"],
        "boost": 0.55,
        "penalty_rules": [
            {"category": "saude", "penalty": -0.40}
        ]
    },
    {
        "name": "sisreg_health_regulation",
        "description": "Boost de regulação, demora e agendamento no SISREG",
        "query_terms": ["sisreg", "demora", "especialista", "marcar especialista", "regulacao", "regulação", "esperando"],
        "source_contains": ["acompanhamento_sisreg_tom_institucional", "regras_negocio"],
        "boost": 0.55
    },
    {
        "name": "smoa_vs_smuh_scope",
        "description": "Boost comparativo de competência entre SMOA e SMUH",
        "query_terms": ["diferenca", "diferença", "secretaria de obras", "secretaria de urbanismo", "escopo", "competencia", "smoa", "smuh"],
        "source_contains": ["smoa_vs_smuh", "regras_negocio"],
        "boost": 0.55
    }
]

KNOWN_LOCALITIES = [
    "xerem", "xerém", "jardim primavera", "parque paulista",
    "imbarie", "imbariê", "pilar", "saracuruna",
    "campos eliseos", "campos elíseos", "pantanal", "centenario",
    "centenário", "25 de agosto"
]
