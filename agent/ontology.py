import os
import json
import sqlite3
import unicodedata
from typing import Optional, Dict, List
from config.settings import DATABASE_MAIN

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_ONTOLOGY_PATH = os.path.join(_PROJECT_ROOT, "data", "ontology.json")

def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text_lower = text.lower().strip()
    return "".join(c for c in unicodedata.normalize('NFKD', text_lower) if not unicodedata.combining(c))


class MunicipalOntologyEngine:
    """
    Motor de Ontologia e Taxonomia Municipal do DUQUE IA.
    Carrega as entidades auditáveis de data/db/main.db (tabela municipal_entities)
    ou de data/ontology.json com renovação em memória RAM (0ms de latência de rede).
    """

    _instance = None

    def __new__(cls, db_path: str = DATABASE_MAIN):
        if cls._instance is None:
            cls._instance = super(MunicipalOntologyEngine, cls).__new__(cls)
            cls._instance.db_path = db_path
            cls._instance.entities = []
            cls._instance._load_ontology()
        return cls._instance

    def _load_ontology(self):
        """Carrega a ontologia do banco SQL ou do JSON mestre."""
        self.entities = []
        loaded = False

        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                # Verifica se a tabela municipal_entities existe
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='municipal_entities'")
                if cur.fetchone():
                    cur.execute("SELECT entity_id, entity_type, canonical_name, aliases, keywords, secretaria FROM municipal_entities WHERE active = 1")
                    for row in cur.fetchall():
                        e_id, e_type, c_name, aliases_str, kw_str, sec = row
                        try:
                            aliases = json.loads(aliases_str) if aliases_str else []
                        except Exception:
                            aliases = []
                        try:
                            keywords = json.loads(kw_str) if kw_str else []
                        except Exception:
                            keywords = []
                            
                        self.entities.append({
                            "entity_id": e_id,
                            "entity_type": e_type,
                            "canonical_name": c_name,
                            "aliases": aliases,
                            "keywords": keywords,
                            "secretaria": sec
                        })
                    loaded = True
                conn.close()
            except Exception as e:
                pass

        if not loaded and os.path.exists(JSON_ONTOLOGY_PATH):
            try:
                with open(JSON_ONTOLOGY_PATH, "r", encoding="utf-8") as f:
                    self.entities = json.load(f)
            except Exception:
                pass

    def reload(self):
        """Força a recarga da ontologia (útil após atualizações da Ouvidoria)."""
        self._load_ontology()

    def resolve_entity(self, query: str) -> Optional[Dict]:
        """
        Localiza a entidade canônica municipal baseada em sinônimos e aliases.
        Retorna um dicionário com a entidade ou None se não houver casamento.
        """
        if not query or not self.entities:
            return None

        query_norm = _normalize_text(query)

        best_entity = None
        best_score = 0.0

        for ent in self.entities:
            # Batimento por Aliases (Precisão Alta)
            for alias in ent.get("aliases", []):
                alias_norm = _normalize_text(alias)
                if alias_norm and alias_norm in query_norm:
                    score = len(alias_norm) / float(len(query_norm) + 1) + 0.5
                    if score > best_score:
                        best_score = score
                        best_entity = ent

            # Batimento por Palavras-Chave Combinadas
            kw_matches = 0
            for kw in ent.get("keywords", []):
                kw_norm = _normalize_text(kw)
                if kw_norm and kw_norm in query_norm:
                    kw_matches += 1

            if kw_matches >= 2:
                score = 0.6 + (kw_matches * 0.1)
                if score > best_score:
                    best_score = score
                    best_entity = ent

        return best_entity

    def expand_query_keywords(self, query: str) -> List[str]:
        """
        Expande a busca do cidadão derivando as palavras-chave e aliases da Ontologia Municipal.
        """
        ent = self.resolve_entity(query)
        expanded = []

        if ent:
            expanded.append(ent["canonical_name"].lower())
            for alias in ent.get("aliases", [])[:5]:
                if alias not in expanded:
                    expanded.append(alias.lower())
            for kw in ent.get("keywords", []):
                if kw not in expanded:
                    expanded.append(kw.lower())

        return expanded


# Instância global para reuso
ontology_engine = MunicipalOntologyEngine()
