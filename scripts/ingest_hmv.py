"""
ingest_hmv.py — Ingestão do Hospital Municipal Veterinário de Duque de Caxias (HMV)
Atualiza incrementalmente:
1. main.db: regras_negocio, municipal_entities, secretaria_unidades
2. vector.db: chunks, chunks_fts, duque_ia_chunks (com embedding 3072d), chunks.vetor_blob
3. data/ontology.json
"""

import sys
import os
import json
import sqlite3
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from config.settings import DATABASE_MAIN, DATABASE_VECTOR
from utils.gemini_client import GeminiClient

gemini = GeminiClient()

HMV_RULE_ID = "regra_canon_hospital_municipal_veterinario_caxias"
HMV_TEMA = "Saúde Animal e Hospital Veterinário"
HMV_ASSUNTO = "Hospital Municipal Veterinário de Duque de Caxias (HMV) — Atendimento Gratuito, Emergência e Consultas"
HMV_TAGS = json.dumps([
    "hospital veterinario", "veterinario", "veterinaria", "veterinario gratuito",
    "emergencia veterinaria", "socorro animal", "cachorro", "gato", "pet",
    "animal doente", "animal ferido", "castracao", "jardim primavera", "hmv",
    "saude animal", "clinica veterinaria", "consulta pet", "levar cachorro"
], ensure_ascii=False)

HMV_CONTEUDO = """[DIRETRIZ DE GOVERNANÇA MÁXIMA E OBRIGATÓRIA — AUDITADO]
Tema: Saúde Animal e Hospital Veterinário
Assunto: Hospital Municipal Veterinário de Duque de Caxias (HMV) — Atendimento Gratuito, Emergência e Consultas
Prioridade: MÁXIMA (Regra Canônica de Negócio - Boost: 5.0x)
Diretriz Oficial Obrigatória:
O município de Duque de Caxias conta com o **Hospital Municipal Veterinário de Duque de Caxias (HMV)**, unidade pública municipal de saúde animal de referência que oferece atendimento 100% público e gratuito para cães e gatos de munícipes da cidade.

• **Nome Oficial:** Hospital Municipal Veterinário de Duque de Caxias (HMV)
• **Endereço Completo:** Alameda Xavier Filho, s/nº, Bairro Jardim Primavera, Duque de Caxias - RJ, CEP 25215-260 (às margens da Rodovia Washington Luiz, próximo à Prefeitura de Caxias).
• **Telefone de Contato:** (21) 2773-5500 / (21) 2676-9000
• **E-mail Institucional:** veterinario@duquedecaxias.rj.gov.br
• **Horário de Funcionamento:** Segunda a sexta-feira, das 8h às 17h.
• **Fluxo de Atendimento e Emergência:** Atendimento de urgência e emergência veterinária imediata de segunda a sexta-feira durante o horário de expediente. Consultas ambulatoriais contam com distribuição de senhas a partir das 7h30/8h.
• **Serviços Gratuitos Oferecidos:**
  - Pronto-atendimento clínico e emergência veterinária para cães e gatos;
  - Consultas com médicos veterinários clínicos e cirurgiões;
  - Cirurgias de tecidos moles e procedimentos cirúrgicos gerais;
  - Programa de castração gratuita e esterilização de animais;
  - Exames de imagem: Ultrassonografia, Raio-X digital e Ecocardiograma;
  - Exames laboratoriais: Hemograma completo e bioquímicos de sangue.
• **Documentos Obrigatórios do Tutor (Morador de Duque de Caxias):**
  1. Documento oficial de identidade com foto (RG ou CNH) do tutor;
  2. Cadastro de Pessoa Física (CPF);
  3. Comprovante de residência ATUALIZADO no município de Duque de Caxias em nome do tutor do animal.
  *(Atenção: O atendimento é exclusivo e gratuito para moradores do município de Duque de Caxias).*
• **Canais Digitais e Agendamento:**
  - Aplicativo e Portal Colab (**duquedecaxias.colab.re**) > Categoria Proteção e Saúde Animal;
  - Portal do Hospital Veterinário: **hmv.duquedecaxias.rj.gov.br**."""

def update_main_db():
    print(">>> 1. Atualizando main.db...")
    conn = sqlite3.connect(DATABASE_MAIN)
    cur = conn.cursor()

    # Inserir ou atualizar na tabela regras_negocio
    cur.execute("""
        INSERT INTO regras_negocio (id, tipo_label, tema, assunto, conteudo, tags, prioridade, boost_weight)
        VALUES (?, 'REGRA_CANONICA', ?, ?, ?, ?, 'MÁXIMA', 5.0)
        ON CONFLICT(id) DO UPDATE SET
            tema = excluded.tema,
            assunto = excluded.assunto,
            conteudo = excluded.conteudo,
            tags = excluded.tags,
            prioridade = excluded.prioridade,
            boost_weight = excluded.boost_weight;
    """, (HMV_RULE_ID, HMV_TEMA, HMV_ASSUNTO, HMV_CONTEUDO, HMV_TAGS))

    # Inserir ou atualizar na tabela municipal_entities
    cur.execute("""
        INSERT INTO municipal_entities (entity_id, entity_type, canonical_name, aliases, keywords, secretaria, active)
        VALUES (
            'HOSPITAL_MUNICIPAL_VETERINARIO',
            'saude_animal',
            'Hospital Municipal Veterinário de Duque de Caxias (HMV)',
            '["hospital veterinario", "hospital veterinario de caxias", "hospital de cachorro", "emergencia veterinaria", "pronto socorro veterinario", "hmv", "veterinario publico", "veterinario gratuito", "upa veterinaria"]',
            '["cachorro", "gato", "pet", "veterinario", "veterinaria", "emergencia", "socorro", "animal", "jardim primavera", "hmv", "consulta animal"]',
            'Secretaria Municipal de Saúde (SMS) / Secretaria Municipal de Meio Ambiente e Proteção Animal (SMMA)',
            1
        )
        ON CONFLICT(entity_id) DO UPDATE SET
            canonical_name = excluded.canonical_name,
            aliases = excluded.aliases,
            keywords = excluded.keywords,
            secretaria = excluded.secretaria,
            active = 1;
    """)

    # Atualizar unidade 422 em secretaria_unidades
    cur.execute("""
        UPDATE secretaria_unidades
        SET name = 'Hospital Municipal Veterinário de Duque de Caxias (HMV)',
            working_hours = 'Segunda a sexta-feira, das 8h às 17h (Emergência e Consultas Ambulatoriais)',
            secretaria_id = 3
        WHERE id = 422;
    """)

    conn.commit()
    conn.close()
    print("   [OK] main.db atualizado com sucesso!")

def update_vector_db():
    print(">>> 2. Atualizando vector.db...")
    conn = sqlite3.connect(DATABASE_VECTOR)
    cur = conn.cursor()

    # Inserir chunk da regra canônica na tabela chunks
    chunk_meta = json.dumps({
        "tema": HMV_TEMA,
        "assunto": HMV_ASSUNTO,
        "tags": json.loads(HMV_TAGS),
        "boost_weight": 5.0,
        "fonte_oficial": "regras_negocio"
    }, ensure_ascii=False)

    cur.execute("""
        INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json)
        VALUES (?, 'REGRA_NEGOCIO', ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            tipo = excluded.tipo,
            titulo = excluded.titulo,
            conteudo = excluded.conteudo,
            metadata_json = excluded.metadata_json;
    """, (HMV_RULE_ID, f"Regra Canônica: {HMV_ASSUNTO}", HMV_CONTEUDO, chunk_meta))

    # Atualizar equipamento_01162 em chunks
    equip_conteudo = f"""EQUIPAMENTO PÚBLICO: Hospital Municipal Veterinário de Duque de Caxias (HMV)
TIPO / CATEGORIA: Saúde Animal e Zoonoses / Hospital Municipal Veterinário
LOCALIZAÇÃO GEOGRÁFICA: Bairro Jardim Primavera — 2º Distrito, Duque de Caxias/RJ
ENDEREÇO OFICIAL: Alameda Xavier Filho, s/nº - Jardim Primavera, Duque de Caxias - RJ, CEP 25215-260 (Rodovia Washington Luiz, perto da Prefeitura)
TELEFONE DE CONTATO: (21) 2773-5500 / (21) 2676-9000
E-MAIL INSTITUCIONAL: veterinario@duquedecaxias.rj.gov.br
HORÁRIO DE FUNCIONAMENTO: Segunda a sexta-feira, das 8h às 17h (Emergência e Consultas Ambulatoriais)
COORDENADAS GPS: Lat -22.685, Lng -43.283
FINALIDADE E ATIVIDADES: Atendimento gratuito a cães e gatos de munícipes de Duque de Caxias. Emergência veterinária, socorro animal, consultas com veterinário clínico e cirurgião, cirurgias gerais, castração, raio-x, ultrassom, exames de sangue.
DOCUMENTOS NECESSÁRIOS: Identidade (RG/CNH), CPF e Comprovante de Residência no município de Duque de Caxias em nome do tutor."""

    equip_meta = json.dumps({
        "categoria": "Saúde Animal e Zoonoses",
        "secretaria_sigla": "SMS",
        "bairro": "Jardim Primavera",
        "distrito": "2º Distrito",
        "boost_weight": 5.0,
        "fonte_oficial": "20-dados-mestres/equipamentos.json"
    }, ensure_ascii=False)

    cur.execute("""
        UPDATE chunks
        SET titulo = 'Equipamento: Hospital Municipal Veterinário de Duque de Caxias (HMV) (Jardim Primavera)',
            conteudo = ?,
            metadata_json = ?
        WHERE id = 'equipamento_01162';
    """, (equip_conteudo, equip_meta))

    # Atualizar chunks_fts
    try:
        cur.execute("DELETE FROM chunks_fts WHERE id IN (?, 'equipamento_01162')", (HMV_RULE_ID,))
        cur.execute("""
            INSERT INTO chunks_fts (id, tipo, titulo, conteudo)
            VALUES (?, 'REGRA_NEGOCIO', ?, ?)
        """, (HMV_RULE_ID, f"Regra Canônica: {HMV_ASSUNTO}", HMV_CONTEUDO))
        cur.execute("""
            INSERT INTO chunks_fts (id, tipo, titulo, conteudo)
            VALUES ('equipamento_01162', 'EQUIPAMENTO_PUBLICO', 'Equipamento: Hospital Municipal Veterinário de Duque de Caxias (HMV) (Jardim Primavera)', ?)
        """, (equip_conteudo,))
    except Exception as e:
        print(f"   [AVISO FTS5] {e}")

    conn.commit()

    # Gerar Embeddings densos de 3072 dimensões via Gemini
    print("   Gerando embeddings 3072d com Gemini...")
    emb_rule = gemini.get_embedding(HMV_CONTEUDO, is_query=False)
    emb_equip = gemini.get_embedding(equip_conteudo, is_query=False)

    if emb_rule and len(emb_rule) == 3072:
        rule_blob = np.array(emb_rule, dtype=np.float32).tobytes()
        cur.execute("UPDATE chunks SET vetor_blob = ? WHERE id = ?", (rule_blob, HMV_RULE_ID))
        
        # Inserir em duque_ia_chunks
        cur.execute("""
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, 'regra_negocio', ?, ?, ?, ?)
        """, (
            HMV_RULE_ID,
            HMV_CONTEUDO,
            json.dumps(emb_rule),
            chunk_meta,
            HMV_TAGS
        ))
        print("   [OK] Embedding da regra inserido em duque_ia_chunks e chunks.vetor_blob!")

    if emb_equip and len(emb_equip) == 3072:
        equip_blob = np.array(emb_equip, dtype=np.float32).tobytes()
        cur.execute("UPDATE chunks SET vetor_blob = ? WHERE id = 'equipamento_01162'", (equip_blob,))
        
        # Atualizar em duque_ia_chunks onde source = 'equipamento_01162'
        cur.execute("""
            UPDATE duque_ia_chunks
            SET content = ?,
                embedding = ?,
                metadata = ?,
                keywords = ?
            WHERE source = 'equipamento_01162';
        """, (
            equip_conteudo,
            json.dumps(emb_equip),
            equip_meta,
            json.dumps(["hospital", "veterinario", "cachorro", "gato", "pet", "emergencia", "jardim primavera", "hmv"])
        ))
        print("   [OK] Embedding do equipamento_01162 atualizado!")

    conn.commit()
    conn.close()
    print("   [OK] vector.db atualizado com sucesso!")

def update_ontology_json():
    print(">>> 3. Atualizando data/ontology.json...")
    onto_path = "data/ontology.json"
    if os.path.exists(onto_path):
        with open(onto_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Remove se já existia
        data = [d for d in data if d.get("entity_id") != "HOSPITAL_MUNICIPAL_VETERINARIO"]
        
        data.append({
            "entity_id": "HOSPITAL_MUNICIPAL_VETERINARIO",
            "entity_type": "saude_animal",
            "canonical_name": "Hospital Municipal Veterinário de Duque de Caxias (HMV)",
            "secretaria": "Secretaria Municipal de Saúde (SMS) / Secretaria Municipal de Meio Ambiente e Proteção Animal (SMMA)",
            "aliases": [
                "hospital veterinario", "hospital veterinario de caxias", "hospital de cachorro",
                "emergencia veterinaria", "pronto socorro veterinario", "hmv",
                "veterinario publico", "veterinario gratuito", "upa veterinaria", "posto veterinario"
            ],
            "keywords": [
                "cachorro", "gato", "pet", "veterinario", "veterinaria", "emergencia",
                "socorro", "animal", "jardim primavera", "hmv", "consulta animal", "castracao"
            ],
            "active": 1
        })
        
        with open(onto_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("   [OK] data/ontology.json atualizado!")

if __name__ == "__main__":
    update_main_db()
    update_vector_db()
    update_ontology_json()
    print("\n>>> INGESTÃO DO HMV CONCLUÍDA COM SUCESSO TOTAL!")
