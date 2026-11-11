"""
agent/synonyms.py — DUQUE IA
============================
Módulo de Normalização Semântica e Dicionário de Sinônimos Populares.
Mapeia expressões coloquiais da Baixada Fluminense para termos técnicos e oficiais
da Prefeitura de Duque de Caxias em sub-1ms (em memória).
"""

import os
import json
from typing import Optional, Dict

_SYNONYM_MAP: Optional[Dict[str, str]] = None
_SYNONYM_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "synonyms", "dicionario_sinonimos.json"))

def _load_synonyms() -> Dict[str, str]:
    """Carrega o dicionário de sinônimos em memória na primeira chamada."""
    global _SYNONYM_MAP
    if _SYNONYM_MAP is not None:
        return _SYNONYM_MAP

    syn_map: Dict[str, str] = {}
    if os.path.exists(_SYNONYM_FILE):
        try:
            with open(_SYNONYM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                official = item.get("termo_oficial")
                if not official:
                    continue
                for syn in item.get("sinonimos_e_variacoes", []):
                    syn_lower = syn.strip().lower()
                    if len(syn_lower) >= 3 and syn_lower not in syn_map:
                        syn_map[syn_lower] = official
        except Exception:
            pass
    _SYNONYM_MAP = syn_map
    return _SYNONYM_MAP

def get_canonical_term(term: str) -> Optional[str]:
    """Retorna o termo oficial associado a um sinônimo popular, se houver."""
    if not term:
        return None
    syn_map = _load_synonyms()
    return syn_map.get(term.strip().lower())

def expand_query_with_synonyms(query: str) -> str:
    """
    Identifica expressões populares presentes na consulta do munícipe e anexa
    o termo oficial entre parênteses para enriquecer a busca vetorial e textual.
    """
    if not query:
        return query
    syn_map = _load_synonyms()
    q_lower = query.lower()
    
    additions = []
    for syn, official in syn_map.items():
        if len(syn) >= 4 and syn in q_lower and official.lower() not in q_lower:
            if official not in additions:
                additions.append(official)
                if len(additions) >= 2:
                    break
                    
    if additions:
        return f"{query} ({', '.join(additions)})"
    return query
