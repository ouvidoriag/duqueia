"""
populate_cras_unidades.py
========================
Popula as unidades descentralizadas dos CRAS (Centros de Referência de Assistência Social)
de Duque de Caxias na tabela `secretaria_unidades` do banco de dados estruturado (`data/db/main.db`)
e injeta seus chunks informativos no banco vetorial (`data/db/vector.db`).
"""

import os
import sys
import json
import sqlite3
import unicodedata

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from utils.gemini_client import GeminiClient

DB_MAIN = os.path.join(_PROJECT_ROOT, "data", "db", "main.db")
DB_VECTOR = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")

CRAS_UNIDADES = [
    {
        "name": "CRAS Jardim Primavera",
        "bairro": "Jardim Primavera",
        "distrito": "2º Distrito",
        "address": "Alameda Esmeralda, 206 - Jardim Primavera, Duque de Caxias - RJ (Anexo à Sede da Prefeitura)",
        "phone": "(21) 2672-6650 / (21) 2672-6659",
        "working_hours": "Segunda a sexta-feira, das 9h às 17h",
        "details": "Atendimento para Cadastro Único (CadÚnico), Programa Bolsa Família, acompanhamento familiar pelo PAIF e benefícios eventuais."
    },
    {
        "name": "CRAS Imbariê",
        "bairro": "Imbariê",
        "distrito": "3º Distrito",
        "address": "Avenida Coronel Sisson, lote 3, quadra 2 - Imbariê, Duque de Caxias - RJ",
        "phone": "(21) 2778-1200",
        "working_hours": "Segunda a sexta-feira, das 9h às 17h",
        "details": "Unidade de Proteção Social Básica para o 3º Distrito. Atende moradores de Imbariê, Santa Cruz da Serra e arredores."
    },
    {
        "name": "CRAS Xerém",
        "bairro": "Xerém",
        "distrito": "4º Distrito",
        "address": "Avenida Venâncio Pereira Veloso, s/nº - Xerém, Duque de Caxias - RJ",
        "phone": "(21) 2679-2001",
        "working_hours": "Segunda a sexta-feira, das 9h às 17h",
        "details": "Unidade do SUAS para atendimento às famílias de Xerém, Mantiquira e região do 4º Distrito."
    },
    {
        "name": "CRAS Parque Paulista",
        "bairro": "Parque Paulista",
        "distrito": "3º Distrito",
        "address": "Rua 14, quadra 19, lote 10 - Parque Paulista, Duque de Caxias - RJ",
        "phone": "(21) 2778-4500",
        "working_hours": "Segunda a sexta-feira, das 9h às 17h",
        "details": "Atendimento e cadastramento de famílias do bairro Parque Paulista e arredores."
    },
    {
        "name": "CRAS Pilar",
        "bairro": "Pilar",
        "distrito": "2º Distrito",
        "address": "Praça da Matriz, s/nº - Pilar, Duque de Caxias - RJ",
        "phone": "(21) 2676-1100",
        "working_hours": "Segunda a sexta-feira, das 9h às 17h",
        "details": "Atendimento socioassistencial para a região do Pilar."
    },
    {
        "name": "CRAS Centenário",
        "bairro": "Centenário",
        "distrito": "1º Distrito",
        "address": "Rua Doutor Manuel Teles, s/nº - Centenário, Duque de Caxias - RJ",
        "phone": "(21) 2671-8900",
        "working_hours": "Segunda a sexta-feira, das 9h às 17h",
        "details": "Atendimento socioassistencial para a região do Centenário e Primeiro Distrito."
    },
    {
        "name": "CRAS Beira Mar",
        "bairro": "Beira Mar",
        "distrito": "1º Distrito",
        "address": "Rua Frei Caneca, s/nº - Beira Mar, Duque de Caxias - RJ",
        "phone": "(21) 2671-5500",
        "working_hours": "Segunda a sexta-feira, das 9h às 17h",
        "details": "Atendimento comunitário do SUAS para o bairro Beira Mar."
    }
]

def populate_main_db():
    print(f"[Main DB] Conectando em: {DB_MAIN}")
    conn = sqlite3.connect(DB_MAIN)
    cur = conn.cursor()
    
    # 1. Garante a criação da tabela secretaria_unidades se não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS secretaria_unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secretaria_id INTEGER,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            working_hours TEXT,
            FOREIGN KEY(secretaria_id) REFERENCES secretarias(id) ON DELETE CASCADE
        );
    """)
    
    # 2. Busca o ID da Secretaria de Assistência Social
    cur.execute("SELECT id FROM secretarias WHERE LOWER(name) LIKE '%assistência social%' OR LOWER(code) LIKE '%smasdh%' OR LOWER(code) LIKE '%seasdh%' LIMIT 1")
    row = cur.fetchone()
    sec_id = row[0] if row else 1
    
    inserted_count = 0
    for u in CRAS_UNIDADES:
        # Verifica se já existe para evitar duplicatas
        cur.execute("SELECT id FROM secretaria_unidades WHERE LOWER(name) = ?", (u["name"].lower(),))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO secretaria_unidades (secretaria_id, name, address, phone, working_hours)
                VALUES (?, ?, ?, ?, ?)
            """, (sec_id, u["name"], u["address"], u["phone"], u["working_hours"]))
            inserted_count += 1
            print(f"  + Inserido em secretaria_unidades: {u['name']}")
        else:
            # Atualiza endereço e telefone
            cur.execute("""
                UPDATE secretaria_unidades 
                SET address = ?, phone = ?, working_hours = ?
                WHERE LOWER(name) = ?
            """, (u["address"], u["phone"], u["working_hours"], u["name"].lower()))
            print(f"  ~ Atualizado em secretaria_unidades: {u['name']}")
            
    conn.commit()
    conn.close()
    print(f"[Main DB] Concluído. {inserted_count} novos registros inseridos.")


def create_knowledge_markdown():
    knowledge_dir = os.path.join(_PROJECT_ROOT, "data", "knowledge", "CRIADO")
    os.makedirs(knowledge_dir, exist_ok=True)
    md_path = os.path.join(knowledge_dir, "unidades_cras.md")
    
    lines = [
        "# Equipamentos e Postos de Atendimento dos CRAS — Duque de Caxias",
        "",
        "Os Centros de Referência de Assistência Social (CRAS) são as unidades públicas descentralizadas do SUAS responsáveis pela Proteção Social Básica no município.",
        "",
        "## Unidades e Endereços dos CRAS:",
        ""
    ]
    
    for u in CRAS_UNIDADES:
        lines.append(f"### {u['name']}")
        lines.append(f"- **Bairro / Distrito:** {u['bairro']} ({u['distrito']})")
        lines.append(f"- **Endereço Oficial:** {u['address']}")
        lines.append(f"- **Telefones de Contato:** {u['phone']}")
        lines.append(f"- **Horário de Funcionamento:** {u['working_hours']}")
        lines.append(f"- **Serviços Prestados:** {u['details']}")
        lines.append("")
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"[Knowledge] Arquivo markdown criado em: {md_path}")
    return md_path


def populate_vector_db(gemini_client):
    print(f"[Vector DB] Conectando em: {DB_VECTOR}")
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()
    
    inserted_chunks = 0
    for u in CRAS_UNIDADES:
        source_name = f"unidades_cras.md ({u['name']})"
        category = "unidades"
        content_text = (
            f"# {u['name']} (Centro de Referência de Assistência Social)\n"
            f"Órgão Responsável: Secretaria Municipal de Assistência Social e Direitos Humanos\n"
            f"Bairro: {u['bairro']} | Distrito: {u['distrito']}\n"
            f"Endereço Oficial: {u['address']}\n"
            f"Telefones de Contato: {u['phone']}\n"
            f"Horário de Atendimento: {u['working_hours']}\n"
            f"Serviços e Atividades: {u['details']} Cadastro Único (CadÚnico), Bolsa Família e programas do SUAS."
        )
        metadata_json = json.dumps({
            "title": u["name"],
            "bairro": u["bairro"],
            "distrito": u["distrito"],
            "category": "unidades"
        }, ensure_ascii=False)
        
        keywords_json = json.dumps([
            "cras", u["name"].lower(), u["bairro"].lower(), "cadúnico", "cadunico", "bolsa família", "assistência social", "endereço"
        ], ensure_ascii=False)
        
        # Gera embedding vetorial
        try:
            emb = gemini_client.get_embedding(content_text, is_query=False) if gemini_client and len(gemini_client.api_keys) > 0 else []
            emb_str = json.dumps(emb) if emb else "[]"
        except Exception as e:
            print(f"  Warning: Erro ao gerar embedding para {u['name']}: {e}")
            emb_str = "[]"
            
        # Verifica duplicata em duque_ia_chunks
        cur.execute("SELECT id FROM duque_ia_chunks WHERE source = ?", (source_name,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_name, category, content_text, emb_str, metadata_json, keywords_json))
            inserted_chunks += 1
            print(f"  + Inserido no vector.db: {source_name}")
        else:
            cur.execute("""
                UPDATE duque_ia_chunks
                SET content = ?, embedding = ?, metadata = ?, keywords = ?
                WHERE source = ?
            """, (content_text, emb_str, metadata_json, keywords_json, source_name))
            print(f"  ~ Atualizado no vector.db: {source_name}")
            
    conn.commit()
    conn.close()
    print(f"[Vector DB] Concluído. {inserted_chunks} novos chunks de CRAS inseridos.")

if __name__ == "__main__":
    print("=" * 70)
    print("      POPOVOAMENTO INCREMENTAL DE UNIDADES CRAS DE DUQUE DE CAXIAS")
    print("=" * 70)
    
    gemini_client = GeminiClient()
    populate_main_db()
    create_knowledge_markdown()
    populate_vector_db(gemini_client)
    
    print("\n[OK] Povoamento concluído com sucesso!")
