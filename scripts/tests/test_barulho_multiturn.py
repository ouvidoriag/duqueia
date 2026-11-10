"""
test_barulho_multiturn.py
Validação automatizada de continuidade conversacional e desambiguação multi-turno:
Turno 1: 'quero abrir uma reclamação' -> Acolhimento neutro e resolutivo (sem tom de pesar).
Turno 2: 'meu vizinho tá com som alto' -> Orientação autoexplicativa e resolutiva (residência 190 vs comércio Colab).
Turno 3: 'estabelecimento comercial' -> Mantém contexto de som alto em comércio (Ordem Pública / Colab),
sem desviar para servidor público/secretaria municipal e orienta via Colab/Ouvidoria.
"""
import os
import sys
import json
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv()

from agent.main import DuqueIAAgent

def test_full_3turn_dialog():
    agent = DuqueIAAgent()
    print("==========================================================")
    print("  TESTE DE REGRESSÃO: FLUXO COMPLETO MULTI-TURNO (3 TURNOS) ")
    print("==========================================================")

    # ── Turno 1: Declaração de Intenção ──────────────────────────────────────
    t0 = time.time()
    r1_str = agent.respond("quero abrir uma reclamação", use_triage=True)
    d1 = json.loads(r1_str)
    dur1 = (time.time() - t0) * 1000
    cid = d1.get("conversation_id")
    ans1 = d1.get("answer", "")

    print(f"\n[Turno 1] 'quero abrir uma reclamação'")
    print(f"  Latência: {dur1:.1f}ms | Intent: {d1.get('intent_detected')}")
    print(f"  Resposta 1:\n{ans1}\n")

    ans1_lower = ans1.lower()
    assert not ("que pena" in ans1_lower or "sinto muito que você precise" in ans1_lower), (
        "ERRO: Resposta usou tom de pesar inadequado ('que pena')"
    )
    assert any(w in ans1_lower for w in ["assunto", "qual é", "qual o assunto", "manifestação"]), (
        "ERRO: Resposta não solicitou o assunto da manifestação"
    )

    # ── Turno 2: Apresentação do Assunto ─────────────────────────────────────
    t1 = time.time()
    r2_str = agent.respond("meu vizinho tá com som alto", use_triage=True, conversation_id=cid)
    d2 = json.loads(r2_str)
    dur2 = (time.time() - t1) * 1000
    ans2 = d2.get("answer", "")

    print(f"[Turno 2] 'meu vizinho tá com som alto'")
    print(f"  Latência: {dur2:.1f}ms | Intent: {d2.get('intent_detected')}")
    print(f"  Resposta 2:\n{ans2}\n")

    ans2_lower = ans2.lower()
    assert "190" in ans2 or "militar" in ans2_lower, "Turno 2 deveria orientar 190 para residência particular"
    assert "colab" in ans2_lower or "ordem pública" in ans2_lower or "comércio" in ans2_lower, "Turno 2 deveria orientar Colab para comércio/rua"

    # ── Turno 3: Esclarecimento do Local / Tipo ──────────────────────────────
    t2 = time.time()
    r3_str = agent.respond("estabelecimento comercial", use_triage=True, conversation_id=cid)
    d3 = json.loads(r3_str)
    dur3 = (time.time() - t2) * 1000
    ans3 = d3.get("answer", "")

    print(f"[Turno 3] 'estabelecimento comercial'")
    print(f"  Latência: {dur3:.1f}ms | Intent: {d3.get('intent_detected')}")
    print(f"  Resposta 3:\n{ans3}\n")

    # Asserções críticas contra regressão do bug relatado
    ans3_lower = ans3.lower()
    assert not ("servidor da prefeitura" in ans3_lower or "servidor público municipal" in ans3_lower), (
        "ERRO CRÍTICO: Desviou para conduta de servidor da prefeitura!"
    )
    assert not ("em qual secretaria, posto ou órgão" in ans3_lower or "em qual secretaria ou unidade" in ans3_lower), (
        "ERRO CRÍTICO: Fez pergunta desconectada sobre secretaria/órgão!"
    )
    assert any(w in ans3_lower for w in ["ordem pública", "ordem publica", "meio ambiente", "colab", "poluição sonora", "ruído", "ruido", "som"]), (
        "ERRO: Perdeu contexto de poluição sonora / ordem pública!"
    )
    assert d3.get("intent_detected") != "possivel_denuncia_redirect", (
        "ERRO: Classificou indevidamente como possivel_denuncia_redirect!"
    )

    print("==========================================================")
    print("  SUCESSO: Fluxo de 3 turnos validado com total precisão!")
    print("==========================================================")

if __name__ == "__main__":
    test_full_3turn_dialog()
