# -*- coding: utf-8 -*-
"""
Reestruturação Territorial (Fase 6 GIS do AGENTS.md):
Subdivide os 4 blocos monolíticos de distritos (geo_01571 a geo_01574)
em 47 Chunks Atômicos por Bairro Mestre Oficial.
Regra: 1 Bairro = 1 Chunk.
Não adiciona comunidades ou ruas (respeito estrito à diretriz do usuário).
"""

import os
import sys
import json
import sqlite3
import unicodedata
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_VECTOR = os.path.join(BASE_DIR, "data", "db", "vector.db")

TYPO_FIXES = {
    "Amapáááá": "Amapá",
    "Nãova Campinas": "Nova Campinas",
    "Taquaraa": "Taquara",
    "V. São José": "Vila São José"
}

def normalize_name(name):
    name = name.strip()
    return TYPO_FIXES.get(name, name)

def get_slug(name):
    clean = unicodedata.normalize('NFKD', name.lower())
    clean = ''.join(c for c in clean if not unicodedata.combining(c))
    clean = re.sub(r'[^a-z0-9]+', '_', clean).strip('_')
    return clean

def extract_bairros_from_db():
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    distritos_map = {
        'geo_01571': ('1º Distrito — Duque de Caxias (Sede / Centro)', '1_distrito'),
        'geo_01572': ('2º Distrito — Campos Elíseos', '2_distrito'),
        'geo_01573': ('3º Distrito — Imbariê', '3_distrito'),
        'geo_01574': ('4º Distrito — Xerém', '4_distrito')
    }

    bairros_chunks = []

    for gid, (dist_nome, dist_slug) in distritos_map.items():
        cur.execute("SELECT conteudo FROM chunks WHERE id = ?", (gid,))
        row = cur.fetchone()
        if not row:
            continue
        text = row[0]

        # Extrair mapeamento de equipamentos por bairro
        equip_detalhes = {}
        if '### 2.' in text and 'Todas as Localidades' in text:
            part_equip = text.split('Todas as Localidades')[1]
            if '###' in part_equip:
                part_equip = part_equip.split('###')[0]
            for l in part_equip.split('\n'):
                if '|' in l and not l.startswith('| :---') and not l.startswith('|:---') and not '| Total de Equipamentos |' in l:
                    c = [col.strip() for col in l.split('|')[1:-1]]
                    if len(c) >= 3 and c[0].isdigit():
                        b_nome = normalize_name(c[1].replace('**', '').strip())
                        b_equip_txt = c[2] if len(c) > 2 else ""
                        equip_detalhes[b_nome.lower()] = b_equip_txt

        # Extrair tabela principal de bairros
        lines = text.split('\n')
        in_table = False
        for line in lines:
            if '| Nº |' in line or '| Nº|' in line:
                in_table = True
                continue
            if in_table:
                if line.startswith('| :---:') or line.startswith('|:---:'):
                    continue
                if not line.startswith('|'):
                    in_table = False
                    continue
                cols = [c.strip() for c in line.split('|')[1:-1]]
                if len(cols) >= 5 and cols[0].isdigit():
                    num = cols[0]
                    nome_raw = cols[1].replace('**', '').strip()
                    nome = normalize_name(nome_raw)
                    carac = cols[2]
                    cep = cols[3].replace('`', '')
                    aliases = cols[4].replace('`', '')
                    equip_cnt = cols[5].replace('**', '').strip() if len(cols) > 5 else "0"

                    detalhes_equip = equip_detalhes.get(nome.lower(), "")
                    equip_str = f" Total cadastrado: {equip_cnt} unidades."
                    if detalhes_equip and len(detalhes_equip) > 5:
                        equip_str += f" Principais unidades instaladas: {detalhes_equip}"

                    b_slug = get_slug(nome)
                    chunk_id = f"bairro_{dist_slug}_{b_slug}"
                    titulo = f"Bairro Oficial de Duque de Caxias: {nome} ({dist_nome.split('—')[0].strip()})"

                    conteudo = f"""# 🏛️ Território Municipal — Duque de Caxias / RJ
## Bairro Oficial: {nome}
• Entidade Geográfica: Bairro Mestre Consolidado (GIS Municipal)
• Distrito Administrativo: {dist_nome}
• Região / Característica Territorial: {carac}
• Faixa Oficial de CEP: {cep}
• Apelidos, Nomes Populares e Variações: {aliases if aliases != '-' else nome}
• Equipamentos Públicos Municipais:{equip_str}
"""
                    tags = [
                        "bairro", "geografia", "distrito", "territorio", 
                        nome.lower(), dist_slug, "cep", "equipamentos publicos"
                    ]
                    if aliases and aliases != '-':
                        for a in aliases.split(','):
                            if len(a.strip()) > 2:
                                tags.append(a.strip().lower())

                    bairros_chunks.append({
                        "id": chunk_id,
                        "tipo": "GEOGRAFIA_TERRITORIAL",
                        "titulo": titulo,
                        "conteudo": conteudo.strip(),
                        "metadata": {
                            "entidade": "bairro",
                            "nome": nome,
                            "distrito": dist_nome,
                            "cep_faixa": cep,
                            "equipamentos_count": equip_cnt,
                            "tags": tags,
                            "boost_weight": 2.0
                        }
                    })

    conn.close()
    return bairros_chunks

if __name__ == "__main__":
    chunks = extract_bairros_from_db()
    print(f"Total de chunks atômicos de bairros gerados: {len(chunks)}")
    for c in chunks[:5]:
        print(f"\nID: {c['id']}")
        print(f"Título: {c['titulo']}")
        print(f"Len: {len(c['conteudo'])} chars")
        print(f"Conteúdo:\n{c['conteudo']}")
