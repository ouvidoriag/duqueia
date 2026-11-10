"""
add_tarifa_zero_canonical_rule.py — DUQUE IA
============================================
Adiciona de forma incremental a regra canônica oficial de gratuidade
do Programa Tarifa Zero (Decreto Municipal nº 8.120/2023).
Respeita a Regra 6 do projeto (inserção puramente incremental).
"""

import os
import json
import sqlite3

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

REGRAS_JSON_PATH = os.path.join(_PROJECT_ROOT, "data", "knowledge", "bancoduqueia", "dados_mestres", "regras_negocio.json")
MAIN_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "db", "main.db")
CHUNKS_JSONL_PATH = os.path.join(_PROJECT_ROOT, "data", "knowledge", "bancoduqueia", "pipeline_storage", "CHUNKS_MESTRES_UNIFICADOS.jsonl")
VECTOR_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")

TARIFA_ZERO_RULE = {
    "id": "regra_canon_tarifa_zero_transporte_gratuito",
    "tipo": "REGRA_DE_NEGOCIO",
    "tipo_label": "Programa Tarifa Zero - Ônibus Municipais Gratuitos",
    "tema": "Transportes, Serviços Públicos e Mobilidade Urbana",
    "assunto": "Gratuidade da Tarifa dos Ônibus Municipais do Programa Tarifa Zero (Decreto nº 8.120/2023)",
    "conteudo": (
        "O Programa Tarifa Zero de Duque de Caxias, instituído e regulamentado pelo Decreto Municipal nº 8.120/2023, "
        "garante transporte público municipal inteiramente GRATUITO a toda a população em suas linhas circulares. "
        "O valor da passagem é de R$ 0,00 (ZERO REAIS). Não há cobrança de tarifa, bilhetagem eletrônica paga nem exigência "
        "de pagamento em dinheiro para embarcar nos coletivos do programa. Os ônibus operam sob gestão da Secretaria Municipal "
        "de Transportes e Serviços Públicos (SMTSP) e interligam bairros e distritos da cidade, tais como: "
        "Capivari x Figueira, Aviário x Xerém, Parque Eldorado x Xerém (via Cantão), Vila Operária x Hosp. Daniel Lipp, "
        "Vila Maria Helena x Parque Equitativa, entre outros. Para dúvidas, itinerários ou horários, o munícipe pode consultar "
        "a Ouvidoria Geral pelo Colab ou telefone (21) 2652-3835."
    ),
    "tags": [
        "tarifa zero", "onibus gratuito", "preco da passagem", "valor da passagem",
        "quanto custa o onibus", "tarifa", "passagem municipal", "decreto 8120",
        "transporte publico gratuito", "smtsp", "linhas tarifa zero", "onibus de graca"
    ],
    "prioridade": "MAXIMA",
    "boost_weight": 3.5,
    "autor": "Ouvidoria Geral e Secretaria Municipal de Transportes e Serviços Públicos",
    "data_homologacao": "2026-10-26 10:00",
    "links_oficiais": ["https://duquedecaxias.rj.gov.br", "https://duquedecaxias.colab.re/"],
    "homologado_por": ["Diretoria da Ouvidoria Geral", "Secretaria Municipal de Transportes e Serviços Públicos"]
}


def update_all():
    print("[1/4] Atualizando regras_negocio.json...")
    if os.path.exists(REGRAS_JSON_PATH):
        with open(REGRAS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        rules = data.get("regras_negocio", [])
        idx = next((i for i, r in enumerate(rules) if r.get("id") == TARIFA_ZERO_RULE["id"]), None)
        if idx is not None:
            rules[idx] = TARIFA_ZERO_RULE
        else:
            rules.append(TARIFA_ZERO_RULE)
        data["regras_negocio"] = rules
        with open(REGRAS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("   -> regras_negocio.json atualizado com sucesso!")

    print("[2/4] Atualizando main.db (regras_negocio)...")
    if os.path.exists(MAIN_DB_PATH):
        conn = sqlite3.connect(MAIN_DB_PATH)
        cur = conn.cursor()
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
            TARIFA_ZERO_RULE["id"],
            TARIFA_ZERO_RULE["tipo"],
            TARIFA_ZERO_RULE["tipo_label"],
            TARIFA_ZERO_RULE["tema"],
            TARIFA_ZERO_RULE["assunto"],
            TARIFA_ZERO_RULE["conteudo"],
            json.dumps(TARIFA_ZERO_RULE["tags"], ensure_ascii=False),
            TARIFA_ZERO_RULE["prioridade"],
            TARIFA_ZERO_RULE["boost_weight"],
            TARIFA_ZERO_RULE["autor"],
            TARIFA_ZERO_RULE["data_homologacao"],
            json.dumps(TARIFA_ZERO_RULE["links_oficiais"], ensure_ascii=False),
            json.dumps(TARIFA_ZERO_RULE["homologado_por"], ensure_ascii=False)
        ))
        conn.commit()
        conn.close()
        print("   -> main.db atualizado com sucesso!")

    print("[3/4] Adicionando chunk mestre ao CHUNKS_MESTRES_UNIFICADOS.jsonl...")
    chunk_obj = {
        "chunk_id": TARIFA_ZERO_RULE["id"],
        "tipo_documento": "REGRA_NEGOCIO",
        "titulo": f"Regra Canônica: {TARIFA_ZERO_RULE['assunto']}",
        "conteudo": f"TEMA DA REGRA: {TARIFA_ZERO_RULE['tema']}\nASSUNTO: {TARIFA_ZERO_RULE['assunto']}\nDIRETRIZ OFICIAL: {TARIFA_ZERO_RULE['conteudo']}\nTAGS DE BUSCA: {', '.join(TARIFA_ZERO_RULE['tags'])}",
        "metadata": {
            "prioridade": TARIFA_ZERO_RULE["prioridade"],
            "boost_weight": TARIFA_ZERO_RULE["boost_weight"],
            "tipo_label": TARIFA_ZERO_RULE["tipo_label"],
            "tema": TARIFA_ZERO_RULE["tema"],
            "tags": TARIFA_ZERO_RULE["tags"],
            "fonte_oficial": "20-dados-mestres/regras_negocio.json"
        }
    }
    if os.path.exists(CHUNKS_JSONL_PATH):
        existing = False
        with open(CHUNKS_JSONL_PATH, "r", encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                try:
                    obj = json.loads(l)
                    if obj.get("chunk_id") == TARIFA_ZERO_RULE["id"]:
                        existing = True
                        break
                except Exception:
                    pass
        if not existing:
            with open(CHUNKS_JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(chunk_obj, ensure_ascii=False) + "\n")
            print("   -> CHUNKS_MESTRES_UNIFICADOS.jsonl incrementado!")

    print("[4/4] Inserindo incrementalmente no vector.db...")
    if os.path.exists(VECTOR_DB_PATH):
        conn = sqlite3.connect(VECTOR_DB_PATH)
        cur = conn.cursor()
        cid = chunk_obj["chunk_id"]
        tipo = chunk_obj["tipo_documento"]
        titulo = chunk_obj["titulo"]
        conteudo = chunk_obj["conteudo"]
        meta_json = json.dumps(chunk_obj["metadata"], ensure_ascii=False)

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
        except Exception as e:
            print("   (chunks_fts info):", e)

        conn.commit()
        conn.close()
        print("   -> vector.db atualizado com sucesso!")


if __name__ == "__main__":
    update_all()
    print("\n[OK] Regra canônica do Tarifa Zero inserida incrementalmente!")
