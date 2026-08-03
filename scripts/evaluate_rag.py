import os
import sys
import json
import time

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

GOLDEN_PATH = os.path.join(_PROJECT_ROOT, "evaluation", "golden_dataset.json")
REPORT_OUTPUT_PATH = os.path.join(_PROJECT_ROOT, "metrics", "relatorio_metricas_ir.json")

def evaluate():
    if not os.path.exists(GOLDEN_PATH):
        print(f"Dataset Golden não encontrado em: {GOLDEN_PATH}")
        return

    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        golden_data = json.load(f)

    questions = golden_data.get("questions", [])
    
    from agent.agent import DuqueIAAgent
    from agent.retrieval import retrieve_context
    from agent.ranking import CandidateRanker
    from agent.candidate import Candidate
    from agent.context_builder import ContextBuilder

    agent = DuqueIAAgent()
    
    results = []
    reciprocal_ranks = []
    recall_at_5_count = 0
    precision_at_5_scores = []
    false_negatives = 0

    print("="*70)
    print("INICIANDO AVALIAÇÃO DE MÉTRICAS CLÁSSICAS DE IR (RECALL, MRR, PRECISION)")
    print("="*70)

    for item in questions:
        qid = item["id"]
        q_text = item["query"]
        mandatory_srcs = item["mandatory_sources"]
        expected_kw = item["expected_keywords"]

        start_t = time.time()
        
        # 1. Pipeline de Busca Modular
        raw_candidates = retrieve_context(
            query=q_text,
            db_path=agent.db_path,
            using_real=agent.using_real,
            similarity_threshold=0.60,
            gemini_client=agent.gemini_client,
            reranker=agent.reranker,
            top_k=10
        )

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

        # 2. Ranking Declarativo
        ranked = CandidateRanker.apply_ranking(q_text, candidate_objs)
        confidence_level, _ = CandidateRanker.evaluate_confidence(ranked)

        # 3. Métricas de Recuperação (IR)
        sources_found = [c.source for c in ranked]
        
        # Reciprocal Rank (MRR)
        rank_pos = 0
        for idx, src in enumerate(sources_found, 1):
            if any(ms in src for ms in mandatory_srcs):
                rank_pos = idx
                break
        
        rr = (1.0 / rank_pos) if rank_pos > 0 else 0.0
        reciprocal_ranks.append(rr)

        # Recall@5
        in_top_5 = any(any(ms in src for ms in mandatory_srcs) for src in sources_found[:5])
        if in_top_5:
            recall_at_5_count += 1

        # Precision@5
        rel_in_top_5 = sum(1 for src in sources_found[:5] if any(ms in src for ms in mandatory_srcs))
        precision_at_5 = rel_in_top_5 / min(len(sources_found), 5) if sources_found else 0.0
        precision_at_5_scores.append(precision_at_5)

        raw_resp = agent.respond(q_text)
        try:
            resp_data = json.loads(raw_resp)
            answer_text = resp_data.get("answer", "")
        except Exception:
            answer_text = raw_resp
        
        says_not_found = any(p in answer_text.lower() for p in ["não encontrei", "não possuo", "não há dados", "não constam"])
        if says_not_found and len(sources_found) > 0:
            false_negatives += 1

        results.append({
            "id": qid,
            "query": q_text,
            "rank_posição_correta": rank_pos,
            "reciprocal_rank": round(rr, 4),
            "in_top_5": in_top_5,
            "precision_at_5": round(precision_at_5, 4),
            "confidence_level": confidence_level,
            "resposta": answer_text[:100] + "..."
        })

        print(f"[{qid}] RR: {rr:.2f} | In Top 5: {'[OK]' if in_top_5 else '[FAIL]'} | Confianca: {confidence_level}")

    # Cálculos Consolidados
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    recall_at_5 = (recall_at_5_count / len(questions)) * 100.0 if questions else 0.0
    mean_precision_5 = (sum(precision_at_5_scores) / len(precision_at_5_scores)) if precision_at_5_scores else 0.0
    fn_rate = (false_negatives / len(questions)) * 100.0 if questions else 0.0

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_questoes": len(questions),
        "MRR": round(mrr, 4),
        "Recall_at_5_percent": round(recall_at_5, 2),
        "Mean_Precision_at_5": round(mean_precision_5, 4),
        "False_Negative_Rate_percent": round(fn_rate, 2),
        "detalhamento": results
    }

    os.makedirs(os.path.dirname(REPORT_OUTPUT_PATH), exist_ok=True)
    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "="*70)
    print("MÉTRICAS FINAIS DE QUALIDADE DO RETRIEVAL (IR EVALUATION):")
    print(f"  MRR (Mean Reciprocal Rank) : {mrr:.4f} (Ideal: > 0.85)")
    print(f"  Recall@5                  : {recall_at_5:.1f}% (Ideal: > 90%)")
    print(f"  Precision@5               : {mean_precision_5:.4f}")
    print(f"  Taxa de Falsos Negativos   : {fn_rate:.1f}%")
    print("="*70)

if __name__ == "__main__":
    evaluate()
