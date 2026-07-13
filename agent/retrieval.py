import sys
import os
import json
import re
import unicodedata
from utils.db_client import get_db_connection, query_db, query_one
from agent.models import QueryIntent
from agent.scoring import (
    cosine_similarity,
    extract_query_keywords,
    calculate_keyword_score,
    calculate_keyword_overlap
)

# Algoritmo de Distância de Levenshtein leve para Fuzzy Matching offline
def Levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def find_fuzzy_match(word: str, targets: list, max_distance: int = 2) -> str | None:
    """Retorna o termo correspondente se a distância Levenshtein for menor ou igual à permitida."""
    w_norm = ''.join(c for c in unicodedata.normalize('NFKD', word.lower()) if not unicodedata.combining(c)).strip()
    if not w_norm:
        return None
    for target in targets:
        t_norm = ''.join(c for c in unicodedata.normalize('NFKD', target.lower()) if not unicodedata.combining(c)).strip()
        if w_norm == t_norm:
            return target
        # Distância Levenshtein para cobrir erros de digitação leves
        if abs(len(w_norm) - len(t_norm)) <= max_distance:
            dist = Levenshtein_distance(w_norm, t_norm)
            if dist <= max_distance:
                return target
    return None

# Dicionário de Aliases/Sinônimos populares das Secretarias para match offline rápido
SECRETARIA_ALIASES = {
    "smo": "obras",
    "obras": "obras",
    "smu": "urbanismo",
    "semuh": "urbanismo",
    "urbanismo": "urbanismo",
    "urbanizmo": "urbanismo",
    "sms": "saúde",
    "saude": "saúde",
    "saúde": "saúde",
    "sme": "educação",
    "educacao": "educação",
    "educação": "educação",
    "smf": "fazenda",
    "fazenda": "fazenda",
    "smma": "meio ambiente",
    "meio ambiente": "meio ambiente",
    "fundec": "educação",
    "cras": "assistência social",
    "posto de saude": "saúde",
    "defesa civil": "defesa civil",
    "sdc": "defesa civil"
}


def retrieve_full_category(db_path: str, category: str, filter_field: str = "category", query: str = None) -> list:
    """Busca global: retorna TODOS os chunks de uma categoria, sem limite top_k."""
    if category == "cursos":
        courses_categorized = {
            "Tecnologia & Informática": [
                "Informática Essencial", "Excel Avançado", "Programador Web",
                "Montador e Reparador de Computadores", "Computação Criativa (Scratch)"
            ],
            "Idiomas": [
                "Espanhol", "Inglês", "Francês", "Mandarim", "Libras (Língua Brasileira de Sinais)"
            ],
            "Beleza & Estética": [
                "Alongamento de Unhas", "Barbeiro", "Cabeleireiro", "Depilação",
                "Design de Sobrancelhas", "Manicure e Pedicure", "Maquiagem"
            ],
            "Saúde": [
                "Atendente de Farmácia", "Auxiliar de Saúde Bucal", "Auxiliar de Veterinário",
                "Cuidador de Idosos", "Técnico em Enfermagem"
            ],
            "Música": [
                "Baixo Elétrico", "Bateria", "Canto e Coral", "Cavaquinho", "Flauta",
                "Clarinete", "Guitarra", "Saxofone", "Teclado", "Violino", "Violão"
            ],
            "Construção Civil & Industrial": [
                "Eletricista Instalador Predial", "Ladrilheiro", "Pedreiro",
                "Mecânico de Refrigeração", "Soldador", "Pintura e Textura"
            ],
            "Outros Cursos": [
                "Auxiliar Administrativo", "Auxiliar de Logística", "Costureiro Industrial",
                "Customização de Costura", "Jardinagem e Paisagismo", "Recepcionista"
            ]
        }

        matched_courses = {}
        if query:
            q_lower = query.lower()
            cat_map = {
                "tecnologia": "Tecnologia & Informática",
                "informática": "Tecnologia & Informática",
                "informatica": "Tecnologia & Informática",
                "programador": "Tecnologia & Informática",
                "computador": "Tecnologia & Informática",
                "idioma": "Idiomas",
                "inglês": "Idiomas",
                "ingles": "Idiomas",
                "espanhol": "Idiomas",
                "francês": "Idiomas",
                "frances": "Idiomas",
                "mandarim": "Idiomas",
                "libras": "Idiomas",
                "beleza": "Beleza & Estética",
                "estética": "Beleza & Estética",
                "estetica": "Beleza & Estética",
                "barbeiro": "Beleza & Estética",
                "saúde": "Saúde",
                "saude": "Saúde",
                "farmácia": "Saúde",
                "veterinário": "Saúde",
                "enfermagem": "Saúde",
                "música": "Música",
                "musica": "Música",
                "violão": "Música",
                "violao": "Música",
                "guitarra": "Música",
                "construção": "Construção Civil & Industrial",
                "construcao": "Construção Civil & Industrial",
                "eletricista": "Construção Civil & Industrial",
                "pedreiro": "Construção Civil & Industrial"
            }

            target_cats = set()
            for kw, actual_cat in cat_map.items():
                if kw in q_lower:
                    target_cats.add(actual_cat)

            if target_cats:
                for tc in target_cats:
                    matched_courses[tc] = courses_categorized[tc]
            else:
                for cat_name, course_list in courses_categorized.items():
                    matching_sub = [
                        c for c in course_list 
                        if c.lower() in q_lower or q_lower in c.lower() or 
                        any(len(w) > 3 and w in q_lower for w in c.lower().split())
                    ]
                    if matching_sub:
                        matched_courses[cat_name] = matching_sub

        if matched_courses:
            lines = ["Com base na sua busca pelos cursos da FUNDEC, encontrei as seguintes opções:\n"]
            for cat_name, course_list in matched_courses.items():
                lines.append(f"• **{cat_name}**:")
                for c in course_list:
                    lines.append(f"  - {c}")
            lines.append("\nPara mais detalhes sobre vagas e inscrições, entre em contato com a **FUNDEC** pelo telefone **(21) 2672-5650** ou visite a sede em **Av. Brigadeiro Lima e Silva, 131 - Parque Duque**.")
            content = "\n".join(lines)
        else:
            content = (
                "A FUNDEC oferece mais de 150 cursos gratuitos de qualificação profissional em diversas áreas:\n\n"
                "• **Tecnologia & Informática:** Informática Essencial, Excel Avançado, Programador Web, Montador e Reparador de Computadores, Computação Criativa (Scratch).\n"
                "• **Idiomas:** Espanhol, Inglês, Francês, Mandarim, Libras (Língua Brasileira de Sinais).\n"
                "• **Beleza & Estética:** Alongamento de Unhas, Barbeiro, Cabeleireiro, Depilação, Design de Sobrancelhas, Manicure e Pedicure, Maquiagem.\n"
                "• **Saúde:** Atendente de Farmácia, Auxiliar de Saúde Bucal, Auxiliar de Veterinário, Cuidador de Idosos, Técnico em Enfermagem.\n"
                "• **Música:** Baixo Elétrico, Bateria, Canto e Coral, Cavaquinho, Flauta, Clarinete, Guitarra, Saxofone, Teclado, Violino, Violão.\n"
                "• **Construção Civil & Industrial:** Eletricista Instalador Predial, Ladrilheiro, Pedreiro, Mecânico de Refrigeração, Soldador, Pintura e Textura.\n"
                "• **Outros Cursos:** Auxiliar Administrativo, Auxiliar de Logística, Costureiro Industrial, Customização de Costura, Jardinagem e Paisagismo, Recepcionista.\n\n"
                "Para mais detalhes sobre vagas e inscrições, entre em contato com a **FUNDEC** pelo telefone **(21) 2672-5650** ou visite a sede em **Av. Brigadeiro Lima e Silva, 131 - Parque Duque**."
            )
        return [{
            "source": "CARTA_DE_SERVICO_23.05.26.xlsx",
            "category": "cursos",
            "content": content,
            "title": "Cursos Oferecidos pela FUNDEC",
            "similarity": 1.0,
            "semantic_score": 1.0,
            "chunk_keywords": [],
            "is_list_result": True
        }]

    rows = query_db(
        db_path,
        f"SELECT DISTINCT source, category, content, metadata FROM duque_ia_chunks "
        f"WHERE {filter_field} = ? ORDER BY source",
        (category,)
    )

    results = []
    seen_keys = set()
    for source, cat, content, meta_str in rows:
        key = content if category == "cursos" else source
        if key in seen_keys:
            continue
        seen_keys.add(key)
        try:
            meta = json.loads(meta_str) if meta_str else {}
        except Exception:
            meta = {}
        results.append({
            "source": source,
            "category": cat,
            "content": content,
            "title": meta.get("title", source),
            "similarity": 1.0,
            "semantic_score": 1.0,
            "chunk_keywords": [],
            "is_list_result": True
        })
    return results

def retrieve_structured_service(db_path: str, query: str, query_keywords: list, using_real: bool) -> list:
    """Busca estruturada nas tabelas normalizadas de serviços com normalização de termos de ação e fuzzy matching."""
    
    # 1. Filtra palavras de ação, pronomes e ruído estrutural
    action_words = [
        "como", "solicitar", "fazer", "quero", "preciso", "saber", "favor", "onde", "para", "pedir", 
        "registrar", " reclamar", "reclamacao", "denuncia", "denunciar", "obter", "emitir", "tirar", 
        "segunda", "via", "telefone", "contato", "endereco"
    ]
    entity_words = ["rua", "ruas", "avenida", "avenidas", "bairro", "bairros", "distrito", "lote", "lotes", "quadra", "quadras", "numero", "num"]
    
    search_words = [w for w in query_keywords if len(w) >= 3 and w not in action_words and w not in entity_words]
    
    # Tratamento especial para termos comuns (IPTU, Tapa Buraco)
    query_lower = query.lower()
    if "tapa" in query_lower or "buraco" in query_lower:
        if "buraco" not in search_words:
            search_words.append("buraco")
        if "tapa" not in search_words:
            search_words.append("tapa")
            
    if not search_words:
        return []
        
    conditions = []
    params = []
    for w in search_words:
        conditions.append("(servico_nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{w}%", f"%{w}%"])
        
    sql = f"""
        SELECT servico_id, secretaria_nome, secretaria_codigo, servico_nome, 
               categoria, descricao, como_acessar, quem_pode_solicitar, 
               tempo_espera, prazo_maximo, custo, norma_reguladora
        FROM vw_ia_servicos
        WHERE {" OR ".join(conditions)}
    """
    
    results = []
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        except Exception as e:
            print(f"[Structured Retrieval Error] View vw_ia_servicos não disponível: {e}", file=sys.stderr)
            return []
            
        for row in rows:
            s_id, sec_name, sec_code, s_name, cat, desc, how, who, wait, deadline, cost, norm = row
            
            match_score = 0.0
            # Normalização para comparação sem acento
            s_name_norm = ''.join(c for c in unicodedata.normalize('NFKD', s_name.lower()) if not unicodedata.combining(c))
            desc_norm = ''.join(c for c in unicodedata.normalize('NFKD', desc.lower()) if not unicodedata.combining(c)) if desc else ""
            
            for w in search_words:
                w_norm = ''.join(c for c in unicodedata.normalize('NFKD', w.lower()) if not unicodedata.combining(c))
                if w_norm in s_name_norm:
                    # Dá um peso significativamente maior se corresponder ao termo exato do serviço
                    if w_norm == "buraco" and "buraco" in s_name_norm:
                        match_score += 4.0
                    else:
                        match_score += 2.0
                elif desc_norm and w_norm in desc_norm:
                    if w_norm == "buraco" and "buraco" in desc_norm:
                        match_score += 2.0
                    else:
                        match_score += 1.0
                    
            if match_score == 0.0:
                continue
                
            cursor.execute("SELECT phone FROM service_phones WHERE service_id = ?", (s_id,))
            phones = [r[0] for r in cursor.fetchall()]
            
            cursor.execute("SELECT email FROM service_emails WHERE service_id = ?", (s_id,))
            emails = [r[0] for r in cursor.fetchall()]
            
            cursor.execute("SELECT link FROM service_links WHERE service_id = ?", (s_id,))
            links = [r[0] for r in cursor.fetchall()]
            
            cursor.execute("SELECT step_number, description FROM service_steps WHERE service_id = ? ORDER BY step_number", (s_id,))
            steps = [f"Passo {num}: {d}" for num, d in cursor.fetchall()]
            
            cursor.execute("SELECT document_name FROM service_documents WHERE service_id = ?", (s_id,))
            docs = [r[0] for r in cursor.fetchall()]
            
            # Busca o endereço físico da secretaria responsável pelo serviço
            sec_address = "Não cadastrado"
            cursor.execute("SELECT address FROM secretarias WHERE name = ? OR code = ?", (sec_name, sec_code))
            sec_row = cursor.fetchone()
            if sec_row and sec_row[0]:
                sec_address = sec_row[0]
                
            content_parts = [
                "[FONTE OFICIAL ESTRUTURADA]",
                "Tipo: Carta de Serviços Oficiais",
                "Confiabilidade: Máxima (Auditado)",
                "Última Atualização: 2026-07-01",
                "",
                f"Serviço Oficial: {s_name}",
                f"Secretaria Responsável: {sec_name} ({sec_code})",
                f"Endereço de Atendimento: {sec_address}",
                f"Descrição: {desc}",
                f"Quem pode solicitar: {who}",
                f"Prazo Máximo: {deadline}",
                f"Custo: {cost}"
            ]
            if phones:
                content_parts.append(f"Telefones de Contato: {', '.join(phones)}")
            if emails:
                content_parts.append(f"E-mails de Contato: {', '.join(emails)}")
            if links:
                content_parts.append(f"Links / Canais Digitais: {', '.join(links)}")
            if docs:
                content_parts.append("Documentos Necessários:\n" + "\n".join(f"- {d}" for d in docs))
            if steps:
                content_parts.append("Passo a Passo de Acesso:\n" + "\n".join(steps))
                
            structured_text = "\n".join(content_parts)
            
            base_score = 0.50 if using_real else 0.35
            calibrated_score = min(base_score + (match_score * 0.15), 0.98)
            
            results.append({
                "source": f"vw_ia_servicos (ID: {s_id})",
                "category": "carta_servicos",
                "content": structured_text,
                "title": s_name,
                "semantic_score": calibrated_score,
                "similarity": calibrated_score,
                "chunk_keywords": search_words
            })
            
    seen_ids = set()
    unique_results = []
    for r in results:
        if r["source"] not in seen_ids:
            seen_ids.add(r["source"])
            unique_results.append(r)
            
    return unique_results

def retrieve_structured_secretaria(db_path: str, query: str, query_keywords: list) -> list:
    """Busca estruturada na tabela de secretarias por nome ou sigla/código com ordenação de relevância, fuzzy e aliases."""
    
    # 1. Resolve Aliases e Apelidos populares na query inteira com fronteiras de palavra exatas
    query_lower = query.lower()
    resolved_keyword = None
    for alias, target in SECRETARIA_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", query_lower):
            resolved_keyword = target
            break
            
            
    ignore_words = ["secretaria", "municipal", "de", "e", "do", "da", "como", "onde", "qual", "telefone", "endereco", "endereço", "email", "contato"]
    search_words = [w for w in query_keywords if len(w) >= 3 and w not in ignore_words]
    
    # Se o alias resolveu para um alvo, garante que ele está nas palavras de busca
    if resolved_keyword and resolved_keyword not in search_words:
        search_words.append(resolved_keyword)
        
    if not search_words:
        return []
        
    # Obtém a lista de siglas existentes para fuzzy matching
    existing_codes = []
    existing_names = []
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT code, name FROM secretarias;")
            for c_row in cursor.fetchall():
                existing_codes.append(c_row[0])
                existing_names.append(c_row[1])
        except Exception:
            pass

        # 2. Corrige erros de digitação (Fuzzy Matching) usando Levenshtein
        fuzzy_words = []
        for w in search_words:
            # Tenta bater com algum código (sigla) primeiro
            matched_code = find_fuzzy_match(w, existing_codes, max_distance=1)
            if matched_code:
                fuzzy_words.append(matched_code)
                continue
            # Tenta bater com palavras contidas nos nomes das secretarias
            words_in_names = []
            for name in existing_names:
                words_in_names.extend([part.strip("(),.-") for part in name.split() if len(part) >= 3])
            matched_name_word = find_fuzzy_match(w, list(set(words_in_names)), max_distance=2)
            if matched_name_word:
                fuzzy_words.append(matched_name_word)
            else:
                fuzzy_words.append(w)

        search_words = list(set(fuzzy_words))

        # 3. Monta a SQL com ordenação de relevância exata de código
        conditions = []
        params = []
        
        # Parâmetros para o ORDER BY CASE
        first_term = search_words[0].upper() if search_words else ""
        order_params = [first_term, first_term, f"{first_term}%", f"%{first_term}%"]
        
        for w in search_words:
            conditions.append("(name LIKE ? OR code LIKE ?)")
            params.extend([f"%{w}%", f"%{w}%"])
            
        sql = f"""
            SELECT id, name, code, address, phone, email, working_hours
            FROM secretarias
            WHERE {" OR ".join(conditions)}
            ORDER BY
            CASE
                WHEN code = ? THEN 1
                WHEN name = ? THEN 2
                WHEN code LIKE ? THEN 3
                WHEN name LIKE ? THEN 4
                ELSE 5
            END
        """
        
        # Junta os parâmetros de filtro com os parâmetros do ORDER BY CASE
        final_params = params + order_params
        
        try:
            cursor.execute(sql, final_params)
            rows = cursor.fetchall()
        except Exception:
            return []
            
        results = []
        for idx, row in enumerate(rows):
            sec_id, name, code, address, phone, email, hours = row
            if not address and not phone and not email:
                continue
                
            content_parts = [
                "[FONTE OFICIAL ESTRUTURADA]",
                "Tipo: Dados Cadastrais / Órgão Municipal",
                "Confiabilidade: Máxima (Auditado)",
                "Última Atualização: 2026-07-01",
                "",
                f"Órgão Oficial: {name} ({code})",
                f"Endereço Oficial: {address or 'Não cadastrado'}",
                f"Telefone de Contato: {phone or 'Não cadastrado'}",
                f"E-mail de Contato: {email or 'Não cadastrado'}",
                f"Horário de Funcionamento: {hours or 'Segunda a sexta-feira, das 9h às 17h'}"
            ]
            structured_text = "\n".join(content_parts)
            
            # Atribui score ligeiramente decrescente com base na ordenação de relevância do SQL
            score = round(0.99 - (idx * 0.01), 2)
            
            results.append({
                "source": f"secretarias (ID: {sec_id})",
                "category": "secretarias",
                "content": structured_text,
                "title": name,
                "semantic_score": score,
                "similarity": score,
                "chunk_keywords": search_words
            })
        return results

def retrieve_context(query: str, db_path: str, using_real: bool, similarity_threshold: float, gemini_client, reranker, top_k: int = 3, intent_info: dict = None, tools_selected: list = None) -> list:
    """Busca híbrida baseada na arquitetura LORS: orquestração multi-query gerada pela LLM/Planner."""
    if not os.path.exists(db_path):
        print(f"[Agent Error] Banco de dados não encontrado em {db_path}", file=sys.stderr)
        return []

    # ---- ROTA ESPECIAL: Listagem completa por categoria ----
    if intent_info and intent_info.get("intent") == QueryIntent.LIST:
        list_cfg = intent_info.get("list_config", {})
        if list_cfg:
            return retrieve_full_category(
                db_path,
                list_cfg["db_category"],
                list_cfg.get("db_filter_field", "category"),
                query=query
            )

    # Define quais ferramentas executar com base na seleção do Roteador de Ferramentas
    run_structured = tools_selected is None or "structured_db" in tools_selected
    run_geo = tools_selected is None or "geo_units" in tools_selected
    run_vector = tools_selected is None or "faq_chunks" in tools_selected

    # 1. Aciona o Planejador Semântico (LORS)
    from agent.planner import SemanticRecoveryPlanner
    planner = SemanticRecoveryPlanner(gemini_client)
    plan = planner.plan_recovery(query, history=None)
    
    plan_queries = plan.get("queries", [query])
    plan_focus = plan.get("focus", ["general"])
    
    structured_candidates = []
    vector_candidates = []
    
    # 2. Executa as buscas para cada sub-query gerada pelo LORS
    for q_sub in plan_queries:
        q_keywords = extract_query_keywords(q_sub)
        
        # A) Busca Estruturada de Secretarias
        if run_structured and any(ind in q_sub.lower() for ind in ["secretaria", "endereco", "endereço", "telefone", "contato", "email", "onde", "localizacao", "smo", "smu", "sms", "sme", "smf"]):
            struct_sec = retrieve_structured_secretaria(db_path, q_sub, q_keywords)
            structured_candidates.extend(struct_sec)
            
        # B) Busca Estruturada de Serviços
        if run_structured:
            struct_res = retrieve_structured_service(db_path, q_sub, q_keywords, using_real)
            structured_candidates.extend(struct_res)
            
        # C) Busca Estruturada de Unidades Físicas (CRAS/Equipamentos) na nova tabela secretaria_unidades
        if run_geo and any(ind in q_sub.lower() for ind in ["cras", "unidade", "posto", "atendimento", "equipamento", "onde fica", "onde fazer", "cadastro"]):
            try:
                rows_unidades = query_db(db_path, """
                    SELECT u.name, u.address, u.phone, u.working_hours, s.name
                    FROM secretaria_unidades u
                    JOIN secretarias s ON u.secretaria_id = s.id
                """)
                for name, addr, phone, hours, sec_name in rows_unidades:
                    structured_text = (
                        "[FONTE OFICIAL ESTRUTURADA]\n"
                        "Tipo: Unidade de Atendimento Local (CRAS/Posto)\n"
                        "Confiabilidade: Máxima (Auditado)\n"
                        "Última Atualização: 2026-07-01\n\n"
                        f"Equipamento: {name}\n"
                        f"Órgão Responsável: {sec_name}\n"
                        f"Endereço Físico: {addr}\n"
                        f"Telefone: {phone or 'Não disponível'}\n"
                        f"Funcionamento: {hours or 'Segunda a sexta-feira, das 9h às 17h'}"
                    )
                    # Verifica se o CRAS se relaciona com as palavras da busca (sem o bug do w in q_sub.lower())
                    if any(w in name.lower() or w in addr.lower() for w in q_keywords if len(w) >= 3):
                        structured_candidates.append({
                            "source": f"unidades (CRAS: {name})",
                            "category": "unidades",
                            "content": structured_text,
                            "title": name,
                            "semantic_score": 0.99,
                            "similarity": 0.99,
                            "chunk_keywords": q_keywords
                        })
            except Exception as e:
                print(f"[LORS Unidades Error] Falha na busca de unidades físicas: {e}", file=sys.stderr)

        # D) Busca Vetorial/Descritiva (Chunks gerais de documentos)
        if run_vector:
            query_vector = gemini_client.get_embedding(q_sub, is_query=True) if using_real else None
            try:
                rows_chunks = query_db(db_path, "SELECT source, category, content, embedding, metadata, keywords FROM duque_ia_chunks")
                for row in rows_chunks:
                    source, category, content, emb_str, meta_str, kw_str = row
                    try:
                        meta = json.loads(meta_str) if meta_str else {}
                    except Exception:
                        meta = {}
                    try:
                        chunk_keywords = json.loads(kw_str) if kw_str else []
                    except Exception:
                        chunk_keywords = []

                    title = meta.get("title", source)

                    if using_real and query_vector:
                        try:
                            emb = json.loads(emb_str)
                            semantic_score = cosine_similarity(query_vector, emb) if len(emb) == len(query_vector) else 0.0
                        except Exception:
                            semantic_score = 0.0
                    else:
                        semantic_score = calculate_keyword_score(q_sub, content, title)

                    vector_candidates.append({
                        "source": source,
                        "category": category,
                        "content": content,
                        "semantic_score": semantic_score,
                        "chunk_keywords": chunk_keywords,
                        "title": title
                    })
            except Exception as e:
                print(f"[LORS Chunks Error] Falha na busca vetorial de chunks: {e}", file=sys.stderr)

    # 3. Consolidação e Deduplicação dos Resultados do LORS
    # Ordena chunks vetoriais pelo score semântico decrescente
    vector_candidates.sort(key=lambda x: x["semantic_score"], reverse=True)
    top_candidates = vector_candidates[:top_k * 6]

    # Reranking Híbrido nos chunks vetoriais
    query_normalized = ''.join(c for c in unicodedata.normalize('NFKD', query.lower()) if not unicodedata.combining(c))
    for c in top_candidates:
        if "similarity" not in c:
            kw_score = calculate_keyword_overlap(extract_query_keywords(query), c["chunk_keywords"])
            # Formula híbrida ajustada para dar peso prioritário à busca vetorial semântica real (85%)
            c["similarity"] = round(0.85 * c["semantic_score"] + 0.15 * kw_score, 4)

    top_candidates.sort(key=lambda x: x["similarity"], reverse=True)
    reranked = reranker.rerank(query, top_candidates)
    
    # Merge Híbrido Dinâmico: Junta todos os candidatos estruturados e vetoriais,
    # ordena pelo score 'similarity' final para garantir que o mais relevante (seja estruturado ou descritivo) suba para o topo.
    all_candidates = []
    seen_sources = set()
    
    for sc in structured_candidates:
        if sc["source"] not in seen_sources:
            seen_sources.add(sc["source"])
            all_candidates.append(sc)
            
    for r in reranked:
        if r["source"] not in seen_sources:
            seen_sources.add(r["source"])
            all_candidates.append(r)
            
    # Aplica boosts e filtros a todos os candidatos mesclados (estruturados e vetoriais)
    for c in all_candidates:
        # Boost de categoria e de contato/localização nos chunks do RAG
        if c.get("category") == "secretarias" and any(w in query_normalized for w in ["onde", "fica", "endereco", "localizacao", "contato", "telefone"]):
            c["similarity"] = round(c["similarity"] + 0.15, 4)
        if any(w in query_normalized for w in ["onde", "fica", "endereco", "localizacao", "contato", "telefone"]):
            content_lower = c.get("content", "").lower()
            if "endereço" in content_lower or "endereco" in content_lower or "como acessar" in content_lower or "telefone" in content_lower:
                c["similarity"] = round(c["similarity"] + 0.15, 4)
                
        # Boost de saúde para direcionamento clínico/hospitalar
        if c.get("source") in ["saude.md", "saude.json", "postos_saude_caxias.xlsx"] and any(w in query_normalized for w in ["hospital", "upa", "uph", "emergencia", "emergência", "dor", "medico", "médico", "quebrado", "fratura", "pe ", "pé "]):
            c["similarity"] = round(c["similarity"] + 0.20, 4)

        # ── NOVOS BOOSTS DE INTENÇÃO E FILTROS DE METADADOS ──
        
        # 1. Governança e Informações Gerais da Cidade
        if any(w in query_normalized for w in ["distrito", "prefeito", "historia", "origem", "fundacao", "fundacao"]):
            if c.get("category") == "general" or "a_cidade" in str(c.get("source")) or "prefeito" in str(c.get("source")):
                c["similarity"] = round(c["similarity"] + 0.35, 4)
            # Penaliza carta de serviços para perguntas de geografia/governo geral
            if c.get("category") == "carta_servicos":
                c["similarity"] = round(c["similarity"] - 0.25, 4)

        # 2. Lideranças e Estrutura das Secretarias (Quem é o secretário...)
        if any(w in query_normalized for w in ["secretario", "secretaria", "responsavel pela pasta", "pasta de", "liderança"]):
            if c.get("category") == "secretarias":
                c["similarity"] = round(c["similarity"] + 0.35, 4)
            if c.get("category") == "carta_servicos":
                c["similarity"] = round(c["similarity"] - 0.30, 4)

        # 3. Impostos, Taxas e Fazenda (IPTU, Alvará, ISS)
        if any(w in query_normalized for w in ["iptu", "alvara", "iss", "fazenda", "tributo", "imposto"]):
            if "fazenda" in str(c.get("source")):
                c["similarity"] = round(c["similarity"] + 0.35, 4)
            elif c.get("category") == "carta_servicos" and "iptu" not in c.get("content", "").lower() and "alvara" not in c.get("content", "").lower():
                c["similarity"] = round(c["similarity"] - 0.25, 4)

        # 4. Saúde do Homem / Saúde Geral
        if "saude do homem" in query_normalized or "saude da mulher" in query_normalized:
            if "saude" in str(c.get("source")):
                c["similarity"] = round(c["similarity"] + 0.35, 4)
            elif c.get("category") == "carta_servicos":
                # Penaliza outros serviços se a busca for especificamente sobre o programa de saúde do homem na ficha da secretaria
                c["similarity"] = round(c["similarity"] - 0.20, 4)

        # C1: Boost para queries de especialidades médicas
        # Prioriza chunks de saúde com "especialidade" ou "encaminhamento" e penaliza programas escolares
        MEDICAL_SPECIALTY_TERMS = [
            "dermato", "oftalmolog", "cardiolog", "ortopedia", "neurolog", "pneumolog",
            "ginecolog", "urolog", "psiquiatr", "nefrol", "gastroenterol", "endocrinol",
            "reumatol", "hemat", "infectolog", "proctolog", "geriatr", "especialist",
            "consulta especializada", "medico especialista"
        ]
        if any(term in query_normalized for term in MEDICAL_SPECIALTY_TERMS):
            content_lower = c.get("content", "").lower()
            title_lower = c.get("title", "").lower()
            if any(x in content_lower or x in title_lower for x in ["especialidade", "encaminhamento", "ubs", "unidade basica", "regulacao"]):
                c["similarity"] = round(c["similarity"] + 0.30, 4)
            # Penaliza fortemente chunks de programas escolares (causa raiz do bug do dermatologista)
            if any(x in title_lower or x in content_lower for x in ["escola", "escolar", "programa saude na escola", "pse"]):
                c["similarity"] = round(c["similarity"] - 0.40, 4)

        # C2: Boost de Localidade — aumenta relevância de chunks que mencionam o bairro/localidade da query
        KNOWN_LOCALITIES = [
            "xerem", "xerém", "jardim primavera", "parque paulista",
            "imbarie", "imbariê", "pilar", "saracuruna",
            "campos eliseos", "campos elíseos", "pantanal", "centenario",
            "centenário", "25 de agosto"
        ]
        for loc in KNOWN_LOCALITIES:
            if loc in query_normalized:
                loc_norm = ''.join(c2 for c2 in unicodedata.normalize('NFKD', loc.lower()) if not unicodedata.combining(c2))
                content_norm = ''.join(c2 for c2 in unicodedata.normalize('NFKD', c.get("content", "").lower()) if not unicodedata.combining(c2))
                if loc_norm in content_norm or loc_norm in ''.join(
                    c2 for c2 in unicodedata.normalize('NFKD', c.get("title", "").lower()) if not unicodedata.combining(c2)
                ):
                    c["similarity"] = round(c["similarity"] + 0.25, 4)
                break

    # Ordena todos juntos pelo score 'similarity' de forma decrescente
    all_candidates.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
    
    return all_candidates[:top_k]



