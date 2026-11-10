"""
Atualização dos chunks mestres e base vetorial (vector.db) com a nova estrutura de secretarias:
- SMG (Governo - sem Ouvidoria Geral)
- SMCT (Cultura e Turismo)
- SMEL (Esporte e Lazer)
- SMCSRPTER (Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral)
"""

import json
import sqlite3
import os
import sys

# Garante path para importar GeminiClient
sys.path.insert(0, os.path.abspath("."))
from utils.gemini_client import GeminiClient

def run_update():
    jsonl_path = "data/knowledge/bancoduqueia/pipeline_storage/CHUNKS_MESTRES_UNIFICADOS.jsonl"
    db_path = "data/db/vector.db"

    # Definição dos 4 chunks oficiais
    chunk_gov = {
        "chunk_id": "secretaria_00721",
        "tipo_documento": "ESTRUTURA_ADMINISTRATIVA",
        "titulo": "Secretaria: Secretaria Municipal de Governo (SMG)",
        "conteudo": (
            "ÓRGÃO MUNICIPAL: Secretaria Municipal de Governo (SMG)\n"
            "CATEGORIA: Gestão Institucional e Articulação Política\n"
            "TITULAR / RESPONSÁVEL LEGAL: Secretária Municipal de Governo (Luciana R. Bertella)\n"
            "SEDE OFICIAL: Alameda Dona Mariana, 91 - 25 de Agosto, Duque de Caxias - RJ, 25075-010\n"
            "TELEFONE DE CONTATO: (21) 2672-8801\n"
            "E-MAIL OFICIAL: governo@duquedecaxias.rj.gov.br\n"
            "HORÁRIO DE ATENDIMENTO AO PÚBLICO: Segunda a Sexta, das 08h às 17h\n"
            "SINÔNIMOS / ALIASES: Secretaria de Governo, Gabinete do Prefeito, SMG, Articulação Política, "
            "Relações Parlamentares, Gestão de Atos Oficiais, secretaria-governo"
        ),
        "metadata": {
            "sigla": "SMG",
            "secretaria_id": "secretaria-governo",
            "categoria": "Gestão Institucional e Articulação Política",
            "aliases": [
                "Secretaria de Governo", "Gabinete do Prefeito", "SMG",
                "Articulação Política", "Relações Parlamentares", "Gestão de Atos Oficiais", "secretaria-governo"
            ],
            "fonte_oficial": "20-dados-mestres/secretarias.json"
        }
    }

    chunk_cultura = {
        "chunk_id": "secretaria_00727",
        "tipo_documento": "ESTRUTURA_ADMINISTRATIVA",
        "titulo": "Secretaria: Secretaria Municipal de Cultura e Turismo (SMCT)",
        "conteudo": (
            "ÓRGÃO MUNICIPAL: Secretaria Municipal de Cultura e Turismo (SMCT)\n"
            "CATEGORIA: Cultura e Turismo\n"
            "TITULAR / RESPONSÁVEL LEGAL: Secretário Municipal de Cultura e Turismo (Aroldo Cândido de Brito)\n"
            "SEDE OFICIAL: Praça Humaitá, s/n - 25 de Agosto, Duque de Caxias - RJ, 25075-000\n"
            "TELEFONE DE CONTATO: (21) 2672-8890 / (21) 2771-8682\n"
            "E-MAIL OFICIAL: cultura@duquedecaxias.rj.gov.br\n"
            "HORÁRIO DE ATENDIMENTO AO PÚBLICO: Segunda a Sexta, das 09h às 17h\n"
            "SINÔNIMOS / ALIASES: Secretaria de Cultura, Cultura e Turismo, SMCT, Teatro Raul Cortez, "
            "Biblioteca Leonel Brizola, Teatro Armando Melo, Museu Histórico da Taquara, "
            "Museu Vivo do São Bento, Centro Cultural Niemeyer, secretaria-cultura-turismo"
        ),
        "metadata": {
            "sigla": "SMCT",
            "secretaria_id": "secretaria-cultura-turismo",
            "categoria": "Cultura e Turismo",
            "aliases": [
                "Secretaria de Cultura", "Cultura e Turismo", "SMCT",
                "Teatro Raul Cortez", "Biblioteca Leonel Brizola", "Teatro Armando Melo",
                "Museu Histórico da Taquara", "Museu Vivo do São Bento", "Centro Cultural Niemeyer",
                "secretaria-cultura-turismo"
            ],
            "fonte_oficial": "20-dados-mestres/secretarias.json"
        }
    }

    chunk_esporte = {
        "chunk_id": "secretaria_00728",
        "tipo_documento": "ESTRUTURA_ADMINISTRATIVA",
        "titulo": "Secretaria: Secretaria Municipal de Esporte e Lazer (SMEL)",
        "conteudo": (
            "ÓRGÃO MUNICIPAL: Secretaria Municipal de Esporte e Lazer (SMEL)\n"
            "CATEGORIA: Esporte e Lazer\n"
            "TITULAR / RESPONSÁVEL LEGAL: Secretário Municipal de Esporte e Lazer (Leandro Guimarães)\n"
            "SEDE OFICIAL: Rua Garibaldi, s/n (Vila Olímpica) - Jardim Vinte e Cinco de Agosto, Duque de Caxias - RJ, 25075-080\n"
            "TELEFONE DE CONTATO: (21) 2652-7428\n"
            "E-MAIL OFICIAL: smel@duquedecaxias.rj.gov.br\n"
            "HORÁRIO DE ATENDIMENTO AO PÚBLICO: Segunda a Sexta, das 08h às 17h\n"
            "SINÔNIMOS / ALIASES: Secretaria de Esporte, Esporte e Lazer, SMEL, Vila Olímpica, "
            "Vila Olímpica de Duque de Caxias, Jogos Estudantis Duque-Caxienses, Polos Esportivos, "
            "Natação, Hidroginástica, Lutas, Ginástica, secretaria-esporte-lazer"
        ),
        "metadata": {
            "sigla": "SMEL",
            "secretaria_id": "secretaria-esporte-lazer",
            "categoria": "Esporte e Lazer",
            "aliases": [
                "Secretaria de Esporte", "Esporte e Lazer", "SMEL", "Vila Olímpica",
                "Vila Olímpica de Duque de Caxias", "Jogos Estudantis Duque-Caxienses",
                "Polos Esportivos", "secretaria-esporte-lazer"
            ],
            "fonte_oficial": "20-dados-mestres/secretarias.json"
        }
    }

    chunk_comunicacao = {
        "chunk_id": "secretaria_00729",
        "tipo_documento": "ESTRUTURA_ADMINISTRATIVA",
        "titulo": "Secretaria: Secretaria Municipal de Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral (SMCSRPTER)",
        "conteudo": (
            "ÓRGÃO MUNICIPAL: Secretaria Municipal de Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral (SMCSRPTER)\n"
            "CATEGORIA: Comunicação, Emprego e Ouvidoria Geral\n"
            "TITULAR / RESPONSÁVEL LEGAL: Secretário(a) Municipal de Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral\n"
            "SEDE OFICIAL: Alameda Dona Mariana, 91 - 25 de Agosto, Duque de Caxias - RJ, 25075-010\n"
            "TELEFONE DE CONTATO: (21) 2652-3835 / WhatsApp Oficial da Ouvidoria: (21) 99824-5903\n"
            "E-MAIL OFICIAL: ouvidoria@duquedecaxias.rj.gov.br / imprensa@duquedecaxias.rj.gov.br\n"
            "HORÁRIO DE ATENDIMENTO AO PÚBLICO: Segunda a Sexta, das 08h às 17h\n"
            "SINÔNIMOS / ALIASES: SMCSRPTER, Secretaria de Comunicação, Comunicação Social, Relações Públicas, "
            "Trabalho Emprego e Renda, Secretaria de Trabalho, SINE Municipal, Carreta do Trabalhador, "
            "Ouvidoria Geral, Ouvidoria, Ouvidoria Geral do Município, OGM, Colab, Reclamações, Denúncias, Elogios, "
            "secretaria-comunicacao-trabalho-ouvidoria"
        ),
        "metadata": {
            "sigla": "SMCSRPTER",
            "secretaria_id": "secretaria-comunicacao-trabalho-ouvidoria",
            "categoria": "Comunicação, Emprego e Ouvidoria Geral",
            "aliases": [
                "SMCSRPTER", "Secretaria de Comunicação", "Comunicação Social", "Relações Públicas",
                "Trabalho Emprego e Renda", "Secretaria de Trabalho", "SINE Municipal", "Carreta do Trabalhador",
                "Ouvidoria Geral", "Ouvidoria", "Ouvidoria Geral do Município", "OGM", "Colab",
                "secretaria-comunicacao-trabalho-ouvidoria"
            ],
            "fonte_oficial": "20-dados-mestres/secretarias.json"
        }
    }

    target_chunks = {
        "secretaria_00721": chunk_gov,
        "secretaria_00727": chunk_cultura,
        "secretaria_00728": chunk_esporte,
        "secretaria_00729": chunk_comunicacao
    }

    # 1. Atualizar CHUNKS_MESTRES_UNIFICADOS.jsonl
    print("[JSONL] Atualizando CHUNKS_MESTRES_UNIFICADOS.jsonl...")
    lines = []
    found_ids = set()
    if os.path.exists(jsonl_path):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    obj = json.loads(line_str)
                    cid = obj.get("chunk_id")
                    if cid in target_chunks:
                        lines.append(json.dumps(target_chunks[cid], ensure_ascii=False) + "\n")
                        found_ids.add(cid)
                    else:
                        lines.append(line_str + "\n")
                except Exception:
                    lines.append(line_str + "\n")

    # Adicionar os que faltam (ex: 00728 e 00729)
    for cid, cdata in target_chunks.items():
        if cid not in found_ids:
            lines.append(json.dumps(cdata, ensure_ascii=False) + "\n")
            print(f"[JSONL] Adicionado novo chunk: {cid}")

    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[JSONL] Sucesso! Total de linhas: {len(lines)}")

    # 2. Gerar Embeddings usando GeminiClient
    print("[EMBEDDINGS] Gerando embeddings oficiais com GeminiClient (gemini-embedding-2)...")
    client = GeminiClient()
    embeddings_map = {}
    for cid, cdata in target_chunks.items():
        text_to_embed = f"{cdata['titulo']}\n{cdata['conteudo']}"
        try:
            emb = client.get_embedding(text_to_embed)
            embeddings_map[cid] = emb
            print(f"  -> {cid} ({len(emb)} dimensões)")
        except Exception as e:
            print(f"  -> Erro gerando embedding para {cid}: {e}")
            embeddings_map[cid] = []

    # 3. Atualizar vector.db
    print("[VECTOR.DB] Atualizando tabelas 'chunks' e 'duque_ia_chunks'...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for cid, cdata in target_chunks.items():
        emb_list = embeddings_map.get(cid, [])
        emb_json = json.dumps(emb_list)
        metadata_str = json.dumps(cdata["metadata"], ensure_ascii=False)
        keywords_str = json.dumps(cdata["metadata"]["aliases"], ensure_ascii=False)

        # A) Tabela chunks
        exists_chunk = c.execute("SELECT 1 FROM chunks WHERE id = ?", (cid,)).fetchone()
        if exists_chunk:
            c.execute(
                """UPDATE chunks 
                   SET tipo = ?, titulo = ?, conteudo = ?, metadata_json = ?
                   WHERE id = ?""",
                (cdata["tipo_documento"], cdata["titulo"], cdata["conteudo"], metadata_str, cid)
            )
        else:
            c.execute(
                """INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (cid, cdata["tipo_documento"], cdata["titulo"], cdata["conteudo"], metadata_str)
            )

        # B) Tabela chunks_fts (Full-text search)
        try:
            c.execute("DELETE FROM chunks_fts WHERE id = ?", (cid,))
            c.execute(
                "INSERT INTO chunks_fts (id, tipo, titulo, conteudo) VALUES (?, ?, ?, ?)",
                (cid, cdata["tipo_documento"], cdata["titulo"], cdata["conteudo"])
            )
        except Exception as e:
            print(f"  [FTS Warning] {e}")

        # C) Tabela duque_ia_chunks
        exists_d = c.execute("SELECT id FROM duque_ia_chunks WHERE source = ?", (cid,)).fetchone()
        if exists_d:
            c.execute(
                """UPDATE duque_ia_chunks 
                   SET category = ?, content = ?, embedding = ?, metadata = ?, keywords = ?
                   WHERE source = ?""",
                ("estrutura_administrativa", cdata["conteudo"], emb_json, metadata_str, keywords_str, cid)
            )
        else:
            c.execute(
                """INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cid, "estrutura_administrativa", cdata["conteudo"], emb_json, metadata_str, keywords_str)
            )
        print(f"[VECTOR.DB] Chunk {cid} atualizado/inserido com sucesso.")

    conn.commit()
    conn.close()
    print("[VECTOR.DB] Base vetorial atualizada com sucesso!")

if __name__ == "__main__":
    run_update()
