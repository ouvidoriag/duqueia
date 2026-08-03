import os
import sys
import time

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

from agent.retrieval import retrieve_context
from agent.reranker import GeminiCrossEncoder
from agent.candidate import Candidate
from agent.ranking import CandidateRanker

def test_top100_pipeline():
    print("="*75)
    print("TESTANDO PIPELINE REVOLUCIONÁRIO: TOP 100 -> CROSS ENCODER -> TOP 5")
    print("="*75)

    test_queries = [
        "Meu filho está pequeno e preciso saber onde ele pode estudar perto de casa",
        "A lâmpada da minha rua queimou e tá tudo escuro à noite",
        "Quais documentos preciso apresentar para conseguir vaga na creche?",
        "Qual é o horário de atendimento das emergências nas UPAs?",
        "A FUNDEC oferece cursos de informática ou idiomas de graça?"
    ]

    from agent.agent import DuqueIAAgent
    agent = DuqueIAAgent()

    for q in test_queries:
        print(f"\n[PERGUNTA]: \"{q}\"")
        t0 = time.time()

        from config.settings import DATABASE_MAIN
        raw_candidates = retrieve_context(
            query=q,
            db_path=DATABASE_MAIN,
            using_real=True,
            similarity_threshold=0.30,
            gemini_client=agent.gemini_client,
            reranker=agent.reranker,
            top_k=50
        )
        fetch_ms = (time.time() - t0) * 1000.0

        # Converte para objetos Candidate
        candidate_objs = [
            Candidate(
                source=r.get("source", ""),
                title=r.get("title", ""),
                category=r.get("category", ""),
                content=r.get("content", ""),
                semantic_score=r.get("semantic_score", 0.0),
                keyword_score=r.get("keyword_score", 0.0),
                retrieval_score=r.get("similarity", 0.0)
            )
            for r in raw_candidates
        ]

        # 2. Reranking Semântico Puro via CrossEncoder nos candidatos brutos
        t1 = time.time()
        reranked_objs = agent.reranker.rerank(q, candidate_objs)
        rerank_ms = (time.time() - t1) * 1000.0

        # 3. Aplicação do Boost Institucional Leve (+0.05 max para Carta Oficial)
        for c in reranked_objs:
            if "vw_ia_servicos" in c.source or "Carta de Serviços" in c.content:
                c.retrieval_score = min(round(c.retrieval_score + 0.05, 4), 1.0)

        # Ordena final pelo score ajustado
        reranked_objs.sort(key=lambda x: x.retrieval_score, reverse=True)
        top5 = reranked_objs[:5]

        print(f"  [METRICAS] Latencia: Fetch={fetch_ms:.1f}ms | Rerank CrossEncoder={rerank_ms:.1f}ms")
        print("  [TOP 3 DOCUMENTOS SELECIONADOS PELO CROSS ENCODER]:")
        for idx, c in enumerate(top5[:3], 1):
            print(f"    {idx}. [{c.source}] Score: {c.retrieval_score:.4f} | Titulo: {c.title}")

if __name__ == "__main__":
    test_top100_pipeline()
