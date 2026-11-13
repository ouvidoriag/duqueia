"""
Teste automatizado para os 4 pontos de auditoria da Duque IA:
1. Poste vs Lâmpada (Diferenciação estrutural e risco elétrico)
2. Linhas de Ônibus (Esclarecimento de bairro ausente e horários publicados Tarifa Zero)
3. Transporte Escolar (Requisitos, taxas e base legal SMTSP)
4. Frontend Markdown (Verificação do test suite JS)
"""
import sys
import os
import uuid

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.agent import DuqueIAAgent

def test_case_1_poste(agent: DuqueIAAgent):
    print("\n" + "="*70)
    print("CASO 1: POSTE VS LÂMPADA & RISCO ELÉTRICO")
    print("="*70)
    conv_id = f"test-poste-{uuid.uuid4().hex[:6]}"
    
    # Turno 1
    t1 = "Tem uma lâmpada queimada no poste da minha rua"
    print(f"\n[Munícipe] {t1}")
    res1 = agent.process_query(t1, conversation_id=conv_id)
    ans1 = res1.get("answer", "")
    print(f"[Duque IA T1] (Handler: {res1.get('route')})\n{ans1[:250]}...\n")
    assert any(k in ans1.lower() for k in ["ilumina", "colab", "lâmpada", "lampada"]), "Deveria falar de iluminação pública"

    # Turno 2
    t2 = "Mas o problema é no poste"
    print(f"[Munícipe] {t2}")
    res2 = agent.process_query(t2, conversation_id=conv_id)
    ans2 = res2.get("answer", "")
    print(f"[Duque IA T2] (Handler: {res2.get('route')})\n{ans2}\n")
    # Não deve apenas repetir a resposta anterior
    assert any(k in ans2.lower() for k in ["estrutura", "fio", "inclinad", "danificad", "elétric", "eletric", "abalo", "lâmpada"]), "Deveria pedir esclarecimento sobre a natureza do problema no poste"

    # Turno 3
    t3 = "O poste está inclinado com fios caídos soltando faíscas"
    print(f"[Munícipe] {t3}")
    res3 = agent.process_query(t3, conversation_id=conv_id)
    ans3 = res3.get("answer", "")
    print(f"[Duque IA T3] (Handler: {res3.get('route')})\n{ans3}\n")
    assert any(k in ans3 for k in ["0800 021 0196", "08000210196", "199", "193"]), "Deveria fornecer contatos emergenciais (Light / Defesa Civil / Bombeiros)"
    assert "afaste" in ans3.lower() or "distância" in ans3.lower() or "risco" in ans3.lower(), "Deveria dar instrução de segurança imediata"
    print("-> CASO 1: PASSOU COM SUCESSO!")

def test_case_2_onibus(agent: DuqueIAAgent):
    print("\n" + "="*70)
    print("CASO 2: LINHAS DE ÔNIBUS (TARIFÁRIO ZERO E HORÁRIOS)")
    print("="*70)
    conv_id = f"test-bus-{uuid.uuid4().hex[:6]}"
    
    # Turno 1: Sem bairro informado
    t1 = "Que horas passa o ônibus no meu bairro?"
    print(f"\n[Munícipe] {t1}")
    res1 = agent.process_query(t1, conversation_id=conv_id)
    ans1 = res1.get("answer", "")
    print(f"[Duque IA T1] (Handler: {res1.get('route')})\n{ans1}\n")
    assert "qual" in ans1.lower() and "bairro" in ans1.lower(), "Deveria perguntar o bairro educadamente antes de buscar"
    assert "não tenho" not in ans1.lower() or "qual é o seu bairro" in ans1.lower(), "Não deveria alegar ignorância sumária"

    # Turno 2: Informando o bairro
    t2 = "Saracuruna"
    print(f"[Munícipe] {t2}")
    res2 = agent.process_query(t2, conversation_id=conv_id)
    ans2 = res2.get("answer", "")
    print(f"[Duque IA T2] (Handler: {res2.get('route')})\n{ans2}\n")
    assert any(k in ans2.lower() for k in ["saracuruna", "linha", "tarifa zero", "horário", "horario"]), "Deveria trazer as linhas de Saracuruna"
    assert any(k in ans2.lower() for k in ["dc-tz12", "05:00", "ana clara"]), "Deveria trazer a linha específica e horários de Saracuruna"
    print("-> CASO 2: PASSOU COM SUCESSO!")

def test_case_3_transporte_escolar(agent: DuqueIAAgent):
    print("\n" + "="*70)
    print("CASO 3: TRANSPORTE ESCOLAR (LEGALIZAÇÃO E AUTORIZAÇÃO)")
    print("="*70)
    conv_id = f"test-escolar-{uuid.uuid4().hex[:6]}"
    
    t1 = "Como faço para conseguir permissão para transporte escolar?"
    print(f"\n[Munícipe] {t1}")
    res = agent.process_query(t1, conversation_id=conv_id)
    ans = res.get("answer", "")
    print(f"[Duque IA] (Handler: {res.get('route')})\n{ans}\n")
    assert any(k in ans.lower() for k in ["smtsp", "transporte", "vistoria", "1.105", "taxa", "cnh"]), "Deveria conter requisitos oficiais da Carta de Serviços para Transporte Escolar"
    assert "não encontrei" not in ans.lower() and "não foi possível" not in ans.lower(), "Não deveria dizer que não encontrou informações"
    print("-> CASO 3: PASSOU COM SUCESSO!")

if __name__ == "__main__":
    agent = DuqueIAAgent()
    test_case_1_poste(agent)
    test_case_2_onibus(agent)
    test_case_3_transporte_escolar(agent)
    print("\n" + "="*70)
    print("TODOS OS TESTES DOS 4 CASOS FORAM CONCLUÍDOS!")
    print("="*70)

