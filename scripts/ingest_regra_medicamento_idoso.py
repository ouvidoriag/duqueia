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

RULE_ID = "regra_canon_falta_medicamentos_idoso_locomocao"
RULE_TEMA = "Saúde Municipal / Assistência Farmacêutica e Apoio Domiciliar a Idosos"
RULE_ASSUNTO = "Falta de Medicamentos na Rede Municipal e Atendimento a Pacientes com Restrição de Mobilidade"
RULE_CONTENT = """DIRETRIZ DE GOVERNANÇA: FALTA DE MEDICAMENTOS NA REDE MUNICIPAL E PACIENTES IDOSOS / COM DIFICULDADE DE LOCOMOÇÃO

1. PRIORIDADE ABSOLUTA - ASSISTÊNCIA À SAÚDE E APOIO DOMICILIAR:
- Para pacientes idosos, acamados ou com dificuldade de locomoção que necessitem de medicamentos de uso contínuo fornecidos pela rede municipal de Duque de Caxias, a assistência à saúde é prioritária.
- A família ou responsável deve procurar a Unidade de Saúde da Família (USF / Clínica da Família) ou UBS de referência do seu bairro.
- As equipes da Estratégia Saúde da Família (ESF) contam com Agentes Comunitários de Saúde (ACS) que realizam acompanhamento territorial e visitas domiciliares contínuas, facilitando a verificação de receitas médicas e a orientação para dispensação facilitada de medicamentos contínuos (Farmácia Básica Municipal / polos distritais).

2. CANAIS REMOTOS CONFIRMADOS (SEM DESLOCAMENTO FÍSICO):
- Para evitar deslocamentos cansativos ou desnecessários da pessoa idosa e de familiares:
  * Aplicativo e portal Colab: https://duquedecaxias.colab.re
  * WhatsApp Oficial da Ouvidoria Geral: (21) 99824-5903
  * Telefone da Ouvidoria Geral: (21) 2652-3835
  * E-mail: ouvidoria@duquedecaxias.rj.gov.br

3. REGISTRO DE RECLAMAÇÃO POR DESABASTECIMENTO NA OUVIDORIA:
- Caso o medicamento prescrito esteja em falta ou haja atraso injustificado, o munícipe pode formalizar o relato/reclamação na Ouvidoria da Saúde pelo Colab ou WhatsApp.
- NÃO EXIGÊNCIA DE DOCUMENTAÇÃO EXCESSIVA: Para relatar a falta de medicamentos na Ouvidoria, NÃO é exigida lista burocrática rígida de documentos (como comprovante de residência em nome próprio ou procuração formal). Basta informar os dados úteis para a fiscalização:
  * Nome do paciente idoso;
  * Nome e dosagem do medicamento em falta;
  * Unidade de saúde onde foi procurado;
  * Data aproximada da tentativa de retirada.
"""

def main():
    print(f"Inserindo regra em {MAIN_DB}...")
    conn_main = sqlite3.connect(MAIN_DB)
    cur_main = conn_main.cursor()
    
    cur_main.execute("DELETE FROM regras_negocio WHERE id = ?", (RULE_ID,))
    cur_main.execute("""
        INSERT INTO regras_negocio (
            id, tipo, tipo_label, tema, assunto, conteudo, tags, prioridade, boost_weight,
            autor, data_homologacao, links_oficiais, homologado_por
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        RULE_ID,
        "REGRA_CANONICA",
        "Regra Canônica de Governança",
        RULE_TEMA,
        RULE_ASSUNTO,
        RULE_CONTENT,
        json.dumps(["medicamento", "medicamentos", "idoso", "idosa", "locomocao", "remedio", "falta", "farmacia", "saude", "esf", "acs", "visita domiciliar"]),
        "ALTA",
        2.5,
        "Auditoria Duque IA",
        "2026-11-11",
        json.dumps(["https://duquedecaxias.colab.re", "https://saude.duquedecaxias.rj.gov.br"]),
        "Ouvidoria Geral / SMS"
    ))
    conn_main.commit()
    conn_main.close()
    print("Regra inserida com sucesso no main.db!")

    print(f"Vetorizando e inserindo regra em {VECTOR_DB}...")
    gemini = GeminiClient()
    embedding = None
    if gemini.api_keys:
        try:
            emb_res = gemini.get_embedding(RULE_CONTENT)
            if emb_res and len(emb_res) == 3072:
                embedding = emb_res
                print("Embedding gerado com sucesso (3072 dimensões)!")
        except Exception as e:
            print(f"Aviso ao gerar embedding: {e}")

    conn_vec = sqlite3.connect(VECTOR_DB)
    cur_vec = conn_vec.cursor()
    
    # 1. duque_ia_chunks
    cur_vec.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (RULE_ID,))
    meta_json = json.dumps({
        "title": RULE_ASSUNTO,
        "category": "regras_negocio",
        "source": RULE_ID,
        "boost_weight": 2.5
    })
    kw_json = json.dumps(["medicamento", "medicamentos", "idoso", "idosa", "locomocao", "remedio", "falta", "farmacia", "saude", "esf", "acs", "visita domiciliar"])
    emb_json = json.dumps(embedding) if embedding else None

    cur_vec.execute("""
        INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (RULE_ID, "regras_negocio", RULE_CONTENT, emb_json, meta_json, kw_json))
    
    # 2. chunks (tabela legada com FTS)
    cur_vec.execute("DELETE FROM chunks WHERE id = ?", (RULE_ID,))
    cur_vec.execute("""
        INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json)
        VALUES (?, ?, ?, ?, ?)
    """, (RULE_ID, "regras_negocio", RULE_ASSUNTO, RULE_CONTENT, meta_json))
    
    try:
        cur_vec.execute("DELETE FROM chunks_fts WHERE id = ?", (RULE_ID,))
        cur_vec.execute("""
            INSERT INTO chunks_fts (id, tipo, titulo, conteudo)
            VALUES (?, ?, ?, ?)
        """, (RULE_ID, "regras_negocio", RULE_ASSUNTO, RULE_CONTENT))
    except Exception as e:
        print(f"Aviso chunks_fts: {e}")

    conn_vec.commit()
    conn_vec.close()
    print("Regra inserida e sincronizada no vector.db com sucesso!")

if __name__ == "__main__":
    main()
