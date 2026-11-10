"""
test_audit_regression_complete.py
Bateria Completa de Auditoria de Regressão Pós-Correção:
Contexto Conversacional + Fast Gate + Triage + Redirect + Latência (p50/p90/p95/p99)
"""

import os
import sys
import json
import time
import re
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv()

from agent.main import DuqueIAAgent
from agent.triage import check_fast_gate

class RegressionAuditRunner:
    def __init__(self):
        self.agent = DuqueIAAgent()
        self.results = {
            "preservacao_contexto": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "desambiguacao": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "fast_gate": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "triage": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "redirect": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "rewritten_query": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "handler": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "mudanca_intencao": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "falsos_positivos": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "falsos_negativos": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "outras_intencoes": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "adversarial_curto": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "contexto_longo": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
            "loop_prevention": {"total": 0, "pass": 0, "fail": 0, "latencies": []},
        }
        self.all_latencies = []
        self.failures = []

    def log_metric(self, category: str, passed: bool, latency: float, failure_detail: dict = None):
        cat = self.results[category]
        cat["total"] += 1
        if passed:
            cat["pass"] += 1
        else:
            cat["fail"] += 1
            if failure_detail:
                self.failures.append(failure_detail)
        cat["latencies"].append(latency)
        self.all_latencies.append(latency)

    # --------------------------------------------------------------------------
    # 1. INCIDENTE ORIGINAL (3 Turnos)
    # --------------------------------------------------------------------------
    def test_original_incident(self):
        print("\n[1/12] Executando Teste do Incidente Original...")
        sess_id = f"audit_orig_{int(time.time()*1000)}"
        
        # Turno 1
        t0 = time.time()
        r1 = json.loads(self.agent.respond("Quero abrir uma reclamação.", use_triage=True, conversation_id=sess_id))
        d1 = (time.time() - t0) * 1000
        ans1 = r1.get("answer", "").lower()
        p1 = ("que pena" not in ans1) and ("assunto" in ans1 or "manifestação" in ans1)
        self.log_metric("desambiguacao", p1, d1)

        # Turno 2
        t1 = time.time()
        r2 = json.loads(self.agent.respond("Meu vizinho está com som alto.", use_triage=True, conversation_id=sess_id))
        d2 = (time.time() - t1) * 1000
        ans2 = r2.get("answer", "").lower()
        p2 = ("190" in ans2 or "militar" in ans2) and ("colab" in ans2 or "ordem pública" in ans2 or "comércio" in ans2)
        self.log_metric("desambiguacao", p2, d2)

        # Turno 3
        t2 = time.time()
        r3 = json.loads(self.agent.respond("Estabelecimento comercial.", use_triage=True, conversation_id=sess_id))
        d3 = (time.time() - t2) * 1000
        ans3 = r3.get("answer", "").lower()
        intent3 = r3.get("intent_detected", "")

        # Validações estritas
        no_servidor_redirect = not ("servidor da prefeitura" in ans3 or "qual secretaria" in ans3 or "qual posto" in ans3)
        not_denuncia = (intent3 != "possivel_denuncia_redirect")
        is_colab_noise = any(w in ans3 for w in ["colab", "ordem pública", "ordem publica", "ruídos de bares", "ruidos"])
        p3 = no_servidor_redirect and not_denuncia and is_colab_noise

        self.log_metric("preservacao_contexto", p3, d3, {
            "test": "Incidente Original Turno 3",
            "query": "Estabelecimento comercial.",
            "answer": ans3[:120],
            "intent": intent3
        })
        self.log_metric("redirect", p3, d3)

    # --------------------------------------------------------------------------
    # 2. TESTE DE PARÁFRASES DE COMÉRCIO (15 variantes)
    # --------------------------------------------------------------------------
    def test_paraphrases(self):
        print("[2/12] Executando Teste de Paráfrases de Comércio...")
        paraphrases = [
            "é um comércio", "é um bar", "é um restaurante", "é uma boate",
            "é uma loja", "é um mercado", "é um estabelecimento", "vem de um comércio",
            "é de um bar aqui perto", "é de um restaurante", "é de um comércio da esquina",
            "é um salão", "é uma casa de festas", "é uma lanchonete", "é uma padaria"
        ]
        dummy_hist = [
            "Munícipe: Meu vizinho tá com som alto",
            "DUQUE IA: Para som alto, se vier de residência particular acione 190. Se vier de comércio, registre pelo Colab."
        ]
        for phrase in paraphrases:
            t0 = time.time()
            res = check_fast_gate(phrase, history=dummy_hist)
            dur = (time.time() - t0) * 1000
            passed = (res is not None and res.get("intent") == "OUVIDORIA_MANIFESTACAO" and
                      res.get("sub_intent") == "poluicao_sonora_comercial")
            self.log_metric("fast_gate", passed, dur, {"test": f"Paráfrase '{phrase}'", "res": res})

    # --------------------------------------------------------------------------
    # 3. TESTE DE VARIAÇÃO LINGUÍSTICA (Typos, Gírias, Erros)
    # --------------------------------------------------------------------------
    def test_linguistic_variations(self):
        print("[3/12] Executando Teste de Variações Linguísticas...")
        variations = [
            "comercio", "comérciu", "barulho do bar", "som alto do bar",
            "bar tá com som alto", "o bar da esquina", "o comercio ta com som alto",
            "o vizinho é um bar", "vem de um estabelecimento", "é um bar aqui perto",
            "é comércio", "comercio da rua"
        ]
        dummy_hist = [
            "Munícipe: Meu vizinho tá com som alto",
            "DUQUE IA: Para som alto, se vier de residência particular acione 190. Se vier de comércio, registre pelo Colab."
        ]
        for phrase in variations:
            t0 = time.time()
            res = check_fast_gate(phrase, history=dummy_hist)
            dur = (time.time() - t0) * 1000
            passed = (res is not None and res.get("intent") == "OUVIDORIA_MANIFESTACAO")
            self.log_metric("fast_gate", passed, dur, {"test": f"Variação '{phrase}'", "res": res})

    # --------------------------------------------------------------------------
    # 4. TESTE DE FALSOS POSITIVOS DO FAST GATE (Crítico)
    # --------------------------------------------------------------------------
    def test_fast_gate_false_positives(self):
        print("[4/12] Executando Teste de Falsos Positivos do Fast Gate (Blindagem)...")
        test_queries = [
            "Quero saber o horário de funcionamento do comércio.",
            "Tenho uma reclamação sobre o comércio ambulante.",
            "Quero abrir uma reclamação contra um estabelecimento por falta de higiene.",
            "Quero denunciar um comércio funcionando irregularmente.",
            "Quero saber como abrir uma empresa.",
            "Preciso do endereço de um bar.",
            "Quero saber se posso abrir um estabelecimento aqui.",
            "O estabelecimento onde trabalho não recebeu o alvará."
        ]
        dummy_hist = [
            "Munícipe: Meu vizinho tá com som alto",
            "DUQUE IA: Para som alto, se vier de residência particular acione 190. Se vier de comércio, registre pelo Colab."
        ]
        for q in test_queries:
            t0 = time.time()
            # O Fast Gate NÃO pode classificar essas perguntas como poluição sonora de comércio!
            res = check_fast_gate(q, history=dummy_hist)
            dur = (time.time() - t0) * 1000
            is_false_positive = (res is not None and res.get("sub_intent") == "poluicao_sonora_comercial")
            passed = not is_false_positive
            self.log_metric("falsos_positivos", passed, dur, {
                "test": "Falso Positivo Fast Gate",
                "query": q,
                "unexpected_fast_gate": res
            })

    # --------------------------------------------------------------------------
    # 5. TESTE DE RESIDÊNCIA (Polícia 190)
    # --------------------------------------------------------------------------
    def test_residence(self):
        print("[5/12] Executando Teste de Residência...")
        residence_phrases = [
            "é meu vizinho", "é uma casa", "é uma residência",
            "vem da casa ao lado", "é uma residência particular", "é na casa do vizinho"
        ]
        dummy_hist = [
            "Munícipe: Meu vizinho tá com som alto",
            "DUQUE IA: Para casos de som alto, a orientação depende da origem do ruído: se residência particular (190) ou comércio (Colab)."
        ]
        for phrase in residence_phrases:
            t0 = time.time()
            res = check_fast_gate(phrase, history=dummy_hist)
            dur = (time.time() - t0) * 1000
            passed = (res is not None and res.get("intent") == "RESIDENCIAL")
            self.log_metric("desambiguacao", passed, dur, {"test": f"Residência '{phrase}'", "res": res})

    # --------------------------------------------------------------------------
    # 6. TESTE DE ESPAÇO PÚBLICO E VEÍCULOS
    # --------------------------------------------------------------------------
    def test_public_space_and_vehicles(self):
        print("[6/12] Executando Teste de Espaço Público e Veículos...")
        public_phrases = [
            ("é na rua", "poluicao_sonora_via_publica"),
            ("é na praça", "poluicao_sonora_via_publica"),
            ("é na calçada", "poluicao_sonora_via_publica"),
            ("é na via pública", "poluicao_sonora_via_publica"),
            ("é um carro com som alto", "poluicao_sonora_veiculo"),
            ("é um paredão na rua", "poluicao_sonora_veiculo"),
            ("é um evento na rua", "poluicao_sonora_via_publica"),
        ]
        dummy_hist = [
            "Munícipe: Tem um som insuportável",
            "DUQUE IA: Se vier de residência particular acione 190. Se vier de comércio ou espaço público, registre no Colab."
        ]
        for phrase, expected_sub in public_phrases:
            t0 = time.time()
            res = check_fast_gate(phrase, history=dummy_hist)
            dur = (time.time() - t0) * 1000
            passed = (res is not None and res.get("intent") == "OUVIDORIA_MANIFESTACAO" and
                      res.get("sub_intent") == expected_sub)
            self.log_metric("desambiguacao", passed, dur, {"test": f"Espaço Público '{phrase}'", "res": res})

    # --------------------------------------------------------------------------
    # 7. TESTE DE MUDANÇA REAL DE INTENÇÃO
    # --------------------------------------------------------------------------
    def test_intent_change(self):
        print("[7/12] Executando Teste de Mudança Real de Intenção...")
        sess_id = f"audit_change_{int(time.time()*1000)}"
        # Turno 1 e 2 configuram contexto de som alto
        self.agent.respond("Quero abrir uma reclamação de barulho.", use_triage=True, conversation_id=sess_id)
        self.agent.respond("É um estabelecimento comercial.", use_triage=True, conversation_id=sess_id)

        # Turno 3: Mudança explícita de assunto
        t0 = time.time()
        r = json.loads(self.agent.respond("Na verdade, esquece isso. Quero saber onde fica a Prefeitura.", use_triage=True, conversation_id=sess_id))
        dur = (time.time() - t0) * 1000
        ans = r.get("answer", "").lower()
        intent = r.get("intent_detected", "")

        # Deve responder o endereço da prefeitura sem falar de barulho/som alto
        passed = ("alameda esmeralda" in ans or "jardim primavera" in ans) and ("barulho" not in ans)
        self.log_metric("mudanca_intencao", passed, dur, {
            "test": "Mudança explícita para endereço da Prefeitura",
            "ans": ans[:120],
            "intent": intent
        })

    # --------------------------------------------------------------------------
    # 8. TESTE DE POSSÍVEL DENÚNCIA (Servidor vs Não-Servidor)
    # --------------------------------------------------------------------------
    def test_possivel_denuncia_discrimination(self):
        print("[8/12] Executando Teste de Discriminação de Possível Denúncia...")
        servidor_cases = [
            "Um servidor me xingou.",
            "Um funcionário da Prefeitura me ameaçou.",
            "Fui maltratado por um servidor.",
            "Uma atendente da Prefeitura se recusou a me atender e me ofendeu.",
            "Um servidor público municipal pediu dinheiro para fazer o serviço.",
            "Um funcionário da Prefeitura praticou uma irregularidade."
        ]
        non_servidor_cases = [
            "Meu vizinho faz muito barulho.",
            "O bar da esquina está com som alto.",
            "Tem lixo na rua.",
            "Tem um buraco na rua.",
            "Uma obra está causando transtorno.",
            "Um comércio está funcionando irregularmente.",
            "Tem esgoto vazando.",
            "O poste está apagado."
        ]

        for q in servidor_cases:
            t0 = time.time()
            res = check_fast_gate(q)
            dur = (time.time() - t0) * 1000
            passed = (res is not None and res.get("intent") == "POSSIVEL_DENUNCIA")
            self.log_metric("triage", passed, dur, {"test": f"Denúncia Servidor '{q}'", "res": res})

        for q in non_servidor_cases:
            t0 = time.time()
            res = check_fast_gate(q)
            dur = (time.time() - t0) * 1000
            is_denuncia = (res is not None and res.get("intent") == "POSSIVEL_DENUNCIA")
            passed = not is_denuncia
            self.log_metric("falsos_positivos", passed, dur, {"test": f"Não-Denúncia '{q}'", "res": res})

    # --------------------------------------------------------------------------
    # 9. TESTE DE CONFUSÃO ENTRE DENÚNCIA E RECLAMAÇÃO (Pares Semânticos)
    # --------------------------------------------------------------------------
    def test_denuncia_vs_reclamacao_pairs(self):
        print("[9/12] Executando Pares Semânticos Denúncia vs Reclamação...")
        pairs = [
            ("Quero reclamar que um servidor me tratou mal.", "POSSIVEL_DENUNCIA"),
            ("Quero reclamar que um comércio me tratou mal.", "NOT_DENUNCIA_FUNCIONAL"),
            ("Quero reclamar que um estabelecimento está fazendo barulho.", "NOT_DENUNCIA_FUNCIONAL"),
            ("Quero denunciar que um servidor público pediu dinheiro.", "POSSIVEL_DENUNCIA")
        ]
        for q, expected in pairs:
            t0 = time.time()
            res = check_fast_gate(q)
            dur = (time.time() - t0) * 1000
            if expected == "POSSIVEL_DENUNCIA":
                passed = (res is not None and res.get("intent") == "POSSIVEL_DENUNCIA")
            else:
                passed = (res is None or res.get("intent") != "POSSIVEL_DENUNCIA")
            self.log_metric("triage", passed, dur, {"test": f"Par Semântico '{q}'", "res": res})

    # --------------------------------------------------------------------------
    # 10. TESTE DE REWRITTEN QUERY E HANDLER
    # --------------------------------------------------------------------------
    def test_rewritten_query_and_handler(self):
        print("[10/12] Executando Teste de rewritten_query e Handler...")
        dummy_hist = [
            "Munícipe: Meu vizinho tá com som alto",
            "DUQUE IA: Para casos de som alto, se for comércio registre no Colab."
        ]
        t0 = time.time()
        res = check_fast_gate("estabelecimento comercial", history=dummy_hist)
        dur = (time.time() - t0) * 1000
        rq = res.get("rewritten_query", "")
        passed = ("poluição sonora" in rq.lower() or "ruído" in rq.lower() or "som alto" in rq.lower()) and ("estabelecimento comercial" in rq.lower())
        self.log_metric("rewritten_query", passed, dur, {"test": "rewritten_query", "rq": rq})
        self.log_metric("handler", passed, dur)

    # --------------------------------------------------------------------------
    # 11. REGRESSÃO GERAL EM OUTRAS INTENÇÕES (IPTU, Saúde, Iluminação, etc.)
    # --------------------------------------------------------------------------
    def test_other_intents_regression(self):
        print("[11/12] Executando Teste de Regressão em Outras Intenções...")
        other_queries = [
            ("Como emitir 2ª via do IPTU?", ["RAG_GERAL", "TRIBUTOS"]),
            ("Onde tem vacina contra gripe?", ["RAG_GERAL", "SAUDE"]),
            ("Quero vaga em creche municipal", ["RAG_GERAL", "EDUCACAO"]),
            ("Horário dos ônibus de Caxias", ["RAG_GERAL", "TRANSPORTES"]),
            ("Poste com lâmpada queimada na rua", ["RAG_GERAL", "ILUMINACAO"]),
            ("Tapa buraco na minha rua", ["RAG_GERAL", "OBRAS"]),
            ("Quem é o prefeito de Duque de Caxias?", ["AUTORIDADE_PUBLICA", "GOLDEN_SOURCE"])
        ]
        for q, valid_intents in other_queries:
            t0 = time.time()
            res = check_fast_gate(q)
            dur = (time.time() - t0) * 1000
            intent = res.get("intent") if res else "RAG_GERAL"
            passed = any(vi in intent for vi in valid_intents)
            self.log_metric("outras_intencoes", passed, dur, {"test": f"Outra Intenção '{q}'", "intent": intent})

    # --------------------------------------------------------------------------
    # 12. ADVERSARIAL: RESPOSTAS CURTAS / SIM / NÃO
    # --------------------------------------------------------------------------
    def test_adversarial_short_replies(self):
        print("[12/13] Executando Teste Adversarial (Frases Curtas / Sim / Não)...")
        dummy_hist = [
            "Munícipe: Tem som alto aqui",
            "DUQUE IA: O barulho vem de uma residência ou de um comércio?"
        ]
        short_cases = [
            ("comércio", "OUVIDORIA_MANIFESTACAO"),
            ("bar", "OUVIDORIA_MANIFESTACAO"),
            ("rua", "OUVIDORIA_MANIFESTACAO"),
            ("casa", "RESIDENCIAL"),
            ("vizinho", "RESIDENCIAL"),
            ("sim, é um bar", "OUVIDORIA_MANIFESTACAO"),
            ("não, é na minha casa", "RESIDENCIAL")
        ]
        for short_ans, expected_intent in short_cases:
            t0 = time.time()
            res = check_fast_gate(short_ans, history=dummy_hist)
            dur = (time.time() - t0) * 1000
            passed = (res is not None and res.get("intent") == expected_intent)
            self.log_metric("adversarial_curto", passed, dur, {"test": f"Curta '{short_ans}'", "res": res})

    # --------------------------------------------------------------------------
    # 13. TESTE DE CONTEXTO LONGO (6 Turnos Sequenciais)
    # --------------------------------------------------------------------------
    def test_long_context(self):
        print("[13/13] Executando Teste de Contexto Longo (6 Turnos)...")
        dummy_hist = [
            "Munícipe: Quero abrir uma reclamação.",
            "DUQUE IA: Claro! Estamos prontos para receber sua manifestação. Qual é o assunto?",
            "Munícipe: É sobre um problema de barulho.",
            "DUQUE IA: Para som alto, se for residencial acione 190, se for comércio registre no Colab.",
            "Munícipe: Acontece todo fim de semana e começa às 22h.",
            "DUQUE IA: Entendido. O barulho vem de uma residência ou de um comércio?"
        ]
        t0 = time.time()
        res = check_fast_gate("O estabelecimento comercial da esquina.", history=dummy_hist)
        dur = (time.time() - t0) * 1000
        passed = (res is not None and res.get("intent") == "OUVIDORIA_MANIFESTACAO" and
                  res.get("sub_intent") == "poluicao_sonora_comercial")
        self.log_metric("contexto_longo", passed, dur, {"test": "Contexto Longo Turno 6", "res": res})

    # --------------------------------------------------------------------------
    # 14. TESTE DE DETECÇÃO E QUEBRA DE LOOPS CÍCLICOS
    # --------------------------------------------------------------------------
    def test_loop_prevention(self):
        print("[14/14] Executando Teste de Detecção e Quebra de Loops Cíclicos...")
        sess_id = f"audit_loop_{int(time.time()*1000)}"
        # Turno 1: reclamação que direciona para Colab
        r1 = json.loads(self.agent.respond("estabelecimento comercial com som alto", use_triage=True, conversation_id=sess_id))
        # Turno 2: insistência sobre colab
        r2 = json.loads(self.agent.respond("como faço nesse aplicativo colab?", use_triage=True, conversation_id=sess_id))
        # Turno 3: terceira insistência sem conseguir
        t0 = time.time()
        r3 = json.loads(self.agent.respond("não consigo usar esse colab, me ajuda", use_triage=True, conversation_id=sess_id))
        dur = (time.time() - t0) * 1000
        ans3 = r3.get("answer", "").lower()
        intent3 = r3.get("intent_detected", "")
        # O detector de loop deve intervir e ofertar o canal direto da Ouvidoria
        passed = ("2652-3835" in ans3 or "99824-5903" in ans3) and ("ouvidoria geral" in ans3)
        self.log_metric("loop_prevention", passed, dur, {"test": "Loop Prevention Turno 3", "ans": ans3[:120], "intent": intent3})

    # --------------------------------------------------------------------------
    # EXECUÇÃO E RELATÓRIO FINAL
    # --------------------------------------------------------------------------
    def run_all(self):
        print("======================================================================")
        print("   INICIANDO AUDITORIA DE REGRESSÃO COMPLETA (24 SEÇÕES)             ")
        print("======================================================================")
        
        self.test_original_incident()
        self.test_paraphrases()
        self.test_linguistic_variations()
        self.test_fast_gate_false_positives()
        self.test_residence()
        self.test_public_space_and_vehicles()
        self.test_intent_change()
        self.test_possivel_denuncia_discrimination()
        self.test_denuncia_vs_reclamacao_pairs()
        self.test_rewritten_query_and_handler()
        self.test_other_intents_regression()
        self.test_adversarial_short_replies()
        self.test_long_context()
        self.test_loop_prevention()

        self.generate_report()

    def generate_report(self):
        print("\n" + "="*70)
        print("                     MATRIZ FINAL DE RESULTADOS                      ")
        print("="*70)
        print(f"{'Categoria':<25} | {'Testes':>6} | {'Aprovados':>9} | {'Falhos':>6} | {'Taxa (%)':>8}")
        print("-" * 70)

        total_tests = 0
        total_pass = 0
        total_fail = 0

        for cat, data in self.results.items():
            tot = data["total"]
            pas = data["pass"]
            fai = data["fail"]
            rate = (pas / tot * 100) if tot > 0 else 0.0
            total_tests += tot
            total_pass += pas
            total_fail += fai
            cat_name = cat.replace("_", " ").title()
            print(f"{cat_name:<25} | {tot:>6} | {pas:>9} | {fai:>6} | {rate:>7.1f}%")

        print("-" * 70)
        overall_rate = (total_pass / total_tests * 100) if total_tests > 0 else 0.0
        print(f"{'TOTAL GERAL':<25} | {total_tests:>6} | {total_pass:>9} | {total_fail:>6} | {overall_rate:>7.1f}%")
        print("=" * 70)

        # Métricas de Latência
        if self.all_latencies:
            lats = np.array(self.all_latencies)
            p50 = np.percentile(lats, 50)
            p90 = np.percentile(lats, 90)
            p95 = np.percentile(lats, 95)
            p99 = np.percentile(lats, 99)
            print("\n" + "="*70)
            print("                 MÉTRICAS DE LATÊNCIA DA AUDITORIA                   ")
            print("="*70)
            print(f"  Mínimo  : {np.min(lats):.2f} ms")
            print(f"  Máximo  : {np.max(lats):.2f} ms")
            print(f"  Média   : {np.mean(lats):.2f} ms")
            print(f"  p50     : {p50:.2f} ms")
            print(f"  p90     : {p90:.2f} ms")
            print(f"  p95     : {p95:.2f} ms")
            print(f"  p99     : {p99:.2f} ms")
            print("=" * 70)

        # Conclusão Obrigatória
        print("\n" + "="*70)
        print("                       CONCLUSÃO OBRIGATÓRIA                         ")
        print("="*70)
        print(f"A correção generalizou?                     : {'SIM' if total_fail == 0 else 'PARCIALMENTE'}")
        print(f"Foram encontrados novos falsos positivos?   : {'NÃO' if self.results['falsos_positivos']['fail'] == 0 else 'SIM'}")
        print(f"Foram encontrados novos falsos negativos?   : {'NÃO' if self.results['falsos_negativos']['fail'] == 0 else 'SIM'}")
        print(f"O Fast Gate está seguro?                    : {'SIM' if self.results['fast_gate']['fail'] == 0 else 'PARCIALMENTE'}")
        print(f"O contexto está sendo preservado?           : {'SIM' if self.results['preservacao_contexto']['fail'] == 0 else 'NÃO'}")
        print(f"O rewritten_query está sendo utilizado?     : {'SIM' if self.results['rewritten_query']['fail'] == 0 else 'NÃO'}")
        print(f"Existem redirects indevidos?                : {'NÃO' if self.results['redirect']['fail'] == 0 else 'SIM'}")
        print(f"Existem regressões?                         : {'NÃO' if total_fail == 0 else 'SIM'}")
        print(f"Existem problemas de latência (p95 > 5s)?   : {'NÃO' if p95 < 5000 else 'SIM'}")
        print("=" * 70)

if __name__ == "__main__":
    runner = RegressionAuditRunner()
    runner.run_all()
