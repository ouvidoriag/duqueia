import os
import sys
import json

# Set up project path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from agent.agent import DuqueIAAgent
from agent.retrieval import retrieve_context
from agent.router import QueryAnalyzer

agent = DuqueIAAgent()
query = "Como dar entrada no ISS da minha empresa?"
print("Analyzing query...")
intent_info = QueryAnalyzer.analyze(query, agent.gemini_client)
print("Intent:", intent_info)

print("Retrieving context...")
results = retrieve_context(
    query, agent.db_path, agent.using_real, agent.similarity_threshold,
    agent.gemini_client, agent.reranker, top_k=3, intent_info=intent_info
)

print("\n--- RESULTS ---")
for i, r in enumerate(results):
    print(f"\n[{i}] Source: {r['source']} | Title: {r['title']} | Similarity: {r['similarity']}")
    print(f"Content:\n{r['content']}")
