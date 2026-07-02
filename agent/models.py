from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class QueryIntent(Enum):
    GIS = "gis"
    INSTITUTIONAL = "institutional"
    GENERAL = "general"
    LIST = "list"

@dataclass
class TriageInfo:
    intent: str
    tipo_manifestacao: Optional[str]
    confidence: float
    needs_clarification: bool
    reason: str
    source: Optional[str] = None

@dataclass
class QueryContext:
    text: str
    intent: QueryIntent
    confidence: float
    entities: List[Dict[str, Any]]
    list_config: Optional[Dict[str, Any]] = None

@dataclass
class RetrievalResult:
    source: str
    category: str
    content: str
    title: str
    similarity: float
    semantic_score: float
    chunk_keywords: List[str]
    is_list_result: bool = False
