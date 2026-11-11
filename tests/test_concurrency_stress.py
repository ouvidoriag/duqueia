import os
import sys
import time
import json
import uuid
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath("."))
from agent.agent import DuqueIAAgent
from config.settings import DATABASE_TELEMETRY

# Perguntas que cobrem diferentes handlers (Golden Source, Authority, Entity, RAG)
QUESTIONS_POOL = [
    "Qual o telefone da Ouvidoria?",
    "Quem é o prefeito?",
    "Qual a função da Secretaria de Obras?",
    "Onde fica o Hospital Moacyr do Carmo?",
    "Como tirar a segunda via do IPTU?",
    "Quem é netinho reis?",
    "Qual o horário de atendimento da Prefeitura?",
    "Como funciona o ônibus Tarifa Zero?",
    "Onde posso tomar vacina contra gripe?",
    "Quais as atividades gratuitas oferecidas na Vila Olímpica?"
]

def simulate_user_session(user_idx: int, num_turns: int = 10):
    """Simula uma sessão completa de um cidadão realizando múltiplos turnos."""
    session_id = f"sess_user_{user_idx:02d}_{uuid.uuid4().hex[:8]}"
    agent = DuqueIAAgent()
    
    session_log = []
    
    for turn_idx in range(num_turns):
        query = QUESTIONS_POOL[turn_idx % len(QUESTIONS_POOL)]
        # Insere marcador único para checagem estrita de não-contaminação
        tagged_query = f"{query} [tag_u{user_idx}_t{turn_idx}]"
        
        t0 = time.time()
        try:
            resp_str = agent.respond(tagged_query, conversation_id=session_id)
            elapsed = time.time() - t0
            
            try:
                resp_json = json.loads(resp_str)
                intent = resp_json.get("intent_detected", "UNKNOWN")
                answer = resp_json.get("answer", "")
            except Exception:
                intent = "PARSE_ERROR"
                answer = resp_str
                
            session_log.append({
                "user_idx": user_idx,
                "session_id": session_id,
                "turn": turn_idx,
                "query": tagged_query,
                "intent": intent,
                "answer_snippet": answer[:80].replace("\n", " "),
                "elapsed": round(elapsed, 3),
                "success": True,
                "error": None
            })
        except Exception as e:
            elapsed = time.time() - t0
            session_log.append({
                "user_idx": user_idx,
                "session_id": session_id,
                "turn": turn_idx,
                "query": tagged_query,
                "intent": "EXCEPTION",
                "answer_snippet": "",
                "elapsed": round(elapsed, 3),
                "success": False,
                "error": str(e)
            })
            
    return session_id, session_log

def run_concurrency_stress_test(num_users=50, turns_per_user=10, max_workers=10):
    print("\n" + "=" * 70)
    print(f"INICIANDO TESTE DE CONCORRÊNCIA E ISOLAMENTO DE SESSÕES")
    print(f"Configuração: {num_users} Usuários Simultâneos x {turns_per_user} Perguntas = {num_users * turns_per_user} Interações")
    print(f"Threads em paralelo: {max_workers}")
    print("=" * 70 + "\n")
    
    start_total = time.time()
    all_results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(simulate_user_session, u_idx, turns_per_user): u_idx 
            for u_idx in range(1, num_users + 1)
        }
        
        completed = 0
        for f in as_completed(futures):
            u_idx = futures[f]
            try:
                sess_id, logs = f.result()
                all_results[sess_id] = logs
                completed += 1
                if completed % 5 == 0 or completed == num_users:
                    print(f"[{completed}/{num_users}] Sessões de usuários concluídas...")
            except Exception as e:
                print(f"[ERRO CRÍTICO] Falha no usuário {u_idx}: {e}")
                
    total_time = round(time.time() - start_total, 2)
    
    # ── Auditoria e Validação Rigorosa dos Resultados ─────────────────────────
    total_interactions = sum(len(logs) for logs in all_results.values())
    total_errors = sum(1 for logs in all_results.values() for item in logs if not item["success"])
    latencies = [item["elapsed"] for logs in all_results.values() for item in logs if item["success"]]
    latencies.sort()
    
    avg_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0
    p95_latency = round(latencies[int(len(latencies) * 0.95)], 3) if latencies else 0
    p50_latency = round(latencies[int(len(latencies) * 0.50)], 3) if latencies else 0
    
    # ── Auditoria no SQLite (Verificação de Integridade e Isolamento) ──────────
    print("\n" + "-" * 70)
    print("AUDITANDO BANCO SQLITE (data/db/telemetry.db) PARA ISOLAMENTO DE SESSÕES:")
    print("-" * 70)
    
    conn = sqlite3.connect(DATABASE_TELEMETRY)
    crosstalk_detected = False
    lost_versions = 0
    
    for sess_id, logs in all_results.items():
        row = conn.execute(
            "SELECT version, history_json FROM agent_session_storage WHERE session_id = ?",
            (sess_id,)
        ).fetchone()
        
        if not row:
            print(f"❌ [ERRO] Sessão {sess_id} não foi encontrada no banco!")
            crosstalk_detected = True
            continue
            
        version, hist_json = row
        hist = json.loads(hist_json) if hist_json else []
        
        # Verifica se o histórico contém mensagens de outros usuários
        expected_u_tag = f"tag_u{logs[0]['user_idx']}_"
        for msg in hist:
            if "tag_u" in msg and expected_u_tag not in msg:
                print(f"❌ [CONTAMINAÇÃO DETECTADA] Mensagem de outro usuário vazou na sessão {sess_id}: {msg}")
                crosstalk_detected = True
                
    conn.close()
    
    # ── Sumário Executivo ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RELATÓRIO DE HOMOLOGAÇÃO DE CONCORRÊNCIA E ISOLAMENTO:")
    print("=" * 70)
    print(f"• Total de Sessões Executadas  : {len(all_results)} / {num_users}")
    print(f"• Total de Interações Realizadas: {total_interactions}")
    print(f"• Falhas / Erros de Concorrência : {total_errors} ({round(total_errors / max(1, total_interactions) * 100, 2)}%)")
    print(f"• Taxa de Sucesso Geral          : {round((total_interactions - total_errors) / max(1, total_interactions) * 100, 2)}%")
    print(f"• Contaminação Cruzada (Leakage) : {'❌ DETECTADA' if crosstalk_detected else '✅ ZERO (Isolamento 100% Confirmado)'}")
    print(f"• Tempo Total de Execução        : {total_time}s")
    print(f"• Latência Média por Mensagem    : {avg_latency}s")
    print(f"• Latência Mediana (P50)         : {p50_latency}s")
    print(f"• Latência Percentil 95 (P95)    : {p95_latency}s")
    print("=" * 70 + "\n")
    
    return {
        "total_users": len(all_results),
        "total_interactions": total_interactions,
        "total_errors": total_errors,
        "success_rate": round((total_interactions - total_errors) / max(1, total_interactions) * 100, 2),
        "crosstalk_detected": crosstalk_detected,
        "avg_latency": avg_latency,
        "p50_latency": p50_latency,
        "p95_latency": p95_latency,
        "total_time": total_time
    }

if __name__ == "__main__":
    users = 50
    turns = 10
    workers = 10
    
    if len(sys.argv) > 1:
        users = int(sys.argv[1])
    if len(sys.argv) > 2:
        turns = int(sys.argv[2])
    if len(sys.argv) > 3:
        workers = int(sys.argv[3])
        
    run_concurrency_stress_test(users, turns, workers)

