from abc import ABC, abstractmethod

class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidates: list) -> list:
        pass

class NoOpReranker(BaseReranker):
    def rerank(self, query: str, candidates: list) -> list:
        return candidates
