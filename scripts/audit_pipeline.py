"""
audit_pipeline.py — DUQUE IA RAG Failure Audit Engine
======================================================
Ferramenta de observabilidade e diagnóstico de causa raiz do pipeline RAG.
Audita todas as 8 etapas e 12 códigos de falha padronizados sem alterar o banco de dados.

Uso:
  python scripts/audit_pipeline.py --question "Qual endereço do CRAS Jardim Primavera?"
  python scripts/audit_pipeline.py --batch
"""

import os
import sys
import json
import time
import re
import argparse
import unicodedata
from datetime import datetime

# Garante suporte a UTF-8 no Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from agent.agent import DuqueIAAgent
from agent.triage import check_fast_gate, perform_triage, call_triage_llm
from agent.tool_router import ToolRouter
from agent.planner import SemanticRecoveryPlanner
from agent.retrieval import (
    retrieve_context,
    retrieve_structured_secretaria,
    retrieve_structured_service
)
from agent.guardrails import (
    check_input_guardrail,
    check_privacy_guardrail,
    check_competency_guardrail,
    check_legal_guardrail,
    check_output_guardrail
)
from agent.scoring import extract_query_keywords, cosine_similarity, calculate_keyword_score
from agent.confidence import calibrate_confidence
from utils.db_client import query_db
from config.settings import DATABASE_MAIN, DATABASE_VECTOR, OUVIDORIA_CONTACTS

# ---------------------------------------------------------------------------
# CÓDIGOS DE FALHA PADRONIZADOS
# ---------------------------------------------------------------------------
FAILURE_CODES = [
    "NO_FAILURE_DETECTED",
    "TRIAGE_BYPASS",
    "TRIAGE_ROUTING_ERROR",
    "ENTITY_LOSS_IN_REWRITE",
    "ENTITY_SUBSTITUTION",
    "VECTOR_INDEX_OUTDATED",
    "STRUCTURED_NOT_INDEXED",
    "RERANKER_DEGRADATION",
    "LOW_CONFIDENCE_THRESHOLD",
    "FALSE_NEGATIVE_GUARDRAIL",
    "LLM_HALLUCINATION",
    "SECURITY_PRIVACY_BLOCKED"
]

# Termos e Entidades Conhecidas do Município para Auditoria de Entidades
KNOWN_ENTITIES = {
    "cras": ["cras", "centro de referencia de assistencia social"],
    "ubs": ["ubs", "unidade basica de saude"],
    "upa": ["upa", "unidade de pronto atendimento"],
    "uph": ["uph", "unidade de pronto atendimento hospitalar"],
    "fundec": ["fundec", "fundacao de apoio a escola tecnica"],
    "iptu": ["iptu"],
    "colab": ["colab"],
    "ouvidoria": ["ouvidoria"],
    "prefeito": ["prefeito"],
    "bairros": [
        "jardim primavera", "xerem", "xerém", "imbabie", "imbariê", "saracuruna",
        "parque paulista", "pilar", "campos eliseos", "campos elíseos", "pantanal",
        "centenario", "centenário", "25 de agosto"
    ],
    "secretarias": [
        "obras", "urbanismo", "saude", "saúde", "educacao", "educação",
        "fazenda", "assistencia social", "assistência social", "meio ambiente",
        "seguranca publica", "segurança pública", "transportes"
    ]
}

def normalize_text(text: str) -> str:
    """Normaliza texto para minúsculas e sem acentuação."""
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return re.sub(r'[^\w\s]', ' ', text).strip()

def extract_entities(text: str) -> list:
    """Extrai entidades conhecidas presentes no texto."""
    norm = normalize_text(text)
    found = []
    
    # Entidades diretas
    for cat, aliases in KNOWN_ENTITIES.items():
        for alias in aliases:
            alias_norm = normalize_text(alias)
            if re.search(rf"\b{re.escape(alias_norm)}\b", norm):
                found.append(alias.upper() if len(alias) <= 6 else alias.title())
                break
                
    # Palavras em caixa alta ou siglas curtas
    siglas = re.findall(r'\b[A-Z]{2,8}\b', text)
    for s in siglas:
        if s not in found and s.lower() not in ["QUAL", "ONDE", "COMO", "PARA"]:
            found.append(s)
            
    return list(set(found))

def compare_entities(original_text: str, rewritten_text: str) -> tuple:
    """Compara entidades da query original vs reescrita para detectar perda ou substituição."""
    orig_entities = extract_entities(original_text)
    rewr_entities = extract_entities(rewritten_text)
    
    loss = [e for e in orig_entities if not any(normalize_text(e) in normalize_text(r) for r in rewr_entities)]
    
    substitution = []
    # Detecção de substituição de siglas específicas por termos genéricos (ex: CRAS -> Assistência Social)
    orig_norm = normalize_text(original_text)
    rewr_norm = normalize_text(rewritten_text)
    
    if "cras" in orig_norm and "cras" not in rewr_norm and ("assistencia" in rewr_norm or "social" in rewr_norm):
        substitution.append({"original": "CRAS", "rewritten": "Assistência Social"})
    if "upa" in orig_norm and "upa" not in rewr_norm and ("saude" in rewr_norm or "hospital" in rewr_norm):
        substitution.append({"original": "UPA", "rewritten": "Hospital/Saúde"})
    if "iptu" in orig_norm and "iptu" not in rewr_norm and ("imposto" in rewr_norm or "fazenda" in rewr_norm):
        substitution.append({"original": "IPTU", "rewritten": "Imposto/Fazenda"})
        
    return loss, substitution

def check_answer_supported_by_context(answer: str, context_chunks: list) -> tuple:
    """Verifica se os fatos principais da resposta gerada estão fundamentados nos chunks recuperados."""
    if not answer or not context_chunks:
        return False, 0.0
        
    combined_context = " ".join([c.get("content", "") + " " + c.get("title", "") for c in context_chunks])
    context_norm = normalize_text(combined_context)
    
    # Extrai telefones, emails e nomes próprios da resposta
    answer_phones = re.findall(r'\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}', answer)
    answer_urls = re.findall(r'https?://[^\s]+|duquedecaxias\.colab\.re', answer)
    
    if not context_norm:
        return False, 0.0
        
    # Verifica correspondência de palavras-chave da resposta no contexto
    ans_keywords = [w for w in extract_query_keywords(answer) if len(w) >= 4 and w not in ["duque", "caxias", "prefeitura", "municipal", "favor", "posso", "ajudar"]]
    
    if not ans_keywords:
        return True, 1.0
        
    matched = [w for w in ans_keywords if normalize_text(w) in context_norm]
    support_score = round(len(matched) / len(ans_keywords), 2) if ans_keywords else 1.0
    
    # Validação de telefones: se a resposta deu um telefone que não está no contexto nem nos contatos da Ouvidoria
    for ph in answer_phones:
        ph_clean = re.sub(r'\D', '', ph)
        if ph_clean and ph_clean not in re.sub(r'\D', '', combined_context) and ph_clean not in ["2126523835", "21998245903"]:
            support_score = round(support_score * 0.5, 2)
            
    supported = support_score >= 0.50
    return supported, support_score


class RAGPipelineAuditor:
    """Motor de Auditoria Passo-a-Passo do Pipeline RAG."""
    
    def __init__(self, agent: DuqueIAAgent = None):
        self.agent = agent or DuqueIAAgent()
        
    def audit_question(self, query: str, history: list = None) -> dict:
        """Executa a auditoria completa de uma pergunta e retorna o raio-x em JSON."""
        start_time = time.time()
        q_original = query.strip()
        
        audit_res = {
            "timestamp": datetime.now().isoformat(),
            "question": q_original,
            "triage": {},
            "query_rewriting": {},
            "planner": {},
            "retrieval": {},
            "context_chunks_sent_to_llm": [],
            "reranking": {},
            "generation": {},
            "root_cause_diagnosis": {
                "code": "NO_FAILURE_DETECTED",
                "details": "RAG executado e auditado sem falhas."
            }
        }
        
        # -------------------------------------------------------------------
        # ETAPA 1: Input Guardrails & Security Audit
        # -------------------------------------------------------------------
        is_inj = check_input_guardrail(q_original)
        is_priv = check_privacy_guardrail(q_original)
        is_comp = check_competency_guardrail(q_original)
        is_leg = check_legal_guardrail(q_original)
        
        if is_inj or is_priv or is_comp or is_leg:
            block_reason = "Prompt Injection" if is_inj else "LGPD / Privacidade" if is_priv else "Fora de Competência" if is_comp else "Jurídico"
            audit_res["triage"] = {
                "intent": "SECURITY_BLOCKED",
                "handler": "SecurityHandler",
                "source": "INPUT_GUARDRAIL",
                "rag_executed": False,
                "confidence": 1.0
            }
            audit_res["root_cause_diagnosis"] = {
                "code": "SECURITY_PRIVACY_BLOCKED",
                "details": f"Bloqueio de segurança legítimo na entrada por regra: {block_reason}."
            }
            return audit_res
            
        # -------------------------------------------------------------------
        # ETAPA 1.5: Golden Source Layer (Resolução Determinística 0ms)
        # -------------------------------------------------------------------
        try:
            from agent.entity_resolver import GoldenSourceResolver
            resolver = GoldenSourceResolver(db_path=self.agent.db_path)
            golden_res = resolver.resolve(q_original)
            if golden_res:
                ans = golden_res["answer"]
                audit_res["triage"] = {
                    "intent": golden_res["intent_detected"],
                    "handler": golden_res["resolved_by"],
                    "source": "GOLDEN_SOURCE_LAYER",
                    "rag_executed": True,
                    "needs_clarification": False,
                    "confidence": 1.0
                }
                audit_res["generation"] = {
                    "prompt_length": 0,
                    "response_before_guardrail": ans,
                    "guardrail_passed": True,
                    "response_after_guardrail": ans,
                    "answer_supported_by_context": True,
                    "support_score": 1.0
                }
                audit_res["root_cause_diagnosis"] = {
                    "code": "NO_FAILURE_DETECTED",
                    "details": f"Resolvido instantaneamente via {golden_res['resolved_by']} (0ms, 100% de precisão)."
                }
                return audit_res
        except Exception as e:
            print(f"[Audit Warning] Falha na Golden Source Layer: {e}", file=sys.stderr)

        # -------------------------------------------------------------------
        # ETAPA 2: Triagem (Fast Gate → Cache → Gemini LLM)
        # -------------------------------------------------------------------
        triage_info = perform_triage(
            db_path=self.agent.db_cache,
            query=q_original,
            gemini_client=self.agent.gemini_client,
            history=history
        )
        
        intent = triage_info.get("intent", "RAG_GERAL")
        next_agent = triage_info.get("next_agent", "RAG_HANDLER")
        triage_source = triage_info.get("source", "UNKNOWN")
        rewritten_query = triage_info.get("rewritten_query", q_original) or q_original
        
        rag_executed = (next_agent == "RAG_HANDLER")
        
        audit_res["triage"] = {
            "intent": intent,
            "handler": next_agent,
            "source": triage_source,
            "rag_executed": rag_executed,
            "needs_clarification": triage_info.get("needs_clarification", False),
            "confidence": triage_info.get("confidence", 0.0)
        }
        
        # Se a triagem desviou a pergunta para um Handler não-RAG
        if not rag_executed:
            if intent in ["LGPD", "ESCALONAMENTO_HUMANO", "FORA_COMPETENCIA", "JURIDICO"]:
                diag_code = "SECURITY_PRIVACY_BLOCKED"
                details = f"Encaminhado corretamente para SecurityHandler (Intenção: {intent})."
            else:
                diag_code = "TRIAGE_BYPASS"
                details = f"Percebida falha de roteamento. A triagem desviou a pergunta do RAG para '{next_agent}' sob a intenção '{intent}'."
                
            audit_res["root_cause_diagnosis"] = {
                "code": diag_code,
                "details": details
            }
            if diag_code == "TRIAGE_BYPASS":
                return audit_res
                
        # -------------------------------------------------------------------
        # ETAPA 3: Query Rewriter & Loss/Substitution Entity Audit
        # -------------------------------------------------------------------
        entity_loss, entity_substitution = compare_entities(q_original, rewritten_query)
        orig_entities = extract_entities(q_original)
        rewr_entities = extract_entities(rewritten_query)
        
        audit_res["query_rewriting"] = {
            "original": q_original,
            "rewritten": rewritten_query,
            "entities_original": orig_entities,
            "entities_rewritten": rewr_entities,
            "entity_loss": entity_loss,
            "entity_substitution": entity_substitution
        }
        
        if entity_substitution:
            audit_res["root_cause_diagnosis"] = {
                "code": "ENTITY_SUBSTITUTION",
                "details": f"A reescrita alterou/substituiu entidades críticas: {entity_substitution}"
            }
        elif entity_loss:
            audit_res["root_cause_diagnosis"] = {
                "code": "ENTITY_LOSS_IN_REWRITE",
                "details": f"A reescrita perdeu entidades cruciais da pergunta original: {entity_loss}"
            }

        # -------------------------------------------------------------------
        # ETAPA 4: Tool Router & Planner Semântico (LORS)
        # -------------------------------------------------------------------
        tools_selected = ToolRouter.select_tools(intent, [q_original])
        planner = SemanticRecoveryPlanner(self.agent.gemini_client)
        plan = planner.plan_recovery(rewritten_query, history=history)
        
        plan_queries = plan.get("queries", [rewritten_query])
        plan_focus = plan.get("focus", ["general"])
        
        audit_res["planner"] = {
            "intent": plan.get("intent", "general"),
            "queries": plan_queries,
            "focus": plan_focus,
            "tools_selected": tools_selected
        }
        
        # -------------------------------------------------------------------
        # ETAPA 5: Comparação Aprofundada — Structured DB vs Vector DB
        # -------------------------------------------------------------------
        q_keywords = extract_query_keywords(rewritten_query)
        
        # Busca isolada Estruturada
        struct_sec = retrieve_structured_secretaria(self.agent.db_path, rewritten_query, q_keywords)
        struct_serv = retrieve_structured_service(self.agent.db_path, rewritten_query, q_keywords, self.agent.using_real)
        structured_candidates = struct_sec + struct_serv
        
        # Busca isolada Vetorial em duque_ia_chunks
        vector_candidates = []
        try:
            query_vector = self.agent.gemini_client.get_embedding(rewritten_query, is_query=True) if self.agent.using_real else None
            rows_chunks = query_db(DATABASE_VECTOR, "SELECT source, category, content, embedding, metadata FROM duque_ia_chunks")
            for row in rows_chunks:
                source, category, content, emb_str, meta_str = row
                try:
                    meta = json.loads(meta_str) if meta_str else {}
                except Exception:
                    meta = {}
                title = meta.get("title", source)
                
                if self.agent.using_real and query_vector and emb_str:
                    try:
                        emb = json.loads(emb_str)
                        score = cosine_similarity(query_vector, emb) if len(emb) == len(query_vector) else 0.0
                    except Exception:
                        score = 0.0
                else:
                    score = calculate_keyword_score(rewritten_query, content, title)
                    
                if score >= 0.30:
                    vector_candidates.append({
                        "source": source,
                        "title": title,
                        "score": round(score, 4),
                        "content": content[:200]
                    })
        except Exception as e:
            print(f"[Audit Warning] Falha na leitura direta do banco vetorial: {e}", file=sys.stderr)
            
        structured_count = len(structured_candidates)
        vector_count = len(vector_candidates)
        structured_found = structured_count > 0
        vector_found = vector_count > 0
        
        audit_res["retrieval"]["structured_comparison"] = {
            "structured_found": structured_found,
            "vector_found": vector_found,
            "structured_count": structured_count,
            "vector_count": vector_count
        }
        
        # Detecção de dessincronização
        if structured_found and not vector_found:
            audit_res["root_cause_diagnosis"] = {
                "code": "VECTOR_INDEX_OUTDATED",
                "details": f"Informação existe no banco estruturado ({structured_count} registros), mas está AUSENTE no banco vetorial."
            }
        elif vector_found and not structured_found and any(w in rewritten_query.lower() for w in ["telefone", "endereco", "contato"]):
            audit_res["root_cause_diagnosis"] = {
                "code": "STRUCTURED_NOT_INDEXED",
                "details": "Informação encontrada no texto vetorial geral, mas ausente nas tabelas estruturadas oficiais."
            }

        # -------------------------------------------------------------------
        # ETAPA 6: Hybrid Retrieval Real + Re-ranker Delta Audit
        # -------------------------------------------------------------------
        results_retrieved = retrieve_context(
            query=rewritten_query,
            db_path=self.agent.db_path,
            using_real=self.agent.using_real,
            similarity_threshold=self.agent.similarity_threshold,
            gemini_client=self.agent.gemini_client,
            reranker=self.agent.reranker,
            top_k=3,
            intent_info={"intent": type("QueryIntentEnum", (), {"value": intent, "name": intent})()},
            tools_selected=tools_selected
        )
        
        retrieval_returned = len(results_retrieved) > 0
        max_score = results_retrieved[0].get("similarity", 0.0) if retrieval_returned else 0.0
        
        boosts_applied = []
        q_norm = normalize_text(rewritten_query)
        if any(w in q_norm for w in ["xerem", "imbarie", "jardim primavera", "saracuruna"]):
            boosts_applied.append("bairro_locality_boost")
        if any(w in q_norm for w in ["hospital", "upa", "uph", "emergencia", "medico"]):
            boosts_applied.append("saude_clinico_boost")
        if any(w in q_norm for w in ["prefeito", "distrito", "origem"]):
            boosts_applied.append("governanca_cidade_boost")
            
        audit_res["retrieval"].update({
            "retrieval_executed": True,
            "retrieval_returned_results": retrieval_returned,
            "max_similarity_score": round(max_score, 4),
            "effective_threshold": self.agent.similarity_threshold,
            "boosts_applied": boosts_applied
        })
        
        # -------------------------------------------------------------------
        # ETAPA 6.1: Golden Document Tracking (Rastreamento do Gabarito)
        # -------------------------------------------------------------------
        golden_found = False
        golden_title = "N/A"
        rank_before = None
        rank_after = None
        used_in_prompt = False

        if retrieval_returned:
            before_rerank = [{"source": r["source"], "title": r.get("title", r["source"]), "score": r.get("semantic_score", 0.0)} for r in results_retrieved[:5]]
            after_rerank = [{"source": r["source"], "title": r.get("title", r["source"]), "score": r.get("similarity", 0.0)} for r in results_retrieved[:5]]
            
            position_deltas = {}
            for idx_after, item in enumerate(after_rerank):
                src = item["source"]
                idx_before = next((i for i, b in enumerate(before_rerank) if b["source"] == src), idx_after)
                position_deltas[item["title"][:40]] = idx_before - idx_after
                
            audit_res["reranking"] = {
                "candidates_before": before_rerank,
                "candidates_after": after_rerank,
                "position_deltas": position_deltas
            }
            
            # Identificação do Golden Document (Maior overlap de entidades com a pergunta original)
            best_overlap = 0
            for idx, item in enumerate(before_rerank, 1):
                item_text = (item["title"] + " " + item["source"]).lower()
                matches = sum(1 for e in orig_entities if normalize_text(e) in normalize_text(item_text))
                if matches > best_overlap:
                    best_overlap = matches
                    golden_found = True
                    golden_title = item["title"]
                    rank_before = idx
                    
            if golden_found:
                rank_after = next((i + 1 for i, a in enumerate(after_rerank) if a["title"] == golden_title), rank_before)
                used_in_prompt = rank_after <= 3

            audit_res["retrieval"]["golden_document_tracking"] = {
                "golden_document_found": golden_found,
                "golden_document_title": golden_title,
                "golden_document_rank_before": rank_before,
                "golden_document_rank_after": rank_after,
                "golden_document_used_in_prompt": used_in_prompt
            }

            # Detecta se candidato com melhor match diminuiu de posição
            for title_k, delta in position_deltas.items():
                if delta < -2 and audit_res["root_cause_diagnosis"]["code"] == "NO_FAILURE_DETECTED":
                    audit_res["root_cause_diagnosis"] = {
                        "code": "RERANKER_DEGRADATION",
                        "details": f"O Cross-Encoder rebaixou significativamente o candidato '{title_k}' em {abs(delta)} posições."
                    }
                    
        # Se a busca retornou abaixo do threshold
        if not retrieval_returned or max_score < self.agent.similarity_threshold:
            if audit_res["root_cause_diagnosis"]["code"] == "NO_FAILURE_DETECTED":
                audit_res["root_cause_diagnosis"] = {
                    "code": "LOW_CONFIDENCE_THRESHOLD",
                    "details": f"O retrieval retornou score máximo {max_score:.4f}, que é inferior ao threshold exigido ({self.agent.similarity_threshold})."
                }

        # -------------------------------------------------------------------
        # ETAPA 7: Context Chunks Sent to LLM Audit
        # -------------------------------------------------------------------
        chunks_sent = []
        for idx, r in enumerate(results_retrieved, 1):
            chunks_sent.append({
                "rank": idx,
                "source": r.get("source", ""),
                "title": r.get("title", ""),
                "category": r.get("category", ""),
                "score": round(r.get("similarity", 0.0), 4),
                "text_preview": r.get("content", "")[:250] + "..." if len(r.get("content", "")) > 250 else r.get("content", "")
            })
            
        audit_res["context_chunks_sent_to_llm"] = chunks_sent

        # -------------------------------------------------------------------
        # ETAPA 8: Generation & Output Guardrail Audit
        # -------------------------------------------------------------------
        from agent.handlers import RagHandler
        rag_handler = RagHandler()
        
        # Gera a resposta normal pelo RAG Handler
        res_dict = rag_handler.execute(
            query=q_original,
            triage_info=triage_info,
            agent=self.agent,
            conversation_id=f"audit_{int(time.time())}",
            start_time=start_time,
            history=history
        )
        
        candidate_answer = res_dict.get("answer", "")
        last_context = getattr(self.agent, "_last_context", "")
        
        # Teste do Output Guardrail
        guardrail_passed = check_output_guardrail(
            query=q_original,
            answer=candidate_answer,
            gemini_client=self.agent.gemini_client,
            context=last_context,
            history=history,
            triage_info=triage_info
        )
        
        answer_supported, support_score = check_answer_supported_by_context(candidate_answer, results_retrieved)
        
        final_answer = candidate_answer if guardrail_passed else (
            "Desculpe, não consegui formular uma resposta segura ou precisa para sua pergunta. "
            f"Para registrar sua solicitação com segurança, contate a Ouvidoria Geral: {OUVIDORIA_CONTACTS['telefone']}."
        )
        
        audit_res["generation"] = {
            "prompt_length": len(last_context),
            "response_before_guardrail": candidate_answer,
            "guardrail_passed": guardrail_passed,
            "response_after_guardrail": final_answer,
            "answer_supported_by_context": answer_supported,
            "support_score": support_score
        }
        
        # Diagnósticos de geração e guardrail
        if not guardrail_passed:
            if candidate_answer and ("não encontrei" not in candidate_answer.lower() and "desculpe" not in candidate_answer.lower()):
                if audit_res["root_cause_diagnosis"]["code"] == "NO_FAILURE_DETECTED":
                    audit_res["root_cause_diagnosis"] = {
                        "code": "FALSE_NEGATIVE_GUARDRAIL",
                        "details": "O Output Guardrail rejeitou indevidamente uma resposta gerada pelo LLM e a substituiu por mensagem genérica."
                    }
                    
        elif not answer_supported and support_score < 0.35 and retrieval_returned:
            if audit_res["root_cause_diagnosis"]["code"] == "NO_FAILURE_DETECTED":
                audit_res["root_cause_diagnosis"] = {
                    "code": "LLM_HALLUCINATION",
                    "details": f"A resposta gerada possui fatos/dados não suportados pelos chunks de contexto (Score de Suporte: {support_score})."
                }

        audit_res["total_execution_ms"] = round((time.time() - start_time) * 1000, 2)
        return audit_res


# ---------------------------------------------------------------------------
# BENCHMARK EM LOTE (BATCH MODE)
# ---------------------------------------------------------------------------
def run_batch_benchmark(auditor: RAGPipelineAuditor, output_file: str = None):
    """Executa a suíte de auditoria sobre 30 perguntas de teste e compila relatório estatístico."""
    from scripts.test_30_perguntas import PERGUNTAS
    
    print("=" * 75)
    print("      DUQUE IA — BENCHMARK ESTATÍSTICO DE AUDITORIA DO RAG")
    print(f"      Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 75)
    
    results = []
    breakdown = {code: 0 for code in FAILURE_CODES}
    
    total = len(PERGUNTAS)
    success_count = 0
    failure_count = 0
    
    for i, item in enumerate(PERGUNTAS, 1):
        pid = item["id"]
        cat = item["categoria"]
        q = item["pergunta"]
        
        print(f"[{i:02d}/{total}] Auditando ({pid} - {cat}): '{q[:50]}...'")
        res = auditor.audit_question(q)
        diag = res["root_cause_diagnosis"]
        code = diag["code"]
        
        breakdown[code] = breakdown.get(code, 0) + 1
        if code in ["NO_FAILURE_DETECTED", "SECURITY_PRIVACY_BLOCKED"]:
            success_count += 1
            print(f"   └─ ✔ {code}")
        else:
            failure_count += 1
            print(f"   └─ ✘ {code}: {diag['details'][:80]}...")
            
        results.append(res)
        time.sleep(1.0) # Prevenção leve de rate-limit
        
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": total,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate_pct": round((success_count / total) * 100, 2),
        "failure_breakdown": breakdown,
        "detailed_results": results
    }
    
    if not output_file:
        os.makedirs(os.path.join(_PROJECT_ROOT, "metrics"), exist_ok=True)
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(_PROJECT_ROOT, "metrics", f"audit_benchmark_{ts_str}.json")
        
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        
    print("\n" + "=" * 75)
    print("                  RESUMO ESTATÍSTICO DA AUDITORIA")
    print("=" * 75)
    print(f"  • Total de Perguntas Auditadas: {total}")
    print(f"  • Sucessos / Casos Válidos:    {success_count} ({summary['success_rate_pct']}%)")
    print(f"  • Falhas de RAG Identificadas: {failure_count}")
    print("\n  [Distribuição por Causa Raiz / Breakdown]:")
    for code, cnt in breakdown.items():
        if cnt > 0:
            print(f"    - {code:<28}: {cnt}")
    print(f"\n Relatório completo salvo em: [audit_benchmark]({output_file})")
    print("=" * 75)


# ---------------------------------------------------------------------------
# MAIN CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Duque IA — RAG Failure Audit Engine")
    parser.add_argument("--question", "-q", type=str, help="Pergunta individual do munícipe para auditagem.")
    parser.add_argument("--batch", "-b", action="store_true", help="Executa o benchmark estatístico em lote.")
    parser.add_argument("--output", "-o", type=str, help="Caminho do arquivo JSON de saída.")
    
    args = parser.parse_args()
    auditor = RAGPipelineAuditor()
    
    if args.batch:
        run_batch_benchmark(auditor, args.output)
    elif args.question:
        res = auditor.audit_question(args.question)
        json_output = json.dumps(res, ensure_ascii=False, indent=2)
        print(json_output)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f"\n[Info] Resultado da auditoria salvo em '{args.output}'.")
    else:
        # Exemplo padrão se executado sem argumentos
        default_q = "Qual endereço do CRAS Jardim Primavera?"
        print(f"[Info] Nenhuma opção informada. Executando auditoria padrão para: '{default_q}'\n")
        res = auditor.audit_question(default_q)
        print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
