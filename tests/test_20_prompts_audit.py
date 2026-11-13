import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.agent import DuqueIAAgent


QUESTIONS = [
    # 1. Vagas / Cursos (Regra 4)
    ("1_vagas_cursos", "Quais cursos gratuitos da FUNDEC e vagas de emprego no Sine Caxias existem?", ["fundec", "sine"], []),
    # 2. Poda em alta tensão (Regra 5)
    ("2_poda_alta_tensao", "Tem uma árvore encostada nos fios de alta tensão na minha rua, quem poda?", ["light", "colab"], []),
    # 3. Poda em quintal particular (Regra 13)
    ("3_poda_quintal", "Quero podar uma árvore dentro do meu quintal particular, quais documentos preciso levar?", ["meio ambiente", "rg", "cpf"], []),
    # 4. Terreno abandonado (Regra 6a)
    ("4_terreno_abandonado", "Tem um terreno abandonado cheio de mato e lixo aqui perto, quem fiscaliza?", ["smuh", "colab"], []),
    # 5. Barulho / Som alto (Regra 6b)
    ("5_barulho_comercio", "Um bar na esquina está com som alto de madrugada atrapalhando o sossego, o que fazer?", ["190", "suop"], []),
    # 6. Emergência / Trauma ortopédico (Regra 10)
    ("6_trauma_fratura", "Acho que quebrei o pé caindo na escada, para qual hospital público de Caxias devo ir?", ["adão pereira nunes", "moacyr"], ["chegaram os especialistas"]),
    # 7. Animal silvestre (Regra 11)
    ("7_animal_silvestre", "Apareceu um gambá no meu quintal, a proteção animal resgata?", ["guarda ambiental", "colab"], []),
    # 8. Falta de água / Concessionária (Regra 12)
    ("8_falta_agua", "Minha rua está sem água há dias e a Águas do Rio não resolve, a prefeitura faz o quê?", ["águas do rio", "agenersa"], []),
    # 9. Templo religioso (Regra 14)
    ("9_templo_religioso", "Igreja ou templo religioso precisa de alvará ou tem imunidade em Duque de Caxias?", ["imunidade", "alvará"], []),
    # 10. Recurso de multa JARI (Regra 15)
    ("10_recurso_multa", "Como faço para recorrer de uma multa de trânsito municipal em Duque de Caxias e qual o prazo?", ["jari", "30 dias"], []),
    # 11. e-SIC vs Ouvidoria (Regra 16)
    ("11_esic_vs_ouvidoria", "Posso pedir cópia de contrato de limpeza urbana e denunciar nepotismo no mesmo protocolo?", ["e-sic", "ouvidoria"], []),
    # 12. Emagrecimento / Nutrição (Regra 17)
    ("12_emagrecimento", "Onde consigo acompanhamento com nutricionista para emagrecer pelo SUS em Caxias?", ["ubs", "nutrição"], ["fundec", "pgm"]),
    # 13. Lâmpada apagada / Zeladoria (Regra 18)
    ("13_lampada_apagada", "A lâmpada do poste na minha rua queimou, falo direto com a Ouvidoria ou tem outro canal?", ["colab"], []),
    # 14. Demora no SISREG (Regra 19)
    ("14_sisreg_demora", "Estou esperando há meses uma consulta com especialista no SISREG pela UBS, como acompanhar?", ["sisreg", "ubs"], []),
    # 15. Denúncia de servidor fantasma (Regra 20)
    ("15_servidor_fantasma", "Como denunciar um funcionário público fantasma que não aparece no plantão?", ["ouvidoria", "colab"], []),
    # 16. Chuva / Enchente / CRAS (Regra 21)
    ("16_chuva_enchente", "Minha casa alagou na chuva e perdi móveis, onde peço aluguel social e cesta básica?", ["cras", "defesa civil"], []),
    # 17. Obras vs Urbanismo (Regra 24)
    ("17_obras_vs_urbanismo", "Qual a diferença entre o que faz a Secretaria de Obras e a de Urbanismo?", ["smoa", "smuh"], []),
    # 18. Falta de medicamento idoso (Regra 25)
    ("18_falta_remedio_idoso", "Meu avô acamado não consegue ir buscar remédio contínuo que está em falta no posto, como proceder?", ["usf", "colab"], []),
    # 19. Alvará de vizinho / Sigilo fiscal (Regra 28)
    ("19_alvara_vizinho", "Quero ir na Fazenda consultar se o alvará do comércio do meu vizinho está regular, posso?", ["sigilo", "colab"], ["99824"]),
    # 20. Coleta incremental Ouvidoria (1 pergunta por vez)
    ("20_ouvidoria_ambigua", "Quero fazer uma reclamação", [], ["99824"]),
]


def main():
    agent = DuqueIAAgent()
    results = []
    passed = 0
    failed = 0

    for idx, (tag, query, must_any, must_not) in enumerate(QUESTIONS, 1):
        cid = f"audit20_{tag}_{int(time.time())}"
        t0 = time.time()
        res = agent.process_query(query, conversation_id=cid)
        dt = round((time.time() - t0) * 1000, 1)
        ans = (res.get("answer") or "").strip()
        ans_low = ans.lower()

        issues = []
        if not ans or len(ans) < 20:
            issues.append("RESPOSTA_CURTA_OU_VAZIA")
        if "99824" in ans_low:
            issues.append("VAZAMENTO_WHATSAPP_OUVIDORIA")
        if any(ans_low.startswith(g) for g in ("olá!", "oi!", "bom dia!", "boa tarde!", "boa noite!")):
            issues.append("SAUDACAO_REDUNDANTE_INICIAL")
        if ans.count("**") % 2 != 0:
            issues.append("POSSIVEL_TRUNCAMENTO_MARKDOWN")
        if must_any and not any(k in ans_low for k in must_any):
            issues.append(f"FALTOU_TERMO_ESPERADO({must_any})")
        for bad in must_not:
            if bad in ans_low:
                issues.append(f"TERMO_PROIBIDO({bad})")

        # Extra check for Q20: should ask only 1 question (<= 2 question marks ideally 1)
        if tag == "20_ouvidoria_ambigua" and ans.count("?") > 1:
            issues.append(f"MULTIPLAS_PERGUNTAS({ans.count('?')})")

        status = "PASS" if not issues else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"[{idx:02d}/20] {tag} | {status} | {dt}ms | intent={res.get('intent_detected')} | issues={issues}")
        print(f"   Q: {query}")
        print(f"   A: {ans[:260].replace(chr(10), ' ')}...")
        results.append({
            "tag": tag,
            "query": query,
            "status": status,
            "issues": issues,
            "intent": res.get("intent_detected"),
            "latency_ms": dt,
            "answer": ans,
        })

    print(f"\nRESUMO: {passed}/20 PASS | {failed}/20 FAIL")
    with open("scratch/test_20_prompts_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

