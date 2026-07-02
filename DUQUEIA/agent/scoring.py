import re
from agent.config import KEYWORD_POLICY

def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Calcula a similaridade de cosseno entre dois vetores."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a * norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

import unicodedata

def extract_query_keywords(query: str) -> list:
    """Extrai palavras-chave significativas da pergunta excluindo stopwords e aplicando pesos."""
    # Normalização de acentuação: remove acentos e cedilhas
    query_normalized = ''.join(
        c for c in unicodedata.normalize('NFKD', query.lower())
        if not unicodedata.combining(c)
    )
    
    # Extrai palavras de 3 a 15 caracteres
    words = re.findall(r'\b\w{3,15}\b', query_normalized)
    
    # Mapeamento de termos comuns e variações de grafia
    mapped_words = []
    for w in words:
        if w in ["buracos", "buraco", "burcao", "burac"]:
            mapped_words.append("buraco")
        elif w in ["reclamar", "reclamacao", "reclamacoes", "queixa"]:
            # 'reclamar' e afins podem causar falsos positivos ou ruído, então ignoramos
            continue
        elif w in ["rua", "ruas", "vias", "via", "estrada", "avenida"]:
            mapped_words.append("rua")
        else:
            mapped_words.append(w)
            
    noise_keys = KEYWORD_POLICY["noise"].keys()
    # Também normaliza as noise_keys para filtragem correta
    noise_normalized = {
        ''.join(c for c in unicodedata.normalize('NFKD', k) if not unicodedata.combining(c))
        for k in noise_keys
    }
    
    return [w for w in mapped_words if w not in noise_normalized and w not in ["isso", "casa", "minha"]]


def calculate_keyword_score(query: str, content: str, title: str) -> float:
    """Score de relevância baseado em palavras-chave ponderadas (KEYWORD_POLICY)."""
    query_words = extract_query_keywords(query)
    if not query_words:
        return 0.0
        
    content_norm = ''.join(
        c for c in unicodedata.normalize('NFKD', content.lower())
        if not unicodedata.combining(c)
    )
    title_norm = ''.join(
        c for c in unicodedata.normalize('NFKD', title.lower())
        if not unicodedata.combining(c)
    )
    
    matches = 0.0
    total_weight = 0.0
    for word in query_words:
        weight = 1.0
        for cat, words_dict in KEYWORD_POLICY.items():
            if word in words_dict:
                weight = words_dict[word]
                break
        total_weight += weight
        
        if word in title_norm:
            matches += (weight * 1.5)
        elif word in content_norm:
            matches += (weight * 1.0)
            
    return matches / total_weight if total_weight > 0 else 0.0

def calculate_keyword_overlap(query_keywords: list, chunk_keywords: list) -> float:
    """Calcula a sobreposição ponderada entre palavras-chave da query e do chunk."""
    if not query_keywords or not chunk_keywords:
        return 0.0
    query_set = set(query_keywords)
    
    # Normaliza chunk_keywords para remover acentos
    normalized_chunk_keywords = []
    for k in chunk_keywords:
        k_norm = ''.join(
            c for c in unicodedata.normalize('NFKD', k.lower())
            if not unicodedata.combining(c)
        )
        normalized_chunk_keywords.append(k_norm)
        
    chunk_set = set(normalized_chunk_keywords)
    intersection = query_set & chunk_set
    
    matches = 0.0
    total_weight = 0.0
    for word in query_set:
        weight = 1.0
        for cat, words_dict in KEYWORD_POLICY.items():
            if word in words_dict:
                weight = words_dict[word]
                break
        total_weight += weight
        if word in intersection:
            matches += weight
            
    return matches / total_weight if total_weight > 0 else 0.0
