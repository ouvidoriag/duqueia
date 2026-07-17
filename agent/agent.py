import os
import json
import re
import sys
import time

from utils.gemini_client import GeminiClient
from utils.db_client import execute_db, query_one
from storage import storage_manager
from agent.triage import perform_triage
from config.settings import (
    DATABASE_MAIN,
    DATABASE_VECTOR,
    DATABASE_CACHE,
    DATABASE_TELEMETRY,
    EMBEDDING_DIMS,
    OUVIDORIA_CONTACTS,
    USE_TRIAGE_LAYER,
    PRIVACY_BLOCKED_MESSAGE,
    COMPETENCY_BLOCKED_MESSAGE,
    LEGAL_BLOCKED_MESSAGE,
    SECURITY_BLOCKED_MESSAGE
)
from agent.models import QueryIntent
from agent.router import QueryAnalyzer, SystemIntentHandler
from agent.reranker import BaseReranker, NoOpReranker, GeminiCrossEncoder
from agent.scoring import extract_query_keywords
from agent.guardrails import (
    check_input_guardrail,
    check_privacy_guardrail,
    check_competency_guardrail,
    check_legal_guardrail,
    check_output_guardrail
)
from agent.fallback import build_fallback_guidance, is_query_too_vague
from agent.confidence import calibrate_confidence
from agent.retrieval import retrieve_context
from agent.handlers import (
    SecurityHandler,
    ConversationHandler,
    CollectorHandler,
    AmbiguityHandler,
    PrivateResponsibilityHandler,
    ProgramacaoHandler,
    RagHandler,
    AuthorityHandler
)


# Instancia o cliente globalmente
gemini_client = GeminiClient()

class DuqueIAAgent:
    """Agente de Atendimento Virtual RAG Inteligente para Duque de Caxias."""
    
    def __init__(self, db_path: str = DATABASE_MAIN, reranker: BaseReranker = None):
        self.db_path = db_path
        self.db_main = DATABASE_MAIN
        self.db_vector = DATABASE_VECTOR
        self.db_cache = DATABASE_CACHE
        self.db_telemetry = DATABASE_TELEMETRY
        self.storage = storage_manager
        
        # Reranker de segundo estágio: GeminiCrossEncoder em produção, NoOpReranker offline.
        # Inicializado após self.using_real — ver linha abaixo.
        self._reranker_override = reranker
        self.using_real = len(gemini_client.api_keys) > 0
        self.similarity_threshold = 0.50 if self.using_real else 0.25
        self.gemini_client = gemini_client
        
        # Ativa Cross-Encoder real em produção; offline usa passthrough NoOp
        if self._reranker_override is not None:
            self.reranker = self._reranker_override
        elif self.using_real:
            self.reranker = GeminiCrossEncoder(
                gemini_client=gemini_client,
                max_candidates=8,   # máximo de chunks avaliados pelo cross-encoder
                min_candidates=2,   # abaixo disso, pula o reranking
                score_weight=0.6,   # 60% cross-encoder + 40% hybrid score original
            )
        else:
            self.reranker = NoOpReranker()
        
        # Tabela de roteamento de Handlers
        self.handlers = {
            "SECURITY_HANDLER": SecurityHandler(),
            "CONVERSATION_HANDLER": ConversationHandler(),
            "COLLECTOR_HANDLER": CollectorHandler(),
            "AMBIGUITY_HANDLER": AmbiguityHandler(),
            "PRIVATE_RESPONSIBILITY_HANDLER": PrivateResponsibilityHandler(),
            "PROGRAMACAO_HANDLER": ProgramacaoHandler(),
            "RAG_HANDLER": RagHandler(),
            "AUTHORITY_HANDLER": AuthorityHandler()
        }
        
        os.makedirs(os.path.join(os.path.dirname(self.db_path), "..", "logs"), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(self.db_path), "..", "metrics"), exist_ok=True)
        
        if not hasattr(DuqueIAAgent, "_history"):
            DuqueIAAgent._history = {}
        if not hasattr(DuqueIAAgent, "_model_sessions"):
            DuqueIAAgent._model_sessions = {}
        
        # Garante a existência e validação da metadata de embeddings no vector.db
        self._initialize_and_validate_embedding_metadata()


    def _initialize_and_validate_embedding_metadata(self):
        """Valida se o provedor e modelo de embedding gravado na DB é idêntico ao configurado no cliente."""
        if not os.path.exists(self.db_vector):
            return
            
        current_provider = "gemini" if self.using_real else "local_hash"
        current_model = gemini_client.embedding_model_name if self.using_real else "deterministic_hash_768"
        current_dimension = EMBEDDING_DIMS.get(current_model, 768)
        
        execute_db(self.db_vector, """
        CREATE TABLE IF NOT EXISTS embedding_metadata (
            provider TEXT,
            model TEXT,
            dimension INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        row = query_one(self.db_vector, "SELECT provider, model, dimension FROM embedding_metadata LIMIT 1")
        
        if not row:
            execute_db(self.db_vector, "INSERT INTO embedding_metadata (provider, model, dimension) VALUES (?, ?, ?)",
                       (current_provider, current_model, current_dimension))
        else:
            db_provider, db_model, db_dimension = row
            if db_dimension != current_dimension:
                print(f"[Warning/Guardrail] INCOMPATIBILIDADE DE ESPAÇO VETORIAL DETECTADA!", file=sys.stderr)
                print(f"  -> No Banco: Provider={db_provider}, Model={db_model}, Dim={db_dimension}", file=sys.stderr)
                print(f"  -> No Cliente: Provider={current_provider}, Model={current_model}, Dim={current_dimension}", file=sys.stderr)
                print("  Recomendado reexecutar o pipeline de ingestão: 'make embed'", file=sys.stderr)
            elif db_model != current_model:
                print(f"[Info] Modelo de embedding alterado: Banco={db_model}, Cliente={current_model} (dimensões compatíveis: {current_dimension})", file=sys.stderr)


    def log_execution_metrics(self, user_query: str, retrieval_time: float, llm_time: float, 
                              total_time: float, similarity_score: float, tokens_usados: int, 
                              embedding_cost: float, rewritten_query: str = None, 
                              structured_hit: bool = False, vector_count: int = 0, 
                              selected_sources: list = None):
        """Salva as métricas exigidas pela Fase 5 e Instrumentação em arquivos csv e log."""
        base_dir = os.path.dirname(self.db_path)
        log_path = os.path.join(base_dir, "..", "logs", "execution.log")
        csv_path = os.path.join(base_dir, "..", "metrics", "retrieval_performance.csv")
        
        is_new_csv = not os.path.exists(csv_path)
        with open(csv_path, "a", encoding="utf-8") as f:
            if is_new_csv:
                f.write("timestamp,query,retrieval_time_ms,llm_time_ms,total_time_ms,similarity_score,tokens_used,cost_usd\n")
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{user_query.replace(',', ';')},"
                    f"{retrieval_time*1000:.2f},{llm_time*1000:.2f},{total_time*1000:.2f},"
                    f"{similarity_score:.4f},{tokens_usados},{embedding_cost:.8f}\n")
                    
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ==========================================\n")
            f.write(f"QUERY ORIGINAL: '{user_query}'\n")
            if rewritten_query and rewritten_query != user_query:
                f.write(f"QUERY REESCRITA (LLM): '{rewritten_query}'\n")
            f.write(f"BUSCA ESTRUTURADA: {'✔ Encontrou' if structured_hit else '✘ Não Ativada/Vazia'}\n")
            f.write(f"BUSCA VETORIAL: {vector_count} chunks candidatos\n")
            if selected_sources:
                f.write(f"FONTES SELECIONADAS: {', '.join(selected_sources)}\n")
            f.write(f"TELEMETRIA: RETRIEVAL={retrieval_time*1000:.2f}ms | LLM={llm_time*1000:.2f}ms | TOTAL={total_time*1000:.2f}ms | SIMILARITY={similarity_score:.4f} | TOKENS={tokens_usados}\n")
            f.write("====================================================\n\n")

    def gerar_esclarecimento_contextual(self, query: str, triage_info: dict) -> str:
        """Gera uma pergunta ou orientação de esclarecimento contextualizada."""
        intent = triage_info.get("intent", "RAG_GERAL")
        reason = triage_info.get("reason", "")

        if intent != "OUVIDORIA_MANIFESTACAO":
            # Clarificação Genérica
            fallback_msg = (
                "Para eu te ajudar com as informações corretas, por favor reformule sua pergunta informando "
                "mais detalhes sobre o que você deseja saber (ex: telefone, endereço ou informações de um serviço específico)."
            )
            
            if "obra" in query.lower() or "obras" in query.lower():
                fallback_msg = (
                    "Você poderia me dar mais detalhes sobre qual informação de **obras** você procura?\n\n"
                    "• Se for o **telefone** ou **endereço** da Secretaria de Obras;\n"
                    "• Informações sobre o andamento de uma **obra específica**;\n"
                    "• Como solicitar manutenção ou serviços públicos (**tapa-buraco, pavimentação**)."
                )
            elif "ilumina" in query.lower() or "lampada" in query.lower() or "luz" in query.lower():
                fallback_msg = (
                    "Você poderia detalhar melhor sua dúvida sobre iluminação?\n\n"
                    "• Se deseja solicitar troca de lâmpada em **poste na rua**;\n"
                    "• Se é sobre falta de energia na sua **residência** (Light)."
                )
            elif "barulho" in query.lower() or "som" in query.lower() or "ruido" in query.lower() or "festa" in query.lower():
                fallback_msg = (
                    "Você poderia me esclarecer se o som alto vem de uma **residência particular (como a casa de um vizinho, apartamento ou festa privada)** "
                    "ou se é de um **evento realizado em espaço público (como um show na rua ou festa em praça)**?\n\n"
                    "• Se for barulho de **vizinho/residência particular**, ligue para a **Polícia Militar (190)**.\n"
                    "• Se for **evento ou show na rua/praça pública**, registre o pedido para a **Ordem Urbana** pelo app **Colab** ou site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/)."
                )
                
            if not self.using_real:
                return fallback_msg
                
            system_instruction = (
                "Você é o DUQUE IA, assistente técnico oficial da Prefeitura de Duque de Caxias — RJ.\n"
                "A pergunta do cidadão é muito vaga ou ambígua e precisamos que ele forneça mais contexto.\n"
                "Sua tarefa é gerar uma resposta educada e prestativa solicitando que ele especifique o que deseja saber.\n"
                "Dê exemplos de opções de forma curta (ex: telefone da secretaria, endereço, informações de um serviço público).\n"
                "Se a intenção for 'AMBIGUO_BARULHO', pergunte de forma simpática se o barulho vem de um vizinho/residência particular (Polícia 190) ou de um evento público na rua (Ordem Urbana/Colab).\n"
                "NUNCA fale sobre Ouvidoria, reclamação, denúncia, elogio ou sugestão aqui, pois a intenção dele NÃO é Ouvidoria.\n"
                "Mantenha a resposta muito curta, objetiva, profissional e sem saudações genéricas."
            )
            
            prompt = (
                f"Mensagem do usuário: \"{query}\"\n"
                f"Intenção detectada: {intent}\n"
                f"Motivo do esclarecimento: {reason}\n\n"
                f"Gere a pergunta de esclarecimento:"
            )
        else:
            # Clarificação de Ouvidoria
            fallback_msg = (
                "Para eu te ajudar com as informações corretas ou orientar como registrar sua manifestação no **Colab**, "
                "por favor reformule sua pergunta incluindo o **local ou serviço específico** da prefeitura sobre o qual deseja falar."
            )
            tipo = triage_info.get("tipo_manifestacao", "geral")
            _PERGUNTAS_TIPO = {
                "elogio":    "Que ótimo! Sobre qual **serviço, unidade ou órgão** da Prefeitura você deseja registrar o elogio?",
                "denuncia":  "Entendido. Qual é o **assunto da denúncia**? \n\nEx: irregularidade em obra, serviço não prestado, mau atendimento...",
                "sugestao":  "Que ótimo! Qual **melhoria ou serviço** você gostaria de sugerir à Prefeitura?",
                "reclamacao":"Entendido. Sobre qual **serviço ou problema** você deseja reclamar?\n\nEx: buraco na rua, capina, iluminação pública, lixo...",
                "geral":     "Certo. Sua manifestação é uma **reclamação**, **denúncia**, **sugestão** ou **elogio**? E sobre qual assunto ou serviço municipal?",
            }
            fallback_msg = _PERGUNTAS_TIPO.get(tipo, _PERGUNTAS_TIPO["geral"])
            
            if not self.using_real:
                return fallback_msg
                
            system_instruction = (
                "Você é o DUQUE IA, assistente virtual simpático da Prefeitura de Duque de Caxias — RJ.\n"
                "O cidadão iniciou um atendimento de Ouvidoria (manifestação: reclamação, denúncia, sugestão ou elogio).\n"
                "Sua tarefa é atuar como um Agente Coletor acolhedor e conduzir a conversa de forma INCREMENTAL, solicitando APENAS UMA informação de cada vez.\n"
                "O objetivo principal é coletar: tipo da manifestação (se já não informado), assunto/serviço e contexto (local, descrição) para orientar o cidadão a registrar no Colab.\n"
                "\n"
                "REGRAS DE COMUNICAÇÃO:\n"
                "1. Seja muito simpático, acolhedor e use tom de conversa natural (não robótico).\n"
                "2. Se o tipo de manifestação já é conhecido (elogio/denúncia/sugestão/reclamação), faça apenas UMA pergunta de forma descontraída sobre o assunto específico.\n"
                "3. Se o tipo não é conhecido, pergunte primeiro o tipo, depois o assunto.\n"
                "4. Personalize a pergunta pelo tipo com empatia.\n"
                "5. EVITE SAUDAÇÕES REDUNDANTES: Como o diálogo já está em andamento, NÃO inclua palavras de boas-vindas ou saudações (como 'Olá', 'Oi', 'Como vai', 'Que bom falar com você') se o usuário já foi saudado no início. Vá direto para a coleta de dados de forma natural."
            )
            
            prompt = (
                f"Mensagem do usuário: \"{query}\"\n"
                f"Intenção detectada: {intent}\n"
                f"Tipo de manifestação: {tipo}\n"
                f"Motivo da necessidade de esclarecimento: {reason}\n\n"
                f"Gere a pergunta de esclarecimento para o cidadão:"
            )

        try:
            answer, _, _ = gemini_client.generate_interaction(
                prompt,
                system_instruction=system_instruction,
                model=None
            )
            return answer.strip()
        except Exception as e:
            print(f"[Clarification Warning] Erro ao gerar pergunta de esclarecimento dinâmica: {e}", file=sys.stderr)
            return fallback_msg

    def respond(self, user_query: str, use_triage: bool = None, conversation_id: str = None) -> str:
        """Wrapper para gerenciar o estado da conversa e responder JSON com validação de Output Guardrail."""
        context_holder = {"conversation_id": conversation_id}
        
        # Obtém o histórico conversacional anterior à execução atual
        hist = None
        cid = conversation_id or context_holder.get("conversation_id")
        if cid and hasattr(DuqueIAAgent, "_history") and cid in DuqueIAAgent._history:
            hist = DuqueIAAgent._history[cid]
            
        res_str = self._respond_raw(user_query, use_triage, context_holder)
        # Atualiza a ID da sessão caso tenha sido gerada dinamicamente no respond_raw
        cid = context_holder.get("conversation_id")
        try:
            data = json.loads(res_str)
            data["conversation_id"] = cid
            
            # Validação do Output Guardrail
            answer = data.get("answer", "")
            last_context = getattr(self, "_last_context", None)
            triage_info = data.get("triage_info", None)
            
            if answer and not check_output_guardrail(
                query=user_query,
                answer=answer,
                gemini_client=self.gemini_client,
                context=last_context,
                history=hist,
                triage_info=triage_info
            ):
                # Se a resposta contiver alucinações ou desvios, aplicamos o bloqueio de segurança
                data["answer"] = (
                    "Desculpe, não consegui formular uma resposta segura ou precisa para sua pergunta. "
                    "Para registrar sua solicitação ou denúncia com total segurança, você pode falar diretamente com a nossa **Ouvidoria Geral de Duque de Caxias**:\n\n"
                    f"• Telefone: **{OUVIDORIA_CONTACTS['telefone']}**\n"
                    f"• WhatsApp: **{OUVIDORIA_CONTACTS['whatsapp']}**\n"
                    f"• E-mail: **{OUVIDORIA_CONTACTS['email']}**\n"
                    f"• Online: aplicativo **Colab** ou site oficial da Prefeitura."
                )
                data["intent_detected"] = "output_guardrail_blocked"
                
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            return res_str

    def _respond_raw(self, user_query: str, use_triage: bool = None, context_holder: dict = None) -> str:
        self._last_context = ""
        start_time = time.time()

        if use_triage is None:
            use_triage = USE_TRIAGE_LAYER

        conversation_id = context_holder.get("conversation_id") if context_holder else None
        if not conversation_id:
            conversation_id = f"sess_{int(time.time() * 1000)}"
            if context_holder:
                context_holder["conversation_id"] = conversation_id

        # Extrai o histórico no início para estar sempre disponível
        hist = None
        if conversation_id and hasattr(DuqueIAAgent, "_history") and conversation_id in DuqueIAAgent._history:
            hist = DuqueIAAgent._history[conversation_id]

        # ---------------------------------------------------------------- #
        # 0. Grafo de Estados (LangGraph Lite)                              #
        #    Substitui o fluxo imperativo quando use_triage=True.           #
        #    O grafo executa: fast_gate → triage → handler correto          #
        # ---------------------------------------------------------------- #
        if use_triage:
            try:
                from agent.graph import run_graph
                result_dict = run_graph(
                    query=user_query,
                    conversation_id=conversation_id,
                    history=hist or [],
                    agent=self
                )
                # Registra histórico
                if conversation_id and hasattr(DuqueIAAgent, "_history"):
                    prev = DuqueIAAgent._history.get(conversation_id, [])
                    ans_text = result_dict.get("answer", "")
                    DuqueIAAgent._history[conversation_id] = (
                        prev + [f"Munícipe: {user_query}", f"DUQUE IA: {ans_text}"]
                    )[-6:]
                return json.dumps(result_dict, ensure_ascii=False, indent=2)
            except Exception as graph_err:
                # Fallback seguro: se o grafo falhar catastroficamente, cai no fluxo legado
                print(f"[Graph CRITICAL] Falha no grafo principal: {graph_err}. Usando fluxo legado.", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)



        # ---------------------------------------------------------------- #
        # 0. B. Camada de Intenções de Sistema
        # ---------------------------------------------------------------- #
        system_intent = SystemIntentHandler.detect(user_query)
        if system_intent:
            intent_label = system_intent.get("intent_label")
            # Se a intenção for de saudação ou apresentação, mas já existir histórico na conversa,
            # nós forçamos a passagem pelo ConversationHandler dinâmico para evitar saudações repetidas/Olá!
            if (intent_label in ["saudacao", "apresentacao"]) and hist:
                triage_info_conv = {
                    "intent": "SAUDACAO" if intent_label == "saudacao" else "CONVERSA",
                    "confidence": system_intent["confidence"],
                    "next_agent": "CONVERSATION_HANDLER",
                    "workflow": "CHAT",
                    "clarification_type": None
                }
                handler = self.handlers["CONVERSATION_HANDLER"]
                result_dict = handler.execute(
                    query=user_query,
                    triage_info=triage_info_conv,
                    agent=self,
                    conversation_id=conversation_id,
                    start_time=start_time,
                    history=hist
                )
                if conversation_id and hasattr(DuqueIAAgent, "_history"):
                    prev = DuqueIAAgent._history.get(conversation_id, [])
                    ans_text = result_dict.get("answer", "")
                    DuqueIAAgent._history[conversation_id] = (
                        prev + [f"Munícipe: {user_query}", f"DUQUE IA: {ans_text}"]
                    )[-6:]
                return json.dumps(result_dict, ensure_ascii=False, indent=2)

            elapsed = time.time() - start_time
            return json.dumps({
                "answer": system_intent["response"],
                "sources": [],
                "confidence": system_intent["confidence"],
                "intent_detected": system_intent["intent_label"],
                "triage_info": triage_info,
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": []
                }
            }, ensure_ascii=False, indent=2)

        # ---------------------------------------------------------------- #
        # 1. Guardrails & Fallbacks (Caso a triagem não tenha sido usada ou não tenha mapeado)
        # ---------------------------------------------------------------- #
        if check_input_guardrail(user_query):
            elapsed = time.time() - start_time
            self.log_execution_metrics(user_query, 0, 0, elapsed, 0, 0, 0)
            return json.dumps({
                "answer": SECURITY_BLOCKED_MESSAGE,
                "sources": [],
                "confidence": 0.0,
                "intent_detected": "blocked",
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": []
                }
            }, ensure_ascii=False, indent=2)

        if check_privacy_guardrail(user_query):
            elapsed = time.time() - start_time
            return json.dumps({
                "answer": PRIVACY_BLOCKED_MESSAGE,
                "sources": [],
                "confidence": 0.0,
                "intent_detected": "blocked_privacy",
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(user_query)
                }
            }, ensure_ascii=False, indent=2)

        if check_competency_guardrail(user_query):
            elapsed = time.time() - start_time
            return json.dumps({
                "answer": COMPETENCY_BLOCKED_MESSAGE,
                "sources": [],
                "confidence": 0.0,
                "intent_detected": "out_of_competency",
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(user_query)
                }
            }, ensure_ascii=False, indent=2)

        if check_legal_guardrail(user_query):
            elapsed = time.time() - start_time
            return json.dumps({
                "answer": LEGAL_BLOCKED_MESSAGE,
                "sources": [],
                "confidence": 0.0,
                "intent_detected": "blocked_legal",
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(user_query)
                }
            }, ensure_ascii=False, indent=2)

        if is_query_too_vague(user_query):
            elapsed = time.time() - start_time
            return json.dumps({
                "answer": (
                    f"A pergunta '{user_query}' é muito breve para que eu possa identificar "
                    "a informação correta.\n\n"
                    "**Dica:** reformule incluindo mais detalhes. Exemplos:\n"
                    "- *Qual o endereço do CRAS do Jardim Primavera?*\n"
                    "- *Como emitir a segunda via do IPTU?*\n"
                    "- *Qual é o nome do prefeito de Duque de Caxias?*"
                ),
                "sources": [],
                "confidence": 0.0,
                "intent_detected": "general",
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(user_query)
                }
            }, ensure_ascii=False, indent=2)

        # Fallback RAG direto caso triagem não seja usada ou não defina next_agent
        rag_handler = self.handlers["RAG_HANDLER"]
        
        hist = None
        if conversation_id and hasattr(DuqueIAAgent, "_history") and conversation_id in DuqueIAAgent._history:
            hist = DuqueIAAgent._history[conversation_id]
            
        result_dict = rag_handler.execute(
            query=user_query,
            triage_info=triage_info or {},
            agent=self,
            conversation_id=conversation_id,
            start_time=start_time,
            history=hist
        )
        
        # Registra histórico completo com pergunta e resposta formatadas
        if conversation_id and hasattr(DuqueIAAgent, "_history"):
            prev = DuqueIAAgent._history.get(conversation_id, [])
            ans_text = result_dict.get("answer", "")
            DuqueIAAgent._history[conversation_id] = (
                prev + [f"Munícipe: {user_query}", f"DUQUE IA: {ans_text}"]
            )[-6:]
            
        return json.dumps(result_dict, ensure_ascii=False, indent=2)
