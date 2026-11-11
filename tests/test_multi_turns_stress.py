import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath("."))
from agent.agent import DuqueIAAgent

def run_stress_test(num_turns=10):
    agent = DuqueIAAgent()
    session_id = f"test_stress_{num_turns}_{int(time.time())}"
    
    # 20 cenários cobrindo todos os pontos da auditoria:
    test_suite = [
        ("T1: Saúde básica", "Onde posso tomar vacina contra gripe?"),
        ("T2: Tributário", "Como tirar a segunda via do IPTU?"),
        ("T3: Institucional", "Qual o horário de atendimento da Prefeitura?"),
        ("T4: Mudança para Obras", "Qual a função da Secretaria Municipal de Obras?"),
        ("T5: Reclamação zeladoria", "Tem um buraco enorme na minha rua, como solicito o conserto?"),
        ("T6: Transporte", "Como funciona o ônibus Tarifa Zero?"),
        ("T7: Proteção Animal", "Como faço para agendar a castração do meu cachorro no Castramóvel?"),
        ("T8: Ponto e vírgula / Pontuação", "Preciso de informações sobre certidões; poderiam me ajudar?"),
        ("T9: Competência / Aposentadoria", "Quero dar entrada na minha aposentadoria como servidor pelo IPMDC."),
        ("T10: Pergunta com travessão", "Gostaria de saber -- onde fica o Hospital Moacyr do Carmo?"),
        ("T11: Ambiguidade / Barulho", "Meu vizinho está fazendo muito barulho."),
        ("T12: Pergunta incompleta", "remédio"),
        ("T13: Consulta médica", "marcar uma consulta?"),
        ("T14: Iluminação pública", "A lâmpada do poste da minha rua está queimada há dias."),
        ("T15: Cultura e Lazer", "Quais os horários de visitação da Biblioteca Leonel Brizola?"),
        ("T16: Mudança brusca de assunto", "Qual o telefone da Ouvidoria Geral?"),
        ("T17: Limpeza e Entulho", "Como pedir retirada de entulho de obra na calçada?"),
        ("T18: Esporte", "Quais as atividades gratuitas oferecidas na Vila Olímpica?"),
        ("T19: Educação e Creche", "Quando começam as inscrições para creche municipal?"),
        ("T20: Confirmação de protocolo", "Já fiz um chamado no Colab, como acompanho o andamento?")
    ]
    
    turns_to_run = test_suite[:num_turns]
    print(f"\n=======================================================")
    print(f"INICIANDO STRESS TEST DE {num_turns} TURNOS CONSECUTIVOS")
    print(f"Session ID: {session_id}")
    print(f"=======================================================\n")
    
    summary = []
    
    for idx, (label, query) in enumerate(turns_to_run, 1):
        print(f"\n-------------------------------------------------------")
        print(f"TURNO {idx} [{label}]: \"{query}\"")
        print(f"-------------------------------------------------------")
        
        hist_before = list(DuqueIAAgent._history.get(session_id, []))
        sess_before = dict(DuqueIAAgent._session_state.get(session_id, {}))
        
        t0 = time.time()
        res_str = agent.respond(query, conversation_id=session_id)
        latency = round(time.time() - t0, 3)
        
        try:
            res = json.loads(res_str)
        except Exception as e:
            res = {"answer": res_str, "error": str(e)}
            
        intent = res.get("intent_detected", "UNKNOWN")
        nodes = res.get("_graph", {}).get("nodes_executed", [])
        answer = res.get("answer", "")
        sess_after = DuqueIAAgent._session_state.get(session_id, {})
        hist_after = DuqueIAAgent._history.get(session_id, [])
        
        colab_count = sess_after.get("colab_redirect_count", 0)
        
        # Análise de comportamento anômalo
        anomaly = None
        if "Percebi que você está com dificuldades para utilizar o aplicativo Colab" in answer:
            anomaly = "HIJACK_COLAB_LOOP (Bloqueio indevido por loop Colab)"
        elif "Não foi possível processar sua solicitação por motivos de segurança" in answer:
            anomaly = "FALSE_POSITIVE_SECURITY (Bloqueio indevido por segurança/pontuação)"
        elif "Essa solicitação foge ao âmbito das atribuições" in answer and "IPMDC" in query:
            anomaly = "FALSE_POSITIVE_COMPETENCY (Bloqueio indevido de competência municipal)"
        elif "Sou o Duque IA, seu assistente virtual" in answer and ("Tarifa Zero" in query or "como funciona" in query.lower()):
            anomaly = "HIJACK_COMO_FUNCIONA (Substituição de resposta factual por texto de ajuda genérico)"
        
        summary.append({
            "turn": idx,
            "label": label,
            "query": query,
            "intent": intent,
            "nodes": nodes,
            "colab_count": colab_count,
            "latency": latency,
            "anomaly": anomaly,
            "snippet": answer[:120].replace("\n", " ") + "..."
        })
        
        print(f"Intent: {intent}")
        print(f"Nós executados: {nodes}")
        print(f"Colab count: {colab_count}")
        print(f"Latência: {latency}s")
        if anomaly:
            print(f">>> ANOMALIA DETECTADA: {anomaly}")
        print(f"Snippet resposta: {answer[:150]}...")
        
    print("\n=======================================================")
    print("RESUMO DAS ANOMALIAS DO TESTE:")
    print("=======================================================")
    for item in summary:
        status = f"❌ {item['anomaly']}" if item['anomaly'] else "✅ OK"
        print(f"T{item['turn']:02d} | {item['intent'][:25]:<25} | {status} | {item['query'][:40]}")
        
    return summary

if __name__ == "__main__":
    turns = 10
    if len(sys.argv) > 1:
        turns = int(sys.argv[1])
    run_stress_test(turns)

