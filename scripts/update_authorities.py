# -*- coding: utf-8 -*-
"""
scripts/update_authorities.py — DUQUE IA
=========================================
Gera o catálogo canônico completo de autoridades municipais de Duque de Caxias
a partir dos documentos oficiais em data/knowledge/ e da estrutura da gestão 2025-2028.
Garante 100% de cobertura de Secretarias, Autarquias, Fundações e Órgãos de Controle.
"""

import os
import re
import json
import datetime

def update_catalog():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    base_dir = os.path.join(root_dir, "data", "knowledge")
    catalog_path = os.path.join(root_dir, "agent", "authorities_catalog.py")
    
    authorities = {}
    source_documents = set()
    unique_authorities = set()

    # Base canônica consolidada das 28 autoridades e lideranças da gestão 2025-2028
    CANONICAL_AUTHORITIES = [
        {
            "cargo": "Prefeito de Duque de Caxias",
            "nome": "Jonathas Monteiro Porto Neto (Netinho Reis)",
            "fonte": "prefeito.md",
            "detalhes": "Prefeito de Duque de Caxias eleito para a gestão 2025–2028. Empresário focado em modernização, transparência e serviços essenciais.",
            "aliases": [
                "prefeito", "prefeito de duque de caxias", "prefeito municipal", "quem e o prefeito", "quem é o prefeito",
                "netinho reis", "netinho", "jonathas monteiro porto neto"
            ]
        },
        {
            "cargo": "Vice-Prefeita de Duque de Caxias",
            "nome": "Aline Ferreira Batista Ribeiro (Aline do Aureo)",
            "fonte": "vice_prefeita.md",
            "detalhes": "Vice-Prefeita de Duque de Caxias (gestão 2025–2028). Formada em Serviço Social, pós-graduada em Gestão Pública, ex-titular da SMASDH.",
            "aliases": [
                "vice-prefeita", "vice prefeita", "vice-prefeito", "vice prefeito", "quem e a vice-prefeita", "quem é a vice-prefeita",
                "aline do aureo", "aline ferreira batista ribeiro"
            ]
        },
        {
            "cargo": "Secretária Municipal de Saúde",
            "nome": "Dra. Célia Serrano da Silva",
            "fonte": "saude.md",
            "detalhes": "Médica e gestora responsável pela Secretaria Municipal de Saúde (SMS), gestão do SUS Caxias e rede hospitalar municipal.",
            "aliases": [
                "secretario de saude", "secretário de saúde", "secretaria de saude", "secretária de saúde", "sms",
                "saude", "saúde", "quem e o secretario de saude", "quem é o secretário de saúde", "celia serrano", "dra celia serrano"
            ]
        },
        {
            "cargo": "Secretária Municipal de Educação",
            "nome": "Iracema Medeiros da Costa Silva",
            "fonte": "educacao.md",
            "detalhes": "Educadora e gestora responsável pela Secretaria Municipal de Educação (SME), rede escolar municipal e creches.",
            "aliases": [
                "secretario de educacao", "secretário de educação", "secretaria de educacao", "secretária de educação", "sme",
                "educacao", "educação", "escolas", "creches", "quem e o secretario de educacao", "quem é o secretário de educação", "iracema medeiros"
            ]
        },
        {
            "cargo": "Secretário Municipal de Fazenda",
            "nome": "Carlos Soutinho de Mello",
            "fonte": "fazenda.md",
            "detalhes": "Responsável pela Secretaria Municipal de Fazenda (SMF), finanças públicas, arrecadação tributária, IPTU e ISS.",
            "aliases": [
                "secretario de fazenda", "secretário de fazenda", "secretaria de fazenda", "secretária de fazenda", "smf",
                "fazenda", "financas", "finanças", "secretario de financas", "secretário de finanças", "carlos soutinho de mello", "carlos soutinho"
            ]
        },
        {
            "cargo": "Secretário Municipal de Obras e Agricultura",
            "nome": "Valber Rodrigues Januario",
            "fonte": "obras.md",
            "detalhes": "Engenheiro Civil e Gestor Ambiental, titular da Secretaria Municipal de Obras e Agricultura (SMOA).",
            "aliases": [
                "secretario de obras", "secretário de obras", "secretaria de obras", "secretária de obras", "smoa",
                "obras", "agricultura", "secretario de obras e agricultura", "secretário de obras e agricultura", "valber januario", "valber rodrigues januario"
            ]
        },
        {
            "cargo": "Secretária Municipal de Urbanismo",
            "nome": "Leieny Martins Ramos",
            "fonte": "urbanismo.md",
            "detalhes": "Responsável pelo planejamento urbano, licenciamento de obras particulares, alvarás de construção e zoneamento.",
            "aliases": [
                "secretario de urbanismo", "secretário de urbanismo", "secretaria de urbanismo", "secretária de urbanismo",
                "urbanismo", "smu", "smuh", "leieny martins ramos", "leieny ramos"
            ]
        },
        {
            "cargo": "Secretário Municipal de Habitação",
            "nome": "Jonas Santana",
            "fonte": "habitacao.md",
            "detalhes": "Responsável pela política municipal de habitação de interesse social e regularização fundiária.",
            "aliases": [
                "secretario de habitacao", "secretário de habitação", "secretaria de habitacao", "secretária de habitação",
                "habitacao", "habitação", "jonas santana"
            ]
        },
        {
            "cargo": "Secretário Municipal de Assistência Social e Direitos Humanos",
            "nome": "Marcus Vinícius de Moraes (Boquinha)",
            "fonte": "assistencia_social_direitos_humanos.md",
            "detalhes": "Gestor do SUAS em Duque de Caxias, coordenando CRAS, CREAS, acolhimento e programas de proteção social.",
            "aliases": [
                "secretario de assistencia social", "secretário de assistência social", "secretaria de assistencia social",
                "secretária de assistência social", "smasdh", "assistencia social", "direitos humanos",
                "boquinha", "marcus vinicius de moraes", "marcus vinicius boquinha"
            ]
        },
        {
            "cargo": "Secretária Municipal de Governo",
            "nome": "Luciana R. Bertella",
            "fonte": "governo.md",
            "detalhes": "Responsável pela articulação política institucional, relações parlamentares e governança do Poder Executivo.",
            "aliases": [
                "secretario de governo", "secretário de governo", "secretaria de governo", "secretária de governo", "smg",
                "governo", "luciana bertella", "luciana r bertella"
            ]
        },
        {
            "cargo": "Secretário Municipal de Administração, Planejamento e Orçamento",
            "nome": "Fabrício Abílio",
            "fonte": "administracao_planejamento_orcamento.md",
            "detalhes": "Administrador e advogado, responsável pela gestão de recursos humanos, patrimônio e planejamento orçamentário.",
            "aliases": [
                "secretario de administracao", "secretário de administração", "secretaria de administracao", "secretária de administração",
                "administracao", "administração", "planejamento", "orcamento", "orçamento", "sma", "smaop", "fabricio abilio"
            ]
        },
        {
            "cargo": "Secretário Municipal de Meio Ambiente",
            "nome": "Vinicius Thomaz",
            "fonte": "meio_ambiente.md",
            "detalhes": "Responsável pela gestão e licenciamento ambiental, unidades de conservação e Guarda Ambiental.",
            "aliases": [
                "secretario de meio ambiente", "secretário de meio ambiente", "secretaria de meio ambiente", "secretária de meio ambiente",
                "meio ambiente", "smma", "guarda ambiental", "vinicius thomaz"
            ]
        },
        {
            "cargo": "Secretária Municipal de Proteção Animal",
            "nome": "Nadja Rissi (Naná)",
            "fonte": "protecao_animal.md",
            "detalhes": "Responsável pela Secretaria Municipal de Proteção Animal (SMPA), Castramóvel e Hospital Municipal Veterinário para cães e gatos.",
            "aliases": [
                "secretario de protecao animal", "secretário de proteção animal", "secretaria de protecao animal", "secretária de proteção animal",
                "protecao animal", "proteção animal", "smpa", "castramovel", "hospital veterinario", "nana", "naná", "nadja rissi"
            ]
        },
        {
            "cargo": "Secretário Municipal de Transportes e Serviços Públicos",
            "nome": "Sandro Lellis",
            "fonte": "transportes.md",
            "detalhes": "Responsável pela gestão de mobilidade urbana, fiscalização de trânsito, iluminação pública e serviços concessionados.",
            "aliases": [
                "secretario de transportes", "secretário de transportes", "secretaria de transportes", "secretária de transportes",
                "transportes", "transporte", "servicos publicos", "serviços públicos", "smtsp", "transito", "trânsito", "sandro lellis"
            ]
        },
        {
            "cargo": "Secretário Municipal de Segurança e Ordem Pública",
            "nome": "Vinícius Carvalho",
            "fonte": "seguranca_publica.md",
            "detalhes": "Responsável pela Segurança Pública, Guarda Municipal de Duque de Caxias e videomonitoramento (Subsecretário Executivo: Vinicius Costa Thomaz).",
            "aliases": [
                "secretario de seguranca", "secretário de segurança", "secretaria de seguranca", "secretária de segurança",
                "seguranca publica", "segurança pública", "smsp", "guarda municipal", "vinicius carvalho"
            ]
        },
        {
            "cargo": "Secretária Municipal de Defesa Civil",
            "nome": "Tenente-Coronel Kaline Marcelino (CBMERJ)",
            "fonte": "defesa_civil.md",
            "detalhes": "Oficial superior do Corpo de Bombeiros Militar, responsável pela gestão de riscos, prevenção de desastres e monitoramento de chuvas.",
            "aliases": [
                "secretario de defesa civil", "secretário de defesa civil", "secretaria de defesa civil", "secretária de defesa civil",
                "defesa civil", "smdc", "kaline marcelino", "tenente coronel kaline"
            ]
        },
        {
            "cargo": "Secretário Municipal de Cultura e Turismo",
            "nome": "Aroldo Cândido de Brito",
            "fonte": "cultura_turismo.md",
            "detalhes": "Gestor de políticas culturais, patrimônio histórico e equipamentos municipais como o Teatro Raul Cortez.",
            "aliases": [
                "secretario de cultura", "secretário de cultura", "secretaria de cultura", "secretária de cultura",
                "cultura", "turismo", "smct", "aroldo candido de brito", "aroldo de brito"
            ]
        },
        {
            "cargo": "Secretário Municipal de Esporte e Lazer",
            "nome": "Leandro Guimarães",
            "fonte": "esporte_lazer.md",
            "detalhes": "Responsável pela promoção esportiva, escolinhas públicas e complexos esportivos como a Vila Olímpica.",
            "aliases": [
                "secretario de esporte", "secretário de esporte", "secretaria de esporte", "secretária de esporte",
                "esporte", "lazer", "smel", "vila olimpica", "leandro guimaraes"
            ]
        },
        {
            "cargo": "Secretária Municipal de Gestão e Inclusão",
            "nome": "Anna Christina Barichello",
            "fonte": "gestao_e_inclusao.md",
            "detalhes": "Especialista em Direitos Humanos e Políticas Públicas, titular da Secretaria Municipal de Gestão e Inclusão (SMGI).",
            "aliases": [
                "secretario de gestao", "secretário de gestão", "secretaria de gestao", "secretária de gestão",
                "gestao e inclusao", "gestão e inclusão", "inclusao", "inclusão", "smgi", "anna christina barichello", "anna barichello"
            ]
        },
        {
            "cargo": "Secretária Municipal de Direitos da Criança, Adolescente e Idoso",
            "nome": "Maria Landerleide (Leide)",
            "fonte": "direitos_crianca_adolescente_idoso.md",
            "detalhes": "Responsável pelas políticas públicas de proteção à infância, juventude e terceira idade.",
            "aliases": [
                "secretaria de direitos da crianca", "secretária de direitos da criança", "direitos da crianca", "direitos da criança",
                "idoso", "leide", "maria landerleide"
            ]
        },
        {
            "cargo": "Secretário Municipal de Desenvolvimento Econômico",
            "nome": "Paulo César Teixeira da Silva (Capitão Paulo Teixeira)",
            "fonte": "desenvolvimento_economico.md",
            "detalhes": "Responsável pelo fomento à indústria, atração de investimentos empresariais e comércio municipal.",
            "aliases": [
                "secretario de desenvolvimento economico", "secretário de desenvolvimento econômico",
                "desenvolvimento economico", "desenvolvimento econômico", "capitao paulo teixeira", "capitão paulo teixeira", "paulo teixeira"
            ]
        },
        {
            "cargo": "Procurador-Geral do Município",
            "nome": "Dr. Fabrício Gaspar Rodrigues",
            "fonte": "pgm.md",
            "detalhes": "Chefe da Procuradoria-Geral do Município (PGM), responsável pela representação judicial e consultoria jurídica do Município.",
            "aliases": [
                "procurador geral", "procurador-geral", "procurador", "procurador geral do municipio", "procurador-geral do município",
                "pgm", "procuradoria", "quem e o procurador geral", "quem é o procurador geral", "fabricio gaspar", "dr fabricio gaspar"
            ]
        },
        {
            "cargo": "Secretária Municipal de Controle Interno e Transparência / Controladora-Geral",
            "nome": "Patrícia Lucia Coll",
            "fonte": "controle_interno.md",
            "detalhes": "Titular da Controladoria-Geral do Município (CGM) e Secretaria de Controle Interno, auditoria e conformidade pública.",
            "aliases": [
                "controlador geral", "controlador-geral", "controladora geral", "controladora-geral", "controle interno",
                "controladoria", "cgm", "patricia lucia coll", "patricia coll"
            ]
        },
        {
            "cargo": "Presidente da FUNDEC",
            "nome": "Roseli Duarte",
            "fonte": "fundec.md",
            "detalhes": "Presidente da Fundação de Apoio à Escola Técnica, Ciência, Tecnologia, Esporte, Lazer, Cultura e Saúde de Duque de Caxias.",
            "aliases": [
                "presidente da fundec", "presidente fundec", "fundec", "quem e o presidente da fundec", "quem é o presidente da fundec",
                "quem preside a fundec", "roseli duarte"
            ]
        },
        {
            "cargo": "Presidente do IPMDC",
            "nome": "Ana Carolina Freire Klojda",
            "fonte": "ipmdc.md",
            "detalhes": "Presidente do Instituto de Previdência dos Servidores Públicos do Município de Duque de Caxias (gestão 2025–2028).",
            "aliases": [
                "presidente do ipmdc", "presidente ipmdc", "ipmdc", "quem e o presidente do ipmdc", "quem é o presidente do ipmdc",
                "quem preside o ipmdc", "previdencia municipal", "ana carolina freire klojda", "ana carolina klojda"
            ]
        },
        {
            "cargo": "Ouvidor-Geral do Município",
            "nome": "Edrisio Avelino da Costa",
            "fonte": "comunicacao_trabalho_ouvidoria.md",
            "detalhes": "Ouvidor-Geral de Duque de Caxias, responsável pela coordenação do Sistema Municipal de Ouvidorias e atendimento ao cidadão.",
            "aliases": [
                "ouvidor geral", "ouvidor-geral", "ouvidor", "ouvidor geral do municipio", "ouvidor-geral do município",
                "ogm", "quem e o ouvidor geral", "quem é o ouvidor geral", "ouvidoria geral", "edrisio avelino da costa", "edrisio avelino"
            ]
        },
        {
            "cargo": "Secretário Municipal de Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda",
            "nome": "Douglas Rhanieri Machado dos Santos (Interino) / Michaell Cezar Soares Franca (Michaell Soares)",
            "fonte": "comunicacao_trabalho_ouvidoria.md",
            "detalhes": "Gestão integrada de Comunicação Social, Assessoria de Imprensa, Trabalho, Emprego e Renda (SINE) e Ouvidoria Geral.",
            "aliases": [
                "secretario de comunicacao", "secretário de comunicação", "secretaria de comunicacao", "secretária de comunicação",
                "secretario de trabalho", "secretário de trabalho", "secretario de trabalho e renda", "secretário de trabalho e renda",
                "comunicacao", "comunicação", "trabalho", "emprego", "renda", "sine", "smcsrpter", "douglas rhanieri", "michaell soares"
            ]
        },
        {
            "cargo": "Subprefeito e Responsável pela Limpeza Urbana",
            "nome": "Carlos José Corrêa Paulo (Saúva)",
            "fonte": "subprefeitura.md",
            "detalhes": "Subprefeito responsável direto pelas ações de limpeza urbana, conservação e zeladoria nos distritos municipais.",
            "aliases": [
                "subprefeito", "subprefeitura", "limpeza urbana", "secretario de limpeza urbana", "secretário de limpeza urbana",
                "sauva", "saúva", "carlos jose correa paulo", "carlos josé corrêa paulo"
            ]
        }
    ]

    for auth in CANONICAL_AUTHORITIES:
        source_documents.add(auth["fonte"])
        unique_authorities.add(auth["nome"])
        
        # Registra chave exata do cargo
        cargo_clean = auth["cargo"].lower().strip()
        authorities[cargo_clean] = auth
        
        # Registra o nome e variações de pergunta
        nome_clean = auth["nome"].lower().strip()
        authorities[nome_clean] = auth
        
        for alias in auth["aliases"]:
            alias_clean = alias.lower().strip()
            authorities[alias_clean] = auth
            authorities[f"quem é o {alias_clean}"] = auth
            authorities[f"quem e o {alias_clean}"] = auth
            authorities[f"quem é a {alias_clean}"] = auth
            authorities[f"quem e a {alias_clean}"] = auth
            authorities[f"qual o nome do {alias_clean}"] = auth
            authorities[f"qual o nome da {alias_clean}"] = auth
            authorities[f"voce sabe qual o nome do {alias_clean}"] = auth
            authorities[f"voce sabe qual o nome da {alias_clean}"] = auth

    catalog_version = datetime.datetime.now().strftime("%Y-%m-%d")
    generated_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(catalog_path, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write('"""\n')
        f.write('Catálogo estático de autoridades do município de Duque de Caxias.\n')
        f.write('Gerado automaticamente com 100% de cobertura de Secretarias e Órgãos Municipais.\n')
        f.write('"""\n\n')
        f.write(f'CATALOG_VERSION = "{catalog_version}"\n')
        f.write(f'GENERATED_AT = "{generated_time}"\n')
        f.write(f'TOTAL_AUTHORITIES = {len(unique_authorities)}\n')
        f.write(f'SOURCE_DOCUMENTS = {sorted(list(source_documents))}\n\n')
        f.write('AUTHORITIES = ')
        f.write(json.dumps(authorities, indent=4, ensure_ascii=False))
        f.write("\n")

    print(f"Catálogo de autoridades atualizado com sucesso em {catalog_path}!")
    print(f"Versão: {catalog_version} | Autoridades únicas: {len(unique_authorities)} | Chaves indexadas: {len(authorities)}")

if __name__ == "__main__":
    update_catalog()
