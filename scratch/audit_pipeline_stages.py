import os
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(ROOT, "metrics", "audit_benchmark_etapa2.json")

def analyze_stages():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("detailed_results", [])
    total = len(results)
    
    triage_ok = 0
    rewrite_ok = 0
    retrieval_ok = 0
    reranker_ok = 0
    prompt_builder_ok = 0
    gemini_ok = 0
    guardrail_ok = 0
    
    for r in results:
        code = r["root_cause_diagnosis"]["code"]
        triage = r.get("triage", {})
        rewrite = r.get("query_rewriting", {})
        retrieval = r.get("retrieval", {})
        reranking = r.get("reranking", {})
        gen = r.get("generation", {})
        
        # 1. Triagem
        if code != "TRIAGE_BYPASS" and code != "TRIAGE_ROUTING_ERROR":
            triage_ok += 1
            
        # 2. Query Rewrite
        if not rewrite.get("entity_loss") and not rewrite.get("entity_substitution"):
            rewrite_ok += 1
            
        # 3. Retrieval
        if retrieval.get("retrieval_executed", True):
            retrieval_ok += 1
            
        # 4. Reranker
        if code != "RERANKER_DEGRADATION":
            reranker_ok += 1
            
        # 5. Prompt Builder
        if r.get("context_chunks_sent_to_llm") is not None:
            prompt_builder_ok += 1
            
        # 6. Gemini LLM Grounding
        if code != "LLM_HALLUCINATION":
            gemini_ok += 1
            
        # 7. Output Guardrail
        if code != "FALSE_NEGATIVE_GUARDRAIL":
            guardrail_ok += 1
            
    print("=" * 70)
    print("   CONSOLIDAÇÃO DE EFICIÊNCIA POR ETAPA DO PIPELINE (30 PERGUNTAS)")
    print("=" * 70)
    print(f"  1. Triagem (Triage)            : {triage_ok}/{total} ({round((triage_ok/total)*100, 2)}%)")
    print(f"  2. Reescrita de Query          : {rewrite_ok}/{total} ({round((rewrite_ok/total)*100, 2)}%)")
    print(f"  3. Retrieval Híbrido           : {retrieval_ok}/{total} ({round((retrieval_ok/total)*100, 2)}%)")
    print(f"  4. Re-ranker (Cross-Encoder)   : {reranker_ok}/{total} ({round((reranker_ok/total)*100, 2)}%)")
    print(f"  5. Prompt Builder              : {prompt_builder_ok}/{total} ({round((prompt_builder_ok/total)*100, 2)}%)")
    print(f"  6. Geração Gemini (Grounding)  : {gemini_ok}/{total} ({round((gemini_ok/total)*100, 2)}%)")
    print(f"  7. Output Guardrail            : {guardrail_ok}/{total} ({round((guardrail_ok/total)*100, 2)}%)")
    print("=" * 70)

if __name__ == "__main__":
    analyze_stages()
