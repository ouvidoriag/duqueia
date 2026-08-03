import os
import sys
import json
import time

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scripts.audit_pipeline import RAGPipelineAuditor

PERGUNTAS_FALHAS = [
    {"id": "P03", "pergunta": "Como registrar uma reclamação de buraco na rua?"},
    {"id": "P11", "pergunta": "Quais são os bairros do segundo distrito de Duque de Caxias?"},
    {"id": "P14", "pergunta": "O poste da minha rua está apagado há uma semana. O que eu faço?"},
    {"id": "P15", "pergunta": "Quero registrar uma denúncia sobre irregularidade em obra pública."},
    {"id": "P18", "pergunta": "Como consigo uma vaga na escola municipal para o próximo ano?"},
    {"id": "P28", "pergunta": "Qual é a capital da França?"}
]

def main():
    auditor = RAGPipelineAuditor()
    print("=" * 70)
    print("   AUDITANDO AS 6 PERGUNTAS QUE APRESENTAVAM FALHAS/LACUNAS")
    print("=" * 70)
    
    sucessos = 0
    
    for item in PERGUNTAS_FALHAS:
        pid = item["id"]
        q = item["pergunta"]
        print(f"\n[{pid}] Pergunta: '{q}'")
        res = auditor.audit_question(q)
        diag = res["root_cause_diagnosis"]
        code = diag["code"]
        
        if code in ["NO_FAILURE_DETECTED", "SECURITY_PRIVACY_BLOCKED"]:
            sucessos += 1
            print(f"   Status: ✔ APROVADO ({code})")
        else:
            print(f"   Status: ✘ FALHA ({code}) - Detalhes: {diag['details']}")
            
        ans_text = res.get("answer", res.get("generated_answer", ""))
        print(f"   Resposta: {str(ans_text)[:150]}...")
        
    print("\n" + "=" * 70)
    print(f"  RESULTADO DAS 6 LACUNAS: {sucessos}/6 APROVADAS ({(sucessos/6)*100:.1f}%)")
    print("=" * 70)

if __name__ == "__main__":
    main()
