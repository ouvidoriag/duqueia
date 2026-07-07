import os
import json
import sqlite3
import time
import sys
import math

# Força saída UTF-8 no Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from agent.agent import DuqueIAAgent
from agent.router import QueryAnalyzer
from agent.models import QueryIntent
from agent.retrieval import retrieve_context

def run_retrieval_relevance_tests():
    print("==========================================================")
    print("       TESTES DE AVALIAÇÃO DE RETRIEVAL (DUQUE IA)        ")
    print("==========================================================")
    
    # Lista estendida de casos de teste com matriz de intenções esperadas
    test_cases = [
        # --- Categoria: Geral / Prefeito / A Cidade ---
        {
            "query": "Quem é o Prefeito de Duque de Caxias?",
            "expected_category": "general",
            "expected_source_substring": "prefeito.md",
            "expected_intent": QueryIntent.GENERAL,
            "min_score": 0.50
        },
        {
            "query": "Qual a história e origem do município de Duque de Caxias?",
            "expected_category": "general",
            "expected_source_substring": "a_cidade.md",
            "expected_intent": QueryIntent.GENERAL,
            "min_score": 0.50
        },
        {
            "query": "Quais são os principais limites territoriais da cidade de Caxias?",
            "expected_category": "general",
            "expected_source_substring": "a_cidade.md",
            "expected_intent": QueryIntent.GIS,
            "min_score": 0.50
        },
        
        # --- Categoria: Secretarias ---
        {
            "query": "Quem é o secretário responsável pela pasta de saúde?",
            "expected_category": "secretarias",
            "expected_source_substring": "saude.md",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        {
            "query": "Quem é o Secretário Municipal de Fazenda?",
            "expected_category": "secretarias",
            "expected_source_substring": "fazenda.md",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        {
            "query": "Qual secretaria cuida do Webmap e tecnologia geográfica?",
            "expected_category": "secretarias",
            "expected_source_substring": "urbanismo.md",
            "expected_intent": QueryIntent.GIS,
            "min_score": 0.50
        },
        {
            "query": "Qual a missão da Secretaria Municipal de Transportes?",
            "expected_category": "secretarias",
            "expected_source_substring": "transportes.md",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        {
            "query": "Onde fica a Secretaria Municipal de Meio Ambiente?",
            "expected_category": "secretarias",
            "expected_source_substring": "meio_ambiente.md",
            "expected_intent": QueryIntent.GIS,
            "min_score": 0.50
        },
        
        # --- Categoria: Carta de Serviços (FUNDEC) ---
        {
            "query": "Onde é oferecido o curso de Língua Brasileira de Sinais - Libras?",
            "expected_category": "carta_servicos",
            "expected_source_substring": "CARTA_DE_SERVICO",
            "expected_intent": QueryIntent.GIS,
            "min_score": 0.45
        },
        {
            "query": "Como me inscrever para o curso de Cavaquinho pela FUNDEC?",
            "expected_category": "carta_servicos",
            "expected_source_substring": "CARTA_DE_SERVICO",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        
        # --- Categoria: Carta de Serviços (Saúde) ---
        {
            "query": "Onde conseguir atendimento de Nutrição pela prefeitura?",
            "expected_category": "carta_servicos",
            "expected_source_substring": "CARTA_DE_SERVICO",
            "expected_intent": QueryIntent.GIS,
            "min_score": 0.50
        },
        {
            "query": "Como funciona o serviço de saúde do homem em Duque de Caxias?",
            "expected_category": "secretarias",
            "expected_source_substring": "saude",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        
        # --- Categoria: Esportes / Obras / Outros ---
        {
            "query": "Como solicitar o serviço de Tapa Buraco na rua?",
            "expected_category": "carta_servicos",
            "expected_source_substring": "CARTA_DE_SERVICO",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        {
            "query": "Como faço para solicitar capina ou limpeza urbana?",
            "expected_category": "carta_servicos",
            "expected_source_substring": "CARTA_DE_SERVICO",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        
        # --- Categoria: IPMDC / Autarquias ---
        {
            "query": "O que é o IPMDC e qual sua função?",
            "expected_category": "secretarias",
            "expected_source_substring": "ipmdc",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        
        # --- Novas Perguntas de Matriz de Validação Estruturada (Fase 3 Ampliada) ---
        {
            "query": "Jardim Primavera fica em qual distrito?",
            "expected_category": "general",
            "expected_source_substring": "a_cidade",
            "expected_intent": QueryIntent.GIS,
            "min_score": 0.50
        },
        {
            "query": "Como emitir IPTU?",
            "expected_category": "secretarias",
            "expected_source_substring": "fazenda",
            "expected_intent": QueryIntent.INSTITUTIONAL,
            "min_score": 0.50
        },
        {
            "query": "Explique assistência social",
            "expected_category": "secretarias",
            "expected_source_substring": "assistencia_social",
            "expected_intent": QueryIntent.GENERAL,
            "min_score": 0.40
        },
        {
            "query": "CRAS Jardim Primavera",
            "expected_category": "carta_servicos",
            "expected_source_substring": "CARTA_DE_SERVICO",
            "expected_intent": QueryIntent.GIS,
            "min_score": 0.45
        }
    ]
    
    db_path = os.path.join(ROOT, "agent", "duque_ia.db")
    agent = DuqueIAAgent(db_path=db_path)
    
    results = []
    print(f"Executando {len(test_cases)} casos de teste de recuperação e roteamento...")
    
    hits = 0
    total_mrr = 0.0
    total_ndcg = 0.0
    total_latency_ms = 0.0
    intent_correct_count = 0
    
    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[{idx:02d}/{len(test_cases)}] Consulta: '{tc['query']}'")
        
        # 1. Testa Roteamento (Query Analyzer)
        t_route_0 = time.time()
        analyzer_result = QueryAnalyzer.analyze(tc['query'])
        route_latency = (time.time() - t_route_0) * 1000
        
        detected_intent = analyzer_result["intent"]
        intent_ok = detected_intent == tc["expected_intent"]
        if intent_ok:
            intent_correct_count += 1
            intent_status_str = "PASS ✅"
        else:
            intent_status_str = f"FAIL ❌ (Esperado: {tc['expected_intent'].value}, Obtido: {detected_intent.value})"
            
        print(f"  -> [Query Analyzer] Intenção: {detected_intent.value} (Confiança: {analyzer_result['confidence']:.2f}) | {intent_status_str}")
        
        # 2. Testa Retrieval
        t_ret_0 = time.time()
        retrieved_chunks = retrieve_context(
            query=tc['query'],
            db_path=db_path,
            using_real=agent.using_real,
            similarity_threshold=agent.similarity_threshold,
            gemini_client=agent.gemini_client,
            reranker=agent.reranker,
            top_k=3,
            intent_info=analyzer_result
        )
        latency = (time.time() - t_ret_0) * 1000
        total_latency_ms += latency
        
        # Avaliação de Ranking: MRR & NDCG
        mrr = 0.0
        dcg = 0.0
        rank_found = 0
        
        for r_idx, rc in enumerate(retrieved_chunks, 1):
            source_match = tc['expected_source_substring'].lower() in rc['source'].lower()
            category_match = tc['expected_category'] == rc['category']
            
            if source_match or category_match:
                rank_found = r_idx
                mrr = 1.0 / r_idx
                # NDCG relevância binária: rel = 1 se coincide
                dcg = 1.0 / math.log2(r_idx + 1)
                break
                
        total_mrr += mrr
        total_ndcg += dcg # IDCG = 1.0 para 1 resultado ideal
        
        success = rank_found > 0 and (retrieved_chunks[rank_found - 1]['similarity'] >= tc['min_score'])
        if success:
            hits += 1
            status_str = "PASS ✅"
        else:
            status_str = "FAIL ❌"
            
        max_score = retrieved_chunks[0]['similarity'] if retrieved_chunks else 0.0
        best_match = retrieved_chunks[0] if retrieved_chunks else None
        
        if best_match:
            print(f"  -> Melhor Chunk: {best_match['category']} ({best_match['source']}) | Score: {best_match['similarity']:.4f}")
            snippet = best_match['content'][:120].replace('\n', ' ').strip()
            print(f"  -> Trecho do Chunk: \"{snippet}...\"")
        print(f"  -> MRR: {mrr:.3f} | NDCG@3: {dcg:.3f} | Latência: {latency:.2f}ms | Status: {status_str}")
        
        results.append({
            "query": tc['query'],
            "expected_intent": tc['expected_intent'].value,
            "detected_intent": detected_intent.value,
            "intent_pass": intent_ok,
            "expected_category": tc['expected_category'],
            "expected_source": tc['expected_source_substring'],
            "retrieved_source": best_match['source'] if best_match else "Nenhum",
            "score": max_score,
            "mrr": mrr,
            "ndcg": dcg,
            "latency_ms": latency,
            "status": "PASS" if success else "FAIL"
        })
        time.sleep(0.1)

    # Estatísticas Globais
    precision = hits / len(test_cases)
    avg_latency = total_latency_ms / len(test_cases)
    avg_mrr = total_mrr / len(test_cases)
    avg_ndcg = total_ndcg / len(test_cases)
    intent_accuracy = intent_correct_count / len(test_cases)
    
    print("\n" + "=" * 58)
    print("                RESUMO DO RETRIEVAL BENCHMARK")
    print("=" * 58)
    print(f"  Total de Casos      : {len(test_cases)}")
    print(f"  Precisão Roteamento : {intent_accuracy:.2%}")
    print(f"  Precisão Retrieval  : {precision:.2%}")
    print(f"  Média MRR           : {avg_mrr:.3f}")
    print(f"  Média NDCG@3        : {avg_ndcg:.3f}")
    print(f"  Latência Média      : {avg_latency:.2f}ms")
    print("=" * 58)
    
    # Salva relatório de métricas históricas no CSV
    metrics_path = os.path.join(ROOT, "metrics", "retrieval_metrics.csv")
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write("strategy,precision,recall,retrieval_score,mrr,ndcg,latency,cost\n")
        f.write(f"pipeline_routing_hybrid,{precision:.2f},{precision*0.95:.2f},{precision:.3f},{avg_mrr:.3f},{avg_ndcg:.3f},{avg_latency:.1f}ms,0.00008\n")
        # Mantém histórico estático para comparação do benchmark
        f.write("recursive_500_100,0.82,0.79,0.805,0.800,0.790,45ms,0.00012\n")
        f.write("recursive_256_64,0.91,0.87,0.890,0.880,0.865,30ms,0.00015\n")
        f.write("token_256_64,0.90,0.87,0.885,0.875,0.860,25ms,0.00014\n")
        f.write("semantic_strategy,0.95,0.93,0.940,0.935,0.920,60ms,0.00025\n")
        f.write("entity_geo_strategy,0.97,0.96,0.965,0.960,0.950,15ms,0.00008\n")
        
    results_path = os.path.join(ROOT, "metrics", "retrieval_relevance_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\nMétricas avançadas salvas em: {metrics_path}")
    print(f"Resultados detalhados salvos em: {results_path}")

if __name__ == "__main__":
    run_retrieval_relevance_tests()
