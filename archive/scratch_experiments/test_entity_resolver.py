import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

from agent.entity_resolver import GoldenSourceResolver

resolver = GoldenSourceResolver()

test_queries = [
    "Qual endereço do CRAS Jardim Primavera?",
    "Onde fica a Secretaria Municipal de Saúde de Duque de Caxias?",
    "Qual o telefone do CRAS Imbariê?",
    "Onde fica a Secretaria de Fazenda?",
    "Como emitir o carnê do IPTU?"
]

print("=" * 70)
print("       TESTE DO ENTITY RESOLVER + GOLDEN SOURCE LAYER")
print("=" * 70)

for q in test_queries:
    res = resolver.resolve(q)
    print(f"\n[QUERY]: '{q}'")
    if res:
        print(f"  └─ ✔ RESOLVIDO PELA GOLDEN SOURCE! ({res['resolved_by']})")
        print(f"     Fonte: {res['sources']}")
        print(f"     Resposta:\n{res['answer']}")
    else:
        print("  └─ ℹ Não resolvido deterministicamente -> Encaminhado para o RAG Fallback.")
