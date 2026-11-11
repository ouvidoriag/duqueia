# -*- coding: utf-8 -*-
"""
Testes de Homologação da Etapa 4:
1. Sibling Chunk Expansion (Expansão Hierárquica de Irmãos) no ContextBuilder
2. In-Memory Vector Index Cache com 100% de cobertura (2.748 vetores de 3072d)
"""

import os
import sys
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from agent.candidate import Candidate
from agent.context_builder import ContextBuilder
from agent.retrieval import _get_vector_index_cache, invalidate_vector_cache

def test_vector_cache_full_coverage():
    """Valida se o cache vetorial em memória carrega exatamente os 2.748 chunks com vetores 3072d."""
    invalidate_vector_cache()
    cache = _get_vector_index_cache(force_reload=True)
    assert cache is not None, "Cache vetorial não pôde ser construído"
    
    matrix = cache["matrix"]
    metadata = cache["metadata"]
    
    assert len(metadata) == 2748, f"Esperado 2748 chunks no cache, encontrado {len(metadata)}"
    assert matrix.shape == (2748, 3072), f"Matriz deve ter shape (2748, 3072), encontrado {matrix.shape}"
    
    # 100% dos chunks devem ter embedding válido de 3072 dimensões
    valid_count = sum(1 for m in metadata if m["has_embedding"])
    assert valid_count == 2748, f"Todos os 2748 chunks devem ter embedding válido, mas apenas {valid_count} têm"

def test_sibling_expansion_single_part():
    """Testa expansão automática quando apenas a Parte 1 de um serviço é fornecida."""
    cand_p1 = Candidate(
        source="servico_00086_p1",
        title="Serviço: Visita Domiciliar — Parte 1: Descrição e Documentação",
        category="saude",
        content="SERVIÇO MUNICIPAL: Visita Domiciliar\nDESCRIÇÃO: Atendimento na residência dos usuários cadastrados na Estratégia de Saúde da Família.",
        retrieval_score=0.92
    )
    
    context_text, sources, final_cands = ContextBuilder.build_context([cand_p1], top_k=4)
    
    assert len(sources) >= 1
    # Verifica que o serviço base foi consolidado
    assert "servico_00086" in sources[0]
    # Verifica que o conteúdo expandido contém tanto a descrição da P1 quanto as etapas da P2
    assert "Visita Domiciliar" in context_text
    assert "ETAPAS / PASSO A PASSO" in context_text or "Etapas" in context_text

def test_sibling_expansion_both_parts():
    """Testa se fornecer Parte 1 e Parte 2 unifica sob o mesmo serviço sem duplicar slots."""
    cand_p1 = Candidate(
        source="servico_00086_p1",
        title="Serviço: Visita Domiciliar — Parte 1",
        category="saude",
        content="SERVIÇO MUNICIPAL: Visita Domiciliar (P1)",
        retrieval_score=0.90
    )
    cand_p2 = Candidate(
        source="servico_00086_p2",
        title="Serviço: Visita Domiciliar — Parte 2",
        category="saude",
        content="ETAPAS / PASSO A PASSO: Visita Domiciliar (P2)",
        retrieval_score=0.88
    )
    
    context_text, sources, final_cands = ContextBuilder.build_context([cand_p1, cand_p2], top_k=4)
    
    # Deve unificar as duas partes sob 1 único bloco de fonte
    assert len(sources) == 1
    assert "servico_00086" in sources[0]
    assert "Visita Domiciliar (P1)" in context_text
    assert "Visita Domiciliar (P2)" in context_text

def test_canonical_rules_priority_preserved():
    """Garante que regras canônicas de negócio continuam no topo do contexto."""
    cand_regra = Candidate(
        source="regras_negocio (regra_canon_casa_do_autista_rua_jandira_status)",
        title="Regra Canônica: Casa do Autista",
        category="regras_negocio",
        content="A Casa do Autista (Policlínica Jandira de Freitas) está em pleno funcionamento.",
        retrieval_score=0.95
    )
    cand_servico = Candidate(
        source="servico_00001_alvara",
        title="Serviço de Alvará",
        category="fazenda",
        content="Orientações sobre emissão de alvará de funcionamento.",
        retrieval_score=0.89
    )
    
    context_text, sources, final_cands = ContextBuilder.build_context([cand_servico, cand_regra], top_k=4)
    
    assert sources[0].startswith("regras_negocio")
    assert "DIRETRIZ DE GOVERNANÇA MÁXIMA E OBRIGATÓRIA" in context_text

if __name__ == "__main__":
    print("[1/4] Executando test_vector_cache_full_coverage...")
    test_vector_cache_full_coverage()
    print("      -> APROVADO!")

    print("[2/4] Executando test_sibling_expansion_single_part...")
    test_sibling_expansion_single_part()
    print("      -> APROVADO!")

    print("[3/4] Executando test_sibling_expansion_both_parts...")
    test_sibling_expansion_both_parts()
    print("      -> APROVADO!")

    print("[4/4] Executando test_canonical_rules_priority_preserved...")
    test_canonical_rules_priority_preserved()
    print("      -> APROVADO!")

    print("\nTODOS OS TESTES DA ETAPA 4 FORAM APROVADOS COM SUCESSO (100%)!")
