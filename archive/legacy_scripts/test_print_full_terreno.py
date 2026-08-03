import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agent.agent import DuqueIAAgent

def run():
    agent = DuqueIAAgent()
    query = "como eu solicito uma limepza de um terreno abandonado ?"
    resp_json = agent.respond(query, use_triage=True)
    data = json.loads(resp_json)
    
    print("\n========================================================")
    print("RESPOSTA COMPLETA RETORNADA PELO DUQUE IA:")
    print("========================================================")
    print(data.get("answer"))
    print("\n========================================================")
    print("FONTES UTILIZADAS:", data.get("sources"))
    print("========================================================")

if __name__ == "__main__":
    run()
