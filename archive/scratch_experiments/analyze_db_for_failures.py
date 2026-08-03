"""
analyze_db_for_failures.py — DUQUE IA
======================================
Inspeção profunda no banco de dados (main.db e vector.db) para identificar
se as 9 perguntas que falharam possuem a informação correta na base ou se
trata-se de uma lacuna de conhecimento (Data Gap).
"""

import os
import sys
import json
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

from config.settings import DATABASE_MAIN, DATABASE_VECTOR

FAILED_QUESTIONS = [
    {
        "id": "P01",
        "pergunta": "Como solicitar a poda de árvore na calçada da minha rua?",
        "erro": "FALSE_NEGATIVE_GUARDRAIL",
        "keywords": ["poda", "árvore", "arvore", "calçada", "zeladoria", "colab", "meio ambiente"]
    },
    {
        "id": "P04",
        "pergunta": "Quais documentos preciso para matricular meu filho na creche municipal?",
        "erro": "LLM_HALLUCINATION",
        "keywords": ["documento", "documentos", "certidão", "matricula", "matrícula", "creche", "escola"]
    },
    {
        "id": "P05",
        "pergunta": "Como emitir o carnê do IPTU em Duque de Caxias?",
        "erro": "LLM_HALLUCINATION",
        "keywords": ["iptu", "carnê", "carne", "guia", "2 via", "fazenda"]
    },
    {
        "id": "P07",
        "pergunta": "Como solicitar limpeza de lote baldio ou terreno abandonado?",
        "erro": "LLM_HALLUCINATION",
        "keywords": ["lote", "baldio", "terreno", "abandonado", "limpeza", "entulho", "mato"]
    },
    {
        "id": "P11",
        "pergunta": "Quais são os bairros do segundo distrito de Duque de Caxias?",
        "erro": "LLM_HALLUCINATION",
        "keywords": ["segundo distrito", "2º distrito", "2 distrito", "distrito", "bairro", "primavera"]
    },
    {
        "id": "P12",
        "pergunta": "Qual a população estimada do município de Duque de Caxias?",
        "erro": "LLM_HALLUCINATION",
        "keywords": ["população", "populacao", "habitantes", "censo", "ibge", "estimada"]
    },
    {
        "id": "P15",
        "pergunta": "Quero registrar uma denúncia sobre irregularidade em obra pública.",
        "erro": "TRIAGE_BYPASS",
        "keywords": ["denúncia", "denuncia", "obra", "irregularidade", "ouvidoria", "colab"]
    },
    {
        "id": "P20",
        "pergunta": "A FUNDEC oferece cursos gratuitos? Quais?",
        "erro": "LLM_HALLUCINATION",
        "keywords": ["fundec", "curso", "cursos", "gratuito", "gratuitos", "inscrição"]
    },
    {
        "id": "P28",
        "pergunta": "Qual é a capital da França?",
        "erro": "TRIAGE_BYPASS",
        "keywords": ["frança", "franca", "capital", "paris"]
    }
]

def search_main_db(keywords):
    if not os.path.exists(DATABASE_MAIN):
        return []
    conn = sqlite3.connect(DATABASE_MAIN)
    cur = conn.cursor()
    matches = []
    
    # 1. Busca em vw_ia_servicos / services
    try:
        cur.execute("SELECT name, description, category_name, secretary_name FROM vw_ia_servicos")
        for row in cur.fetchall():
            name, desc, cat, sec = row
            full_txt = f"{name} {desc} {cat} {sec}".lower()
            if any(kw.lower() in full_txt for kw in keywords):
                matches.append(f"[vw_ia_servicos] {name} | Órgão: {sec} | Resumo: {desc[:150]}...")
    except Exception as e:
        pass
        
    # 2. Busca em secretarias
    try:
        cur.execute("SELECT name, description, address, phone FROM secretarias")
        for row in cur.fetchall():
            name, desc, addr, phone = row
            full_txt = f"{name} {desc}".lower()
            if any(kw.lower() in full_txt for kw in keywords):
                matches.append(f"[secretarias] {name} | Contatos: {phone} | Endereço: {addr}")
    except Exception as e:
        pass

    conn.close()
    return matches

def search_vector_db(keywords):
    if not os.path.exists(DATABASE_VECTOR):
        return []
    conn = sqlite3.connect(DATABASE_VECTOR)
    cur = conn.cursor()
    matches = []
    
    try:
        cur.execute("SELECT source, title, content FROM duque_ia_chunks")
        for row in cur.fetchall():
            src, title, content = row
            full_txt = f"{src} {title} {content}".lower()
            matching_kws = [kw for kw in keywords if kw.lower() in full_txt]
            if matching_kws:
                matches.append({
                    "source": src,
                    "title": title,
                    "matched_keywords": matching_kws,
                    "preview": content[:200].replace("\n", " ")
                })
    except Exception as e:
        pass
        
    conn.close()
    return matches

def run_analysis():
    report_data = []
    
    print("=" * 70)
    print("     INSPEÇÃO PROFUNDA DE LACUNAS DE DADOS NO MAIN.DB E VECTOR.DB")
    print("=" * 70)
    
    for q_item in FAILED_QUESTIONS:
        pid = q_item["id"]
        q = q_item["pergunta"]
        err = q_item["erro"]
        kws = q_item["keywords"]
        
        main_matches = search_main_db(kws)
        vector_matches = search_vector_db(kws)
        
        has_precise_data = len(main_matches) > 0 or len(vector_matches) > 0
        
        item_analysis = {
            "id": pid,
            "pergunta": q,
            "erro": err,
            "tem_resposta_no_banco": has_precise_data,
            "main_db_matches": main_matches[:3],
            "vector_db_matches": vector_matches[:3]
        }
        report_data.append(item_analysis)
        
        status_txt = "✔ TEM RESPOSTA NO BANCO" if has_precise_data else "✘ LACUNA DE DADOS (DATA GAP)"
        print(f"\n[{pid}] '{q}'")
        print(f"    Erro Auditado : {err}")
        print(f"    Status Base   : {status_txt}")
        print(f"    Encontrados em main.db   : {len(main_matches)}")
        print(f"    Encontrados em vector.db : {len(vector_matches)}")
        
    output_path = os.path.join(_PROJECT_ROOT, "metrics", "data_gap_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n[OK] Análise salva em: {output_path}")

if __name__ == "__main__":
    run_analysis()
