import sys
sys.path.append(r'C:\Users\501379.PMDC\Desktop\PROJETOS\PRODUCAO')
from agent.agent import DuqueIAAgent
from agent.triage import perform_triage
from agent.retrieval import retrieve_context
from config.settings import DATABASE_MAIN

agent = DuqueIAAgent()
query = 'Como faço para legalizar ou renovar a permissão de transporte escolar em Duque de Caxias?'
triage_info = perform_triage(DATABASE_MAIN, query, agent.gemini_client)
print('Triage:', triage_info)

results = retrieve_context(
    query=query,
    db_path=DATABASE_MAIN,
    using_real=agent.using_real,
    similarity_threshold=agent.similarity_threshold,
    gemini_client=agent.gemini_client,
    reranker=agent.reranker,
    top_k=5,
    intent_info=triage_info
)
print('Num results:', len(results))
for i, r in enumerate(results):
    print(f"=== DOC {i+1} (score={r.get('score')}, id={r.get('id')}, title={r.get('title')}) ===")
    print((r.get('text') or r.get('content') or '')[:300])
