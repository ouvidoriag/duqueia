import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.agent import DuqueIAAgent


def run_flow(agent: DuqueIAAgent, cid: str, turns: list):
    print("=" * 72)
    print(f"SESSÃO: {cid}")
    for i, msg in enumerate(turns, 1):
        res = agent.process_query(msg, conversation_id=cid)
        ans = res.get("answer", "")
        intent = res.get("intent_detected", "")
        print(f"\n[Turno {i}] Munícipe: {msg}")
        print(f"[Intent: {intent}]")
        print(f"DUQUE IA:\n{ans}")
        yield i, msg, intent, ans


def main():
    agent = DuqueIAAgent()

    # Fluxo 1: Reprodução exata da conversa problemática reportada
    cid1 = f"flow_buraco_{int(time.time())}"
    turns1 = [
        "Eu quero abrir uma reclamação.",
        "Você que vai abrir?",
        "Era sobre rua.",
        "Rua A.",
        "buraco",
        "mas aí eu marco o quê?",
    ]
    results1 = list(run_flow(agent, cid1, turns1))

    # Asserções obrigatórias do Fluxo 1
    _, _, intent2, ans2 = results1[1]
    assert intent2 != "ai_meta_info", f"Turno 2 caiu indevidamente em ai_meta_info: {ans2}"
    assert "não consigo" in ans2.lower() or "colab" in ans2.lower(), f"Turno 2 não respondeu diretamente se abre protocolo: {ans2}"

    _, _, _, ans4 = results1[3]
    assert "qual é o problema" in ans4.lower() or "problema" in ans4.lower(), f"Turno 4 encerrou coleta antes de perguntar qual era o problema na Rua A: {ans4}"
    assert "rua a" in ans4.lower(), f"Turno 4 perdeu a referência 'Rua A': {ans4}"

    _, _, _, ans5 = results1[4]
    assert "rua a" in ans5.lower(), f"Turno 5 perdeu a localização 'Rua A': {ans5}"
    assert "buraco" in ans5.lower(), f"Turno 5 perdeu o problema 'buraco': {ans5}"
    assert "tapa-buraco" in ans5.lower() or "zeladoria urbana" in ans5.lower(), f"Turno 5 não identificou categoria Colab correta: {ans5}"
    assert "duquedecaxias.colab.re" in ans5.lower(), f"Turno 5 não forneceu link do Colab: {ans5}"

    _, _, _, ans6 = results1[5]
    assert "tapa-buraco" in ans6.lower() or "zeladoria urbana" in ans6.lower(), f"Turno 6 perdeu categoria ao perguntar 'mas aí eu marco o quê?': {ans6}"

    # Verificação global de segurança/formatação em todos os turnos
    for i, _, _, ans in results1:
        assert "99824" not in ans, f"Vazamento de número proibido no turno {i}: {ans}"
        assert not ("whatsapp" in ans.lower() and "ouvidoria" in ans.lower()), f"Menção a WhatsApp da Ouvidoria no turno {i}: {ans}"
        assert ans.count("**") % 2 == 0, f"Markdown desbalanceado no turno {i}: {ans}"

    # Fluxo 2: Conversa natural, pergunta de capacidade e mudança de assunto (regressão reportada)
    cid2 = f"flow_conversa_{int(time.time())}"
    turns2 = [
        "Olá",
        "Você faz oq?",
        "Eu queria conversar",
        "Quero reclamar de um buraco na minha rua",
        "Na verdade, deixa isso, quero saber sobre IPTU",
    ]
    results2 = list(run_flow(agent, cid2, turns2))

    assert results2[0][2] == "saudacao", f"Turno 1 deveria ser saudacao: {results2[0]}"
    assert not results2[1][2].startswith("ouvidoria"), f"Turno 2 ('Você faz oq?') caiu indevidamente na Ouvidoria: {results2[1]}"
    assert not results2[2][2].startswith("ouvidoria"), f"Turno 3 ('Eu queria conversar') caiu indevidamente na Ouvidoria: {results2[2]}"
    assert "vistoria" not in results2[2][3].lower(), f"Turno 3 gerou solicitação fictícia: {results2[2][3]}"
    assert "buraco" in results2[3][3].lower() or "rua" in results2[3][3].lower(), f"Turno 4 não reconheceu reclamação de buraco: {results2[3]}"
    assert "iptu" in results2[4][3].lower(), f"Turno 5 não mudou de assunto para IPTU: {results2[4]}"

    # Fluxo 3: Sequência obrigatória de 7 turnos + retomada após mudança de assunto
    cid3 = f"flow_7turnos_{int(time.time())}"
    turns3 = [
        "Olá",
        "Queria abrir uma manifestação",
        "Buraco",
        "Rua A, Centro",
        "Você consegue abrir por mim?",
        "Na verdade quero falar de IPTU",
        "Quero voltar ao buraco",
    ]
    results3 = list(run_flow(agent, cid3, turns3))

    assert results3[0][2] == "saudacao", f"F3 Turno 1 deveria ser saudacao: {results3[0]}"
    assert "queria abrir" not in results3[1][3].lower(), f"F3 Turno 2 tratou intenção como endereço: {results3[1][3]}"
    assert "assunto" in results3[1][3].lower() or "problema" in results3[1][3].lower(), f"F3 Turno 2 não perguntou assunto/problema: {results3[1][3]}"
    assert "rua" in results3[2][3].lower() and "bairro" in results3[2][3].lower(), f"F3 Turno 3 não pediu rua e bairro: {results3[2][3]}"
    assert "rua a, centro" in results3[3][3].lower() and "queria abrir" not in results3[3][3].lower(), f"F3 Turno 4 não preservou Rua A, Centro ou vazou intenção: {results3[3][3]}"
    assert ("não consigo" in results3[4][3].lower() or "colab" in results3[4][3].lower()) and "rua a, centro" in results3[4][3].lower(), f"F3 Turno 5 não respondeu capacidade ou perdeu Rua A, Centro: {results3[4][3]}"
    assert "iptu" in results3[5][3].lower(), f"F3 Turno 6 não mudou para IPTU: {results3[5]}"
    assert "buraco" in results3[6][3].lower() and "rua a, centro" in results3[6][3].lower(), f"F3 Turno 7 não retomou buraco + Rua A, Centro: {results3[6][3]}"

    print("\n✅ TODOS OS TESTES DE CONTINUIDADE E CONVERSA NATURAL PASSARAM COM 100% DE SUCESSO!")


if __name__ == "__main__":
    main()

