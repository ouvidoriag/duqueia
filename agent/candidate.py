from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class Candidate:
    """
    Objeto tipado único que representa um candidato de recuperação (estruturado ou vetorial).
    Garante que todos os atributos sejam tipados e expõe a explicabilidade do ranking.
    """
    source: str
    title: str
    category: str
    content: str
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    retrieval_score: float = 0.0
    rrf_score: float = 0.0
    doc_id: str = ""
    parent_context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_keywords: List[str] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)

    def add_explanation(self, text: str):
        """Adiciona uma justificativa de explicabilidade para o score de ranking."""
        self.explanations.append(text)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o candidato em dicionário mantendo compatibilidade."""
        return {
            "source": self.source,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "semantic_score": self.semantic_score,
            "keyword_score": self.keyword_score,
            "similarity": self.retrieval_score,  # Alias de retrocompatibilidade
            "retrieval_score": self.retrieval_score,
            "rrf_score": self.rrf_score,
            "doc_id": self.doc_id,
            "parent_context": self.parent_context,
            "metadata": self.metadata,
            "chunk_keywords": self.chunk_keywords,
            "explanations": self.explanations
        }
