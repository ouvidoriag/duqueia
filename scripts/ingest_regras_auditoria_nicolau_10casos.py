import sqlite3
import json
import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from utils.gemini_client import GeminiClient

MAIN_DB = os.path.join(_PROJECT_ROOT, "data", "db", "main.db")
VECTOR_DB = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")

RULES = [
    {
        "id": "regra_canon_concessionaria_aguas_do_rio_desabastecimento",
        "tema": "Concessionárias de Serviços Públicos / Saneamento e Abastecimento de Água",
        "assunto": "Falta Crônica de Água, Desabastecimento, Concessionária Águas do Rio e AGENERSA",
        "conteudo": """DIRETRIZ DE GOVERNANÇA: DESABASTECIMENTO CRÔNICO DE ÁGUA, CONCESSIONÁRIA ÁGUAS DO RIO E PAPEL DA PREFEITURA

1. RESPONSABILIDADE OPERACIONAL DA CONCESSIONÁRIA:
- O abastecimento de água encanada e o tratamento de esgoto em Duque de Caxias são operados pela concessionária privada Águas do Rio sob contrato de concessão estadual.
- Canais de Atendimento da Concessionária: Telefone 0800 195 0 195 | WhatsApp Oficial (21) 97211-8064 | Site: aguasdorio.com.br.

2. FISCALIZAÇÃO E REGULAÇÃO ESTADUAL (AGENERSA):
- A agência reguladora estadual responsável pela fiscalização do cumprimento das metas contratuais e punição da concessionária é a AGENERSA (Agência Reguladora de Energia e Saneamento Básico do Estado do Rio de Janeiro).
- Ouvidoria da AGENERSA: Telefone gratuito 0800 024 9040 | Site: agenersa.rj.gov.br.

3. ATUAÇÃO DA PREFEITURA DE DUQUE DE CAXIAS (MEDIAÇÃO E DEFESA DO CIDADÃO):
- Quando uma rua, trecho ou bairro (como Jardim Primavera, Xerém, Imbariê, etc.) sofre desabastecimento crônico, corte injustificado ou descumprimento de prazos pela concessionária, a Prefeitura atua cobrando e notificando formalmente a empresa através da Ouvidoria Geral do Município e do PROCON Caxias.
- Como Formalizar a Reclamação / Denúncia:
  * Pelo aplicativo ou portal Colab: https://duquedecaxias.colab.re na categoria Concessionárias > Falta de Água / Esgoto.
  * Ouvidoria Geral de Duque de Caxias: Telefone (21) 2652-3835 | WhatsApp (21) 99824-5903 | E-mail: ouvidoria@duquedecaxias.rj.gov.br.
  * PROCON Duque de Caxias: Telefone (21) 2672-6668.
- A Prefeitura reúne as demandas coletivas para exigir providências imediatas da concessionária e ingressar com representações perante a AGENERSA e o Ministério Público.""",
        "tags": ["agua", "aguas do rio", "falta de agua", "desabastecimento", "concessionaria", "agenersa", "jardim primavera", "ouvidoria", "colab", "procon"],
        "boost_weight": 2.5
    },
    {
        "id": "regra_canon_lava_jato_ordem_publica_desobstrucao_calcada",
        "tema": "Ordem Pública, Fiscalização de Posturas e Segurança do Cidadão",
        "assunto": "Fiscalização de Calçadas, Lava-Jatos Irregulares, Cones na Rua e Unidades Móveis da Ordem Pública",
        "conteudo": """DIRETRIZ DE GOVERNANÇA: DESOBSTRUÇÃO DE CALÇADAS, LAVA-JATOS EM VIA PÚBLICA E ORDEM PÚBLICA

1. FISCALIZAÇÃO DE CALÇADAS E OBSTÁCULOS NA RUA:
- A ocupação indevida de calçadas e vias públicas por lava-jatos, cones, cavaletes, mangueiras, correntes ou carros estacionados no passeio público viola o Código de Posturas do Município e o Código de Trânsito Brasileiro.
- Órgão de Atuação Imediata: As unidades móveis (viaturas de ronda) da Superintendência de Ordem Pública (SUOP) e Guarda Municipal atuam na fiscalização ostensiva, apreensão de materiais e desobstrução física imediata da via pública.
- A Secretaria Municipal de Urbanismo e Habitação (SMUH / Posturas) e a Secretaria Municipal de Meio Ambiente (SMMA) atuam na fiscalização de alvará edilício e descarte de produtos químicos/efluentes.

2. COMO REGISTRAR A DENÚNCIA:
- Pelo aplicativo oficial Colab: https://duquedecaxias.colab.re (ou portal Colab), selecionando a categoria Ordem Pública / Fiscalização de Posturas ou Urbanismo.
- Ouvidoria Geral de Duque de Caxias: Telefone (21) 2652-3835 | WhatsApp (21) 99824-5903.
- Informações úteis: Forneça o endereço completo com ponto de referência, horários de funcionamento e fotos/vídeos dos obstáculos na rua. O denunciante pode optar pelo sigilo de seus dados.

3. AMEAÇAS E SEGURANÇA PESSOAL:
- Ameaças, intimidações ou agressões verbais cometidas por proprietários ou funcionários de estabelecimentos configuram crime previsto no Código Penal e extrapolam a competência administrativa da Prefeitura.
- Em caso de flagrante ou ameaça iminente: Ligue imediatamente para a Polícia Militar pelo 190.
- Registro da Ocorrência: O cidadão deve registrar Boletim de Ocorrência (BO) na Delegacia da Polícia Civil do município ou pelo portal da Delegacia Online (delegaciaonline.pcerj.rj.gov.br).""",
        "tags": ["lava jato", "calcada", "obstaculos", "cones", "ordem publica", "suop", "unidades moveis", "ameaca", "190", "colab", "policia civil"],
        "boost_weight": 2.5
    },
    {
        "id": "regra_canon_fiscalizacao_alvara_terceiros_sigilo_fiscal",
        "tema": "Fazenda Municipal / Fiscalização de Alvará e Sigilo Fiscal",
        "assunto": "Sigilo Fiscal, Proibição de Consulta Balcão de Alvará de Terceiros e Denúncia de Comércio Sem Alvará",
        "conteudo": """DIRETRIZ DE GOVERNANÇA: SIGILO FISCAL, VERIFICAÇÃO DE ALVARÁ DE TERCEIROS E CANAIS OFICIAIS

1. PROIBIÇÃO DE CONSULTA BALCÃO DE ALVARÁ DE TERCEIROS (SIGILO FISCAL):
- A Secretaria Municipal de Fazenda (SMF) NÃO fornece dados cadastrais, fichas fiscais ou certidões de alvará de estabelecimentos terceiros para particulares no balcão presencial ou pelo Portal do Contribuinte, por força do Sigilo Fiscal previsto no Artigo 198 do Código Tributário Nacional (CTN).
- O cidadão comum não faz "pesquisa avulsa no balcão da Fazenda" sobre alvará alheio.

2. COMO PROCEDER DIANTE DE SUSPEITA DE COMÉRCIO SEM ALVARÁ:
- Se o morador suspeita de comércio, oficina ou lava-jato funcionando irregularmente ou sem alvará, a providência cabível é registrar uma DENÚNCIA DE ESTABELECIMENTO IRREGULAR / SEM ALVARÁ.
- Canais Oficiais: Aplicativo Colab (https://duquedecaxias.colab.re) na categoria Fazenda / Fiscalização de Alvará ou Ordem Pública, ou pela Ouvidoria Geral (Telefone: (21) 2652-3835 | WhatsApp: (21) 99824-5903).
- A fiscalização tributária da Prefeitura realizará a inspeção presencial in loco com poder de polícia, exigindo a exibição do Alvará de Funcionamento e aplicando notificação, multa ou interdição caso irregular.

3. ACESSO A DOCUMENTOS PÚBLICOS E PROCESSOS (e-SIC / LAI):
- Para requisições formais de documentos, contratos públicos ou informações coletivas da administração, o canal legal exclusivo é o e-SIC / Lei de Acesso à Informação através do Portal Cidadão: https://portal.duquedecaxias.rj.gov.br ou https://duquedecaxias.rj.gov.br/e-sic (prazo legal de até 20 dias corridos).""",
        "tags": ["alvara", "consultar alvara", "alvara vizinho", "comercio sem alvara", "sigilo fiscal", "fazenda", "denuncia", "colab", "e-sic", "portal cidadao"],
        "boost_weight": 2.5
    }
]

def main():
    gemini = GeminiClient()
    conn_main = sqlite3.connect(MAIN_DB)
    cur_main = conn_main.cursor()
    conn_vec = sqlite3.connect(VECTOR_DB)
    cur_vec = conn_vec.cursor()

    for r in RULES:
        rid = r["id"]
        tema = r["tema"]
        assunto = r["assunto"]
        conteudo = r["conteudo"]
        tags = r["tags"]
        boost = r["boost_weight"]

        print(f"\n--- Processando {rid} ---")
        
        # 1. main.db
        cur_main.execute("DELETE FROM regras_negocio WHERE id = ?", (rid,))
        cur_main.execute("""
            INSERT INTO regras_negocio (
                id, tipo, tipo_label, tema, assunto, conteudo, tags, prioridade, boost_weight,
                autor, data_homologacao, links_oficiais, homologado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rid,
            "REGRA_CANONICA",
            "Regra Canônica de Governança",
            tema,
            assunto,
            conteudo,
            json.dumps(tags),
            "ALTA",
            boost,
            "Auditoria Duque IA",
            "2026-11-12",
            json.dumps(["https://duquedecaxias.colab.re", "https://portal.duquedecaxias.rj.gov.br"]),
            "Ouvidoria Geral / Gestão Municipal"
        ))
        print("Salvo em main.db.")

        # 2. Embedding 3072d
        embedding = None
        if gemini.api_keys:
            try:
                emb = gemini.get_embedding(conteudo)
                if emb and len(emb) == 3072:
                    embedding = emb
                    print("Embedding 3072d gerado.")
            except Exception as e:
                print(f"Aviso embedding: {e}")

        # 3. vector.db duque_ia_chunks
        cur_vec.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (rid,))
        meta_json = json.dumps({
            "title": assunto,
            "category": "regras_negocio",
            "source": rid,
            "boost_weight": boost
        })
        kw_json = json.dumps(tags)
        emb_json = json.dumps(embedding) if embedding else None

        cur_vec.execute("""
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rid, "regras_negocio", conteudo, emb_json, meta_json, kw_json))

        # 4. vector.db chunks e chunks_fts
        cur_vec.execute("DELETE FROM chunks WHERE id = ?", (rid,))
        cur_vec.execute("""
            INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json)
            VALUES (?, ?, ?, ?, ?)
        """, (rid, "regras_negocio", assunto, conteudo, meta_json))

        try:
            cur_vec.execute("DELETE FROM chunks_fts WHERE id = ?", (rid,))
            cur_vec.execute("""
                INSERT INTO chunks_fts (id, tipo, titulo, conteudo)
                VALUES (?, ?, ?, ?)
            """, (rid, "regras_negocio", assunto, conteudo))
        except Exception as e:
            print(f"Aviso chunks_fts: {e}")

        print("Salvo em vector.db.")

    conn_main.commit()
    conn_main.close()
    conn_vec.commit()
    conn_vec.close()
    print("\nTodas as 3 regras canônicas inseridas com sucesso!")

if __name__ == "__main__":
    main()

