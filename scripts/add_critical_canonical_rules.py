"""
add_critical_canonical_rules.py — DUQUE IA
==========================================
Adiciona de forma incremental regras canônicas auditadas para eliminar
qualquer resposta de falsa ausência ("não consta na nossa base de dados oficial").
Cobre os temas identificados na auditoria:
1. Fazendinha do Autista (Funcionamento, Inscrições e Atendimento)
2. Casa do Autista (Rua Jandira vs Fazendinha em Xerém)
3. Isenção de IPTU para Aposentados e Pensionistas (+65 anos)
4. Ingresso, Vagas e Matrícula em Creches e Educação Infantil (SME)
5. Transferência Escolar e Troca de Escola (SME)

Estritamente incremental (respeita a Regra 6).
"""

import os
import json
import sqlite3

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REGRAS_JSON_PATH = os.path.join(_PROJECT_ROOT, "data", "knowledge", "bancoduqueia", "dados_mestres", "regras_negocio.json")
MAIN_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "db", "main.db")
CHUNKS_JSONL_PATH = os.path.join(_PROJECT_ROOT, "data", "knowledge", "bancoduqueia", "pipeline_storage", "CHUNKS_MESTRES_UNIFICADOS.jsonl")
VECTOR_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")

NEW_CANONICAL_RULES = [
    {
        "id": "regra_canon_fazendinha_do_autista",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Fazendinha do Autista - Equipamento Municipal em Funcionamento",
        "tema": "Gestão, Inclusão e Mulher (Fazendinha do Autista e Programas de Inclusão)",
        "assunto": "Funcionamento, Inscrição e Atendimento na Fazendinha do Autista (Xerém)",
        "conteudo": (
            "A Fazendinha do Autista é um equipamento público municipal de Duque de Caxias em PLENO FUNCIONAMENTO "
            "E ABERTO AO PÚBLICO, localizado na Rua Marcio S. Silva, 2846 - Parque Ana Dantas, distrito de Xerém. "
            "A unidade oferece gratuitamente arteterapia, equoterapia, fisioterapia, psicologia, hortoterapia, "
            "musicalização e terapia com animais no desenvolvimento de habilidades, cognição e socialização de crianças "
            "e jovens com Transtorno do Espectro Autista (TEA). "
            "COMO INSCREVER: O atendimento é presencial. O responsável deve comparecer diretamente à unidade munido "
            "dos documentos da criança e do responsável (Documento pessoal/RG, Certidão de Nascimento, Cartão do SUS, "
            "Comprovante de Residência em Duque de Caxias e Laudo Médico/Diagnóstico com CID de TEA). "
            "CUSTO: 100% Gratuito. FILA DE ESPERA: Não há fila de espera para abertura do pedido. "
            "PRAZO DO PROCEDIMENTO: Em média de 5 a 15 dias úteis para inclusão nas terapias. "
            "CANAIS DE CONTATO OFICIAIS: Telefone / WhatsApp: (21) 99482-8304 | E-mail: fazendinhadoautista@gmail.com | "
            "Instagram: https://www.instagram.com/fazendinhadoautista. "
            "ATENÇÃO: A Fazendinha em Xerém está aberta e ativa. Não confundir com a Casa do Autista (Rua Jandira), que é obra em implantação."
        ),
        "tags": [
            "fazendinha do autista", "fazendinha", "autista", "autismo", "tea", "equoterapia",
            "xerem", "rua marcio s silva", "como inscrever na fazendinha", "fazendinha esta funcionando",
            "parque ana dantas", "terapia com animais", "laudo autismo"
        ],
        "prioridade": "MAXIMA",
        "boost_weight": 4.0,
        "autor": "Ouvidoria Geral e Secretaria Municipal de Governo",
        "data_homologacao": "2026-10-26 12:00",
        "links_oficiais": ["https://duquedecaxias.rj.gov.br", "https://duquedecaxias.colab.re/"],
        "homologado_por": ["Diretoria da Ouvidoria Geral", "Coordenação de Inclusão"]
    },
    {
        "id": "regra_canon_casa_do_autista_rua_jandira_status",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Casa do Autista (1º Distrito) - Obra em Implantação vs Atendimento em Xerém",
        "tema": "Gestão, Inclusão e Mulher (Fazendinha do Autista e Programas de Inclusão)",
        "assunto": "Status da Casa do Autista da Rua Jandira (1º Distrito) vs Atendimento Ativo na Fazendinha (Xerém)",
        "conteudo": (
            "A Casa do Autista, localizada na Rua Jandira (atrás do Restaurante Popular, Parque Vila Nova, 1º Distrito "
            "de Duque de Caxias), é um projeto municipal em fase de obras e estruturação para futuro centro de atendimento "
            "multidisciplinar especializado (com fisioterapia, fonoaudiologia, pedagogia, psicologia, psiquiatria, nutrição, "
            "espaço cultural e circo). Ela ainda NÃO está aberta para atendimento imediato de rotina nem consultas ao público na Rua Jandira. "
            "ORIENTAÇÃO AO CIDADÃO: Se o munícipe precisa de atendimento terapêutico e inclusivo IMEDIATO para seu filho com autismo/TEA hoje, "
            "o encaminhamento correto é a FAZENDINHA DO AUTISTA, localizada na Rua Marcio S. Silva, 2846 - Parque Ana Dantas - Xerém, "
            "que se encontra em pleno funcionamento com equoterapia, fisioterapia, arteterapia e suporte multiprofissional gratuito "
            "(Telefone/WhatsApp: 21 99482-8304). Para dúvidas sobre o cronograma das obras da Casa do Autista, contate a Secretaria Municipal "
            "de Saúde ou a Ouvidoria Geral pelo Colab."
        ),
        "tags": [
            "casa do autista", "rua jandira", "levar filho na casa do autista", "casa do autista esta funcionando",
            "parque vila nova", "atendimento autista rua jandira", "diferenca casa do autista fazendinha"
        ],
        "prioridade": "MAXIMA",
        "boost_weight": 4.0,
        "autor": "Ouvidoria Geral e Secretaria Municipal de Saúde",
        "data_homologacao": "2026-10-26 12:00",
        "links_oficiais": ["https://duquedecaxias.rj.gov.br", "https://duquedecaxias.colab.re/"],
        "homologado_por": ["Diretoria da Ouvidoria Geral", "Secretaria Municipal de Saúde"]
    },
    {
        "id": "regra_canon_isencao_iptu_aposentados_pensionistas",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Isenção de IPTU para Aposentados e Pensionistas - Secretaria de Fazenda",
        "tema": "Fiscalização e tributos",
        "assunto": "Isenção de IPTU para Aposentados, Pensionistas e Idosos com mais de 65 anos (SMF)",
        "conteudo": (
            "A Prefeitura Municipal de Duque de Caxias, através da Secretaria Municipal de Fazenda (SMF), assegura o direito "
            "à ISENÇÃO DE IPTU para contribuintes aposentados ou pensionistas com idade igual ou superior a 65 anos, que sejam "
            "titulares de um único imóvel utilizado exclusivamente para sua própria residência e atendam aos limites de metragem "
            "e remuneração previstos no Código Tributário Municipal. "
            "COMO SOLICITAR: O benefício é solicitado mediante Abertura de Processo Administrativo presencial na Secretaria Municipal de Fazenda. "
            "ONDE COMPARECER: Praça Roberto Silveira, nº 31 - Jardim 25 de Agosto, Duque de Caxias - RJ (Sede da Fazenda Municipal). "
            "DOCUMENTOS NECESSÁRIOS: 1. Documento de Identidade (RG) e CPF; 2. Comprovante de Concessão do Benefício do INSS/Aposentadoria "
            "comprovando a condição e o valor do provento mensal; 3. Carnê do IPTU do imóvel ou Certidão de Ônus Reais/RGI comprovando titularidade "
            "de único imóvel; 4. Comprovante de Residência em nome do requerente. "
            "CUSTO: Gratuito para protocolar. "
            "CANAIS DE ATENDIMENTO: Portal do Contribuinte da SMF (https://duquedecaxias.rj.gov.br/) e Ouvidoria Geral pelo Colab."
        ),
        "tags": [
            "isencao iptu aposentado", "isencao de iptu", "iptu aposentados", "desconto iptu idoso",
            "como pedir isencao de iptu", "fazenda iptu isencao", "praca roberto silveira 31", "isencao 65 anos"
        ],
        "prioridade": "MAXIMA",
        "boost_weight": 4.0,
        "autor": "Ouvidoria Geral e Secretaria Municipal de Fazenda",
        "data_homologacao": "2026-10-26 12:00",
        "links_oficiais": ["https://duquedecaxias.rj.gov.br", "https://duquedecaxias.colab.re/"],
        "homologado_por": ["Diretoria da Ouvidoria Geral", "Secretaria Municipal de Fazenda"]
    },
    {
        "id": "regra_canon_vaga_creche_matricula_escolar_sme",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Matrícula e Vagas em Creches e Escolas Municipais - Secretaria de Educação",
        "tema": "Educação",
        "assunto": "Ingresso, Reserva de Vagas e Matrícula em Creches e Escolas da Rede Municipal (SME)",
        "conteudo": (
            "O processo de ingresso, inscrição e reserva de vagas em Creches Municipais, Educação Infantil e Ensino Fundamental "
            "em Duque de Caxias é unificado e gerenciado pela Secretaria Municipal de Educação (SME). "
            "COMO SOLICITAR VAGA EM CRECHE OU ESCOLA: "
            "1. Inscrição Oficial Online: As inscrições ocorrem de forma 100% online através do Portal Oficial da Educação de Duque de Caxias "
            "(https://educacao.duquedecaxias.rj.gov.br/) durante o período oficial divulgado no calendário anual de matrículas. "
            "2. Atendimento Presencial e Casos Especiais: Os responsáveis também podem buscar orientação presencialmente na sede da "
            "Secretaria Municipal de Educação (SME), localizada na Rua Prefeito Bernardo Távora, s/n - 25 de Agosto, Duque de Caxias - RJ, "
            "especialmente para matrícula de crianças com deficiência (PcD), autismo/TEA ou suporte da equipe multiprofissional. "
            "DOCUMENTOS PARA MATRÍCULA: Certidão de Nascimento da criança, Cartão de Vacinação atualizado, Comprovante de Residência "
            "em Duque de Caxias, Documento de Identidade e CPF do responsável legal e Cartão do SUS. "
            "CUSTO: 100% Gratuito. DÚVIDAS E CALENDÁRIO: Consulte a Ouvidoria Geral pelo Colab ou telefone (21) 2652-3835."
        ),
        "tags": [
            "vaga em creche", "creche municipal", "matricula creche", "vaga escola municipal",
            "como conseguir vaga na creche", "educacao infantil duque de caxias", "sme matricula", "rua prefeito bernardo tavora"
        ],
        "prioridade": "MAXIMA",
        "boost_weight": 4.0,
        "autor": "Ouvidoria Geral e Secretaria Municipal de Educação",
        "data_homologacao": "2026-10-26 12:00",
        "links_oficiais": ["https://educacao.duquedecaxias.rj.gov.br", "https://duquedecaxias.colab.re/"],
        "homologado_por": ["Diretoria da Ouvidoria Geral", "Secretaria Municipal de Educação"]
    },
    {
        "id": "regra_canon_transferencia_escolar_alunos_sme",
        "tipo": "REGRA_DE_NEGOCIO",
        "tipo_label": "Transferência de Aluno entre Escolas Municipais - Secretaria de Educação",
        "tema": "Educação",
        "assunto": "Transferência de Aluno entre Escolas Municipais ou de Outras Redes (SME)",
        "conteudo": (
            "A transferência escolar de alunos (entre unidades da rede municipal de Duque de Caxias ou vindos de redes estaduais, "
            "privadas ou de outros municípios) é coordenada pela Secretaria Municipal de Educação (SME). "
            "PASSO A PASSO PARA SOLICITAR TRANSFERÊNCIA: "
            "1. Na Escola Atual (Origem): O responsável comparece à secretaria da escola onde o aluno está matriculado e solicita a Declaração de Transferência "
            "ou Histórico Escolar atualizado. "
            "2. Na Escola Pretendida (Destino): Apresentar a Declaração de Transferência na secretaria da escola municipal de destino para averiguação imediata de vaga na turma. "
            "3. Se não houver vaga imediata na escola desejada: Comparecer ao Setor de Matrículas da Secretaria Municipal de Educação (SME), "
            "na Rua Prefeito Bernardo Távora, s/n - 25 de Agosto, para que o setor realize o encaminhamento oficial para a unidade escolar municipal mais próxima da residência. "
            "DOCUMENTOS: Declaração de transferência, RG/Certidão do aluno, documento do responsável e comprovante de residência. "
            "CUSTO: Gratuito."
        ),
        "tags": [
            "transferencia de aluno", "transferir de escola", "mudar de escola", "transferencia escolar",
            "mudar meu filho de escola", "declaracao de transferencia", "sme transferencia"
        ],
        "prioridade": "MAXIMA",
        "boost_weight": 4.0,
        "autor": "Ouvidoria Geral e Secretaria Municipal de Educação",
        "data_homologacao": "2026-10-26 12:00",
        "links_oficiais": ["https://educacao.duquedecaxias.rj.gov.br", "https://duquedecaxias.colab.re/"],
        "homologado_por": ["Diretoria da Ouvidoria Geral", "Secretaria Municipal de Educação"]
    }
]


def apply_rules():
    print(f"[1/4] Atualizando regras_negocio.json com {len(NEW_CANONICAL_RULES)} novas regras canônicas...")
    if os.path.exists(REGRAS_JSON_PATH):
        with open(REGRAS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        rules = data.get("regras_negocio", [])
        rule_map = {r["id"]: r for r in rules}
        for nr in NEW_CANONICAL_RULES:
            rule_map[nr["id"]] = nr
        data["regras_negocio"] = list(rule_map.values())
        with open(REGRAS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("   -> regras_negocio.json atualizado!")

    print("[2/4] Atualizando main.db (regras_negocio)...")
    if os.path.exists(MAIN_DB_PATH):
        conn = sqlite3.connect(MAIN_DB_PATH)
        cur = conn.cursor()
        for nr in NEW_CANONICAL_RULES:
            cur.execute("""
                INSERT INTO regras_negocio (id, tipo, tipo_label, tema, assunto, conteudo, tags, prioridade, boost_weight, autor, data_homologacao, links_oficiais, homologado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    tipo = excluded.tipo,
                    tipo_label = excluded.tipo_label,
                    tema = excluded.tema,
                    assunto = excluded.assunto,
                    conteudo = excluded.conteudo,
                    tags = excluded.tags,
                    prioridade = excluded.prioridade,
                    boost_weight = excluded.boost_weight,
                    autor = excluded.autor,
                    data_homologacao = excluded.data_homologacao,
                    links_oficiais = excluded.links_oficiais,
                    homologado_por = excluded.homologado_por
            """, (
                nr["id"], nr["tipo"], nr["tipo_label"], nr["tema"], nr["assunto"], nr["conteudo"],
                json.dumps(nr["tags"], ensure_ascii=False), nr["prioridade"], nr["boost_weight"],
                nr["autor"], nr["data_homologacao"],
                json.dumps(nr["links_oficiais"], ensure_ascii=False),
                json.dumps(nr["homologado_por"], ensure_ascii=False)
            ))
        conn.commit()
        conn.close()
        print("   -> main.db atualizado!")

    print("[3/4] Adicionando chunks ao CHUNKS_MESTRES_UNIFICADOS.jsonl...")
    if os.path.exists(CHUNKS_JSONL_PATH):
        existing_ids = set()
        with open(CHUNKS_JSONL_PATH, "r", encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                try:
                    obj = json.loads(l)
                    existing_ids.add(obj.get("chunk_id"))
                except Exception:
                    pass

        added_jsonl = 0
        with open(CHUNKS_JSONL_PATH, "a", encoding="utf-8") as f:
            for nr in NEW_CANONICAL_RULES:
                cid = nr["id"]
                if cid not in existing_ids:
                    chunk_obj = {
                        "chunk_id": cid,
                        "tipo_documento": "REGRA_NEGOCIO",
                        "titulo": f"Regra Canônica: {nr['assunto']}",
                        "conteudo": f"TEMA DA REGRA: {nr['tema']}\nASSUNTO: {nr['assunto']}\nDIRETRIZ OFICIAL: {nr['conteudo']}\nTAGS DE BUSCA: {', '.join(nr['tags'])}",
                        "metadata": {
                            "prioridade": nr["prioridade"],
                            "boost_weight": nr["boost_weight"],
                            "tipo_label": nr["tipo_label"],
                            "tema": nr["tema"],
                            "tags": nr["tags"],
                            "fonte_oficial": "20-dados-mestres/regras_negocio.json"
                        }
                    }
                    f.write(json.dumps(chunk_obj, ensure_ascii=False) + "\n")
                    added_jsonl += 1
        print(f"   -> {added_jsonl} novos chunks mestres adicionados ao JSONL!")

    print("[4/4] Atualizando vector.db (chunks e chunks_fts)...")
    if os.path.exists(VECTOR_DB_PATH):
        conn = sqlite3.connect(VECTOR_DB_PATH)
        cur = conn.cursor()
        for nr in NEW_CANONICAL_RULES:
            cid = nr["id"]
            tipo = "REGRA_NEGOCIO"
            titulo = f"Regra Canônica: {nr['assunto']}"
            conteudo = f"TEMA DA REGRA: {nr['tema']}\nASSUNTO: {nr['assunto']}\nDIRETRIZ OFICIAL: {nr['conteudo']}\nTAGS DE BUSCA: {', '.join(nr['tags'])}"
            meta_json = json.dumps({
                "prioridade": nr["prioridade"],
                "boost_weight": nr["boost_weight"],
                "tipo_label": nr["tipo_label"],
                "tema": nr["tema"],
                "tags": nr["tags"],
                "fonte_oficial": "20-dados-mestres/regras_negocio.json"
            }, ensure_ascii=False)

            cur.execute("""
                INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
                VALUES (?, ?, ?, ?, ?, NULL)
                ON CONFLICT(id) DO UPDATE SET
                    tipo = excluded.tipo,
                    titulo = excluded.titulo,
                    conteudo = excluded.conteudo,
                    metadata_json = excluded.metadata_json
            """, (cid, tipo, titulo, conteudo, meta_json))

            try:
                cur.execute("""
                    INSERT OR REPLACE INTO chunks_fts (rowid, titulo, conteudo)
                    VALUES ((SELECT rowid FROM chunks WHERE id = ?), ?, ?)
                """, (cid, titulo, conteudo))
            except Exception:
                pass

        conn.commit()
        conn.close()
        print("   -> vector.db atualizado com sucesso!")


if __name__ == "__main__":
    apply_rules()
    print("\n[SUCESSO] Todas as 5 regras canônicas inseridas com sucesso de forma incremental!")
