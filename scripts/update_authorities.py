import os
import re
import json
import datetime

def update_catalog():
    base_dir = r"c:\Users\501379.PMDC\Desktop\PRODUCAO\data\knowledge"
    catalog_path = r"c:\Users\501379.PMDC\Desktop\PRODUCAO\agent\authorities_catalog.py"
    
    authorities = {}
    source_documents = set()
    unique_authorities = set()
    
    # 1. Prefeito
    prefeito_file = os.path.join(base_dir, "CRIADO", "prefeito.md")
    if os.path.exists(prefeito_file):
        source_documents.add("prefeito.md")
        with open(prefeito_file, "r", encoding="utf-8") as f:
            content = f.read()
        name_match = re.search(r'##\s*([^\n]+)', content)
        if name_match:
            full_name = name_match.group(1).strip()
            # Limpa markdown
            full_name = re.sub(r'\([^\)]+\)', '', full_name).strip() # remove parenteses
            prefeito_entry = {
                "cargo": "Prefeito de Duque de Caxias",
                "nome": "Jonathas Monteiro Porto Neto (Netinho Reis)",
                "fonte": "prefeito.md",
                "detalhes": "Netinho Reis é o Prefeito de Duque de Caxias.",
                "documento": "Estrutura Administrativa Oficial"
            }
            unique_authorities.add(prefeito_entry["nome"])
            authorities["prefeito"] = prefeito_entry
            authorities["prefeito de duque de caxias"] = prefeito_entry
            authorities["prefeito municipal"] = prefeito_entry

    # 2. Secretarias e Autarquias
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Encontra títulos # Secretaria... ou # Ouvidoria...
                title_match = re.search(r'#\s*([^\n]+)', content)
                if not title_match:
                    continue
                
                title = title_match.group(1).strip()
                # Procura por Secretário:, Presidente:, Ouvidor:, Procurador:, Controlador:, etc.
                boss_match = re.search(r'-\s+\*\*(Secret(?:á|a)ri[oa]|Presidente|Ouvidor[a]?|Procurador[a]?|Controlador[a]?|Respons(?:á|a)vel):\*\*\s*([^\n]+)', content, re.IGNORECASE)
                
                if boss_match:
                    source_documents.add(file)
                    cargo_type = boss_match.group(1).strip()
                    boss_name = boss_match.group(2).strip()
                    boss_name = re.sub(r'\*\*|\*', '', boss_name).strip()
                    
                    # Normaliza o nome do órgão
                    org_name = title.replace(" - Duque de Caxias", "").strip()
                    
                    auth_entry = {
                        "cargo": f"{cargo_type} de {org_name.replace('Secretaria Municipal de ', '')}",
                        "nome": boss_name,
                        "fonte": file,
                        "detalhes": f"{boss_name} é o {cargo_type.lower()} do órgão {org_name}.",
                        "documento": "Estrutura Administrativa Oficial"
                    }
                    unique_authorities.add(boss_name)
                    
                    # Adiciona chaves de busca normalizadas
                    key_org = org_name.lower().replace("secretaria municipal de ", "").strip()
                    authorities[f"secretário de {key_org}"] = auth_entry
                    authorities[f"secretario de {key_org}"] = auth_entry
                    authorities[f"secretário da {key_org}"] = auth_entry
                    authorities[f"secretario da {key_org}"] = auth_entry
                    authorities[f"responsável pela {key_org}"] = auth_entry
                    authorities[f"responsavel pela {key_org}"] = auth_entry
                    authorities[f"responsável pelo {key_org}"] = auth_entry
                    authorities[f"responsavel pelo {key_org}"] = auth_entry
                    authorities[f"dirige a {key_org}"] = auth_entry
                    authorities[f"dirige o {key_org}"] = auth_entry
                    authorities[f"quem comanda a {key_org}"] = auth_entry
                    authorities[f"quem comanda o {key_org}"] = auth_entry
                    authorities[f"quem é o secretário de {key_org}"] = auth_entry
                    authorities[f"quem é o secretario de {key_org}"] = auth_entry
                    authorities[f"quem é a secretária de {key_org}"] = auth_entry
                    authorities[f"quem é a secretaria de {key_org}"] = auth_entry
                    
                    # Mapeamento para nomes curtos/comuns de cargos
                    if "saúde" in key_org:
                        authorities["secretário de saúde"] = auth_entry
                        authorities["secretario de saude"] = auth_entry
                        authorities["secretária de saúde"] = auth_entry
                        authorities["secretaria de saude"] = auth_entry
                    elif "educação" in key_org or "educacao" in key_org:
                        authorities["secretário de educação"] = auth_entry
                        authorities["secretario de educacao"] = auth_entry
                    elif "obras" in key_org:
                        authorities["secretário de obras"] = auth_entry
                        authorities["secretario de obras"] = auth_entry
                    elif "fazenda" in key_org:
                        authorities["secretário de fazenda"] = auth_entry
                        authorities["secretario de fazenda"] = auth_entry
                        authorities["secretário de finanças"] = auth_entry
                        authorities["secretario de financas"] = auth_entry
                    elif "ouvidoria" in key_org:
                        authorities["ouvidor"] = auth_entry
                        authorities["ouvidor geral"] = auth_entry
                        authorities["quem é o ouvidor"] = auth_entry
                    elif "procuradoria" in key_org or "procurador" in key_org:
                        authorities["procurador"] = auth_entry
                        authorities["procurador geral"] = auth_entry
                    elif "controle" in key_org or "controlador" in key_org:
                        authorities["controlador"] = auth_entry
                        authorities["controlador geral"] = auth_entry

    # Adiciona vice-prefeito se não encontrado
    if "vice-prefeito" not in authorities:
        source_documents.add("a_cidade.md")
        vice_entry = {
            "cargo": "Vice-Prefeito de Duque de Caxias",
            "nome": "Aline da Silva Santos (Aline do Mestre Lulinha)",
            "fonte": "a_cidade.md",
            "detalhes": "Aline do Mestre Lulinha é a Vice-Prefeita de Duque de Caxias.",
            "documento": "Estrutura Administrativa Oficial"
        }
        unique_authorities.add(vice_entry["nome"])
        authorities["vice-prefeito"] = vice_entry
        authorities["vice prefeito"] = vice_entry
        authorities["vice-prefeita"] = vice_entry
        authorities["vice prefeita"] = vice_entry
        authorities["quem é o vice-prefeito"] = vice_entry
        authorities["quem é o vice prefeito"] = vice_entry

    generated_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    catalog_version = datetime.datetime.now().strftime("%Y-%m-%d")

    # Salva o arquivo python gerado com os metadados de versionamento
    with open(catalog_path, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write('"""\n')
        f.write('Catálogo estático de autoridades do município de Duque de Caxias.\n')
        f.write('Gerado automaticamente a partir de data/knowledge.\n')
        f.write('"""\n\n')
        f.write(f'CATALOG_VERSION = "{catalog_version}"\n')
        f.write(f'GENERATED_AT = "{generated_time}"\n')
        f.write(f'TOTAL_AUTHORITIES = {len(unique_authorities)}\n')
        f.write(f'SOURCE_DOCUMENTS = {sorted(list(source_documents))}\n\n')
        f.write('AUTHORITIES = ')
        f.write(json.dumps(authorities, indent=4, ensure_ascii=False))
        f.write("\n")

    print(f"Catálogo de autoridades atualizado com sucesso em {catalog_path}!")
    print(f"Versão: {catalog_version} | Autoridades únicas: {len(unique_authorities)} | Chaves: {len(authorities)}")

if __name__ == "__main__":
    update_catalog()
