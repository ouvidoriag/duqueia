import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.fallback import build_controlled_web_fallback
from agent.agent import DuqueIAAgent

def test():
    agent = DuqueIAAgent()
    q = "quantos hospitais temos em caxias ?"
    print("Testing build_controlled_web_fallback directly...")
    res = build_controlled_web_fallback(q, agent.gemini_client)
    print("RES KEYS:", res.keys())
    print("IS_WEB_FALLBACK:", res.get("is_web_fallback"))
    print("CONFIDENCE:", res.get("confidence"))
    print("SOURCES:", res.get("sources"))
    print("ANSWER:\n", res.get("answer"))

if __name__ == "__main__":
    test()
