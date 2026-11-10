# -*- coding: utf-8 -*-
"""
Script de Execução em Lote de Todas as Perguntas do DUQUE IA
Executa as 102 perguntas consolidadas utilizando o pipeline oficial RAG
e a nova chave Gemini ativa (index=0) com gemini-3.8-flash.

Gera:
1. data/resultados_todas_as_perguntas.json (base de dados estruturada com todas as respostas)
2. docs/DOSSIE_COMPLETO_TODAS_AS_PERGUNTAS_E_RESPOSTAS.md (documento markdown completo)
3. docs/relatorio_todas_as_perguntas_a4.html (relatório HTML A4 diagramado)
4. docs/DUQUE_IA_DOSSIE_COMPLETO_PERGUNTAS_E_RESPOSTAS.pdf (dossiê executivo em PDF)
"""

import os
import sys
import json
import time
import shutil
import subprocess

# Configurar stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.agent import DuqueIAAgent

INPUT_JSON = os.path.join(BASE_DIR, "data", "todas_as_perguntas_consolidadas.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "data", "resultados_todas_as_perguntas.json")
OUTPUT_MD = os.path.join(BASE_DIR, "docs", "DOSSIE_COMPLETO_TODAS_AS_PERGUNTAS_E_RESPOSTAS.md")
OUTPUT_HTML = os.path.join(BASE_DIR, "docs", "relatorio_todas_as_perguntas_a4.html")
OUTPUT_PDF = os.path.join(BASE_DIR, "docs", "DUQUE_IA_DOSSIE_COMPLETO_PERGUNTAS_E_RESPOSTAS.pdf")
ROOT_PDF = os.path.join(BASE_DIR, "DUQUE_IA_DOSSIE_COMPLETO_PERGUNTAS_E_RESPOSTAS.pdf")


def load_previous_results():
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {item["id"]: item for item in data}
        except Exception:
            return {}
    return {}


def save_results(results_map, total_count):
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    results_list = list(results_map.values())
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results_list, f, ensure_ascii=False, indent=2)


def run_all_queries():
    print("=" * 70)
    print("DUQUE IA - EXECUÇÃO COMPLETA DAS 102 PERGUNTAS COM GEMINI-3.8-FLASH")
    print("=" * 70)

    if not os.path.exists(INPUT_JSON):
        print(f"ERRO: Arquivo de perguntas não encontrado: {INPUT_JSON}")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total = len(questions)
    print(f"Total de perguntas carregadas: {total}")

    results_map = load_previous_results()
    print(f"Respostas já em cache/executadas anteriormente: {len(results_map)}")

    agent = DuqueIAAgent()
    print(f"Agente inicializado com modelo: {agent.gemini_client.generation_model_name}")
    print(f"Chave ativa atual: index={agent.gemini_client.current_key_index}")

    for idx, item in enumerate(questions, 1):
        q_id = item["id"]

        # Se já temos resposta válida, reaproveita
        if q_id in results_map and results_map[q_id].get("answer") and not results_map[q_id].get("error"):
            print(f"[{idx:03d}/{total:03d}] {q_id} | JÁ PROCESSADO | Titulo: {item['titulo'][:40]}")
            continue

        query = item["query"]
        print(f"\n[{idx:03d}/{total:03d}] {q_id} | Processando: '{query[:60]}...'")
        t0 = time.time()

        try:
            raw_response = agent.respond(query)
            elapsed_sec = time.time() - t0

            try:
                res_dict = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
            except Exception:
                res_dict = {"answer": str(raw_response), "confidence": 0.5, "intent_detected": "unknown"}

            answer = res_dict.get("answer", "")
            confidence = res_dict.get("confidence", 0.0)
            intent = res_dict.get("intent_detected", "unknown")
            sources = res_dict.get("sources", [])
            metrics = res_dict.get("metrics", {})

            result_entry = {
                "id": q_id,
                "origem": item.get("origem", "Geral"),
                "subgrupo": item.get("subgrupo", "Geral"),
                "titulo": item.get("titulo", ""),
                "query": query,
                "criterio": item.get("criterio", ""),
                "answer": answer,
                "confidence": confidence,
                "intent_detected": intent,
                "sources_count": len(sources),
                "sources": sources[:3],
                "elapsed_seconds": round(elapsed_sec, 2),
                "total_time_ms": metrics.get("total_time_ms", round(elapsed_sec * 1000, 2)),
                "gemini_model": agent.gemini_client.generation_model_name,
                "status": "OK"
            }

            results_map[q_id] = result_entry
            save_results(results_map, total)

            preview = answer.replace("\n", " ")[:90]
            print(f"    --> Tempo: {elapsed_sec:.2f}s | Conf: {confidence} | Intent: {intent}")
            print(f"    --> Resposta: {preview}...")

        except Exception as e:
            elapsed_sec = time.time() - t0
            print(f"    --> ERRO na pergunta {q_id}: {e}")
            result_entry = {
                "id": q_id,
                "origem": item.get("origem", "Geral"),
                "subgrupo": item.get("subgrupo", "Geral"),
                "titulo": item.get("titulo", ""),
                "query": query,
                "criterio": item.get("criterio", ""),
                "answer": f"Erro durante execução: {str(e)}",
                "confidence": 0.0,
                "intent_detected": "error",
                "sources_count": 0,
                "sources": [],
                "elapsed_seconds": round(elapsed_sec, 2),
                "total_time_ms": round(elapsed_sec * 1000, 2),
                "gemini_model": agent.gemini_client.generation_model_name,
                "status": "ERROR",
                "error": str(e)
            }
            results_map[q_id] = result_entry
            save_results(results_map, total)

        # Pequeno intervalo para respeitar taxa da API se necessário
        time.sleep(0.4)

    print("\n" + "=" * 70)
    print(f"EXECUÇÃO FINALIZADA! {len(results_map)}/{total} perguntas processadas.")
    print("=" * 70)


if __name__ == "__main__":
    run_all_queries()

