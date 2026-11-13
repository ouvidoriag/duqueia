import sys
sys.path.append(r'C:\Users\501379.PMDC\Desktop\PROJETOS\PRODUCAO')
from agent.retrieval import retrieve_structured_service, extract_query_keywords
from config.settings import DATABASE_MAIN

query = 'Como faço para legalizar ou renovar a permissão de transporte escolar em Duque de Caxias?'
words = extract_query_keywords(query)
services = retrieve_structured_service(DATABASE_MAIN, query, words, False)
for i, s in enumerate(services[:5]):
    print(f"--- Service {i+1} keys: {list(s.keys())}")
    print(f"title: {s.get('title')}, similarity: {s.get('similarity')}, semantic_score: {s.get('semantic_score')}")
