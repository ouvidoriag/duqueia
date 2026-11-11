import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
from agent.agent import DuqueIAAgent

def test_authorities():
    agent = DuqueIAAgent()
    queries = [
        "quem é netinho reis",
        "quem é o prefeito",
        "quem é o secretário de obras",
        "quem é boquinha"
    ]

    for q in queries:
        resp = json.loads(agent.respond(q))
        print(f"\n==============================================")
        print(f"QUERY: '{q}'")
        print(f"Intent: {resp.get('intent_detected')}")
        print(f"Resposta:\n{resp.get('answer')}")

if __name__ == "__main__":
    test_authorities()

