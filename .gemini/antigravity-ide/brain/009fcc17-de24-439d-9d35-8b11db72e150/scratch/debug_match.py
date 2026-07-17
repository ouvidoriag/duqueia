import sys
import os
ROOT = r"c:\Users\501379.PMDC\Desktop\PRODUCAO"
sys.path.insert(0, ROOT)

import unicodedata
import re
import difflib
from agent.authorities_catalog import AUTHORITIES

queries = ["Quem é o prefeito?", "Quem é o vice-prefeito de Duque de Caxias?", "Quem é o secretário de obras?", "Quem dirige a secretaria de saúde?"]

def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in text if not unicodedata.combining(c)).lower().strip()
    t = t.replace("secretaria", "secretario")
    t = t.replace("prefeita", "prefeito")
    t = re.sub(r'\s+de\s+duque\s+de\s+caxias\b|\s+duque\s+de\s+caxias\b', '', t)
    return t.strip()

AUTHORITY_PATTERNS = [
    "quem é o",
    "quem é a",
    "quem é",
    "quem e o",
    "quem e a",
    "quem e",
    "qual é o",
    "qual é a",
    "qual é",
    "qual e o",
    "qual e a",
    "qual e",
    "quem dirige o",
    "quem dirige a",
    "quem dirige",
    "quem administra o",
    "quem administra a",
    "quem administra",
    "quem comanda o",
    "quem comanda a",
    "quem comanda",
    "quem ocupa o cargo de",
    "quem ocupa o cargo da",
    "quem ocupa o cargo",
    "o responsável pela",
    "o responsavel pela",
    "o responsável pelo",
    "o responsavel pelo",
    "qual o",
    "qual a",
]

for q in queries:
    print(f"\n====================================")
    print(f"QUERY: {q}")
    q_clean = q.lower().strip()
    q_clean = re.sub(r'^[¿\?¡\!]+|[¿\?¡\!]+$', '', q_clean).strip()
    
    for pattern in AUTHORITY_PATTERNS:
        if q_clean.startswith(pattern):
            q_clean = q_clean[len(pattern):].strip()
            break
            
    q_normalized = _normalize(q_clean)
    print(f"Cleaned & Normalized: '{q_normalized}'")
    
    matches = []
    q_norm_words = set(q_normalized.split())
    stopwords = {"de", "da", "do", "o", "a", "em", "para", "quem", "e"}
    q_clean_words = q_norm_words - stopwords
    
    for key in AUTHORITIES.keys():
        key_norm = _normalize(key)
        key_norm_words = set(key_norm.split())
        key_clean_words = key_norm_words - stopwords
        
        # Word overlap score
        word_score = 0.0
        if key_clean_words:
            intersection = q_clean_words.intersection(key_clean_words)
            word_score = len(intersection) / len(key_clean_words)
            
        # Character similarity score
        char_score = difflib.SequenceMatcher(None, q_normalized, key_norm).ratio()
        
        # Combined score
        combined_score = 0.7 * word_score + 0.3 * char_score
        
        is_sub = False
        if key_norm == q_normalized or (len(key_norm) > 3 and key_norm in q_normalized) or (len(q_normalized) > 3 and q_normalized in key_norm):
            combined_score = max(combined_score, 0.90)
            is_sub = True
            
        matches.append((key, combined_score, is_sub, word_score, char_score))
        
    matches.sort(key=lambda x: x[1], reverse=True)
    print("Top 5 Matches:")
    for key, score, is_sub, w_score, c_score in matches[:5]:
        print(f"  - '{key}': score={score:.4f} (is_sub={is_sub}, word={w_score:.2f}, char={c_score:.2f})")
