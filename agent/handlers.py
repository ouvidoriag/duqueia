import re
import json
import time
import sys
from agent.config import DEFAULT_DB_PATH
from agent.scoring import extract_query_keywords
from agent.fallback import build_fallback_guidance, is_query_too_vague
from agent.confidence import calibrate_confidence
from agent.retrieval import retrieve_context, retrieve_structured_service

def rewrite_query_with_history(query: str, history: list, gemini_client) -> str:
    """Usa LLM ou Regras Heurísticas Locais (offline) para reescrever queries de continuidade baseadas no histórico."""
    if not history:
        return query

    # Heurística de Resolução de Continuidade para modo Offline/Contingência
    query_lower = query.lower().strip()
    is_continuity = any(
        query_lower.startswith(prefix) for prefix in 
        ["e o ", "e a ", "qual o ", "qual a ", "onde fica a ", "onde fica o ", "qual é o ", "qual é a ", "e quanto a", "e sobre ", "e de "]
    ) or query_lower in ["e o telefone?", "e o telefone", "e o endereço?", "e o endereço", "endereço?", "telefone?", "e o email?", "email?", "horário?", "e o horário?"] or len(query_lower) < 6
    
    # Se detectada continuidade, tenta resolver o contexto pelo histórico
    resolved_heuristic = None
    if is_continuity:
        last_msg = history[-1].lower()
        
        # Encontra a entidade (Secretaria) no histórico recente
        entity = None
        for sec in ["obras", "urbanismo", "saude", "saúde", "fazenda", "educacao", "educação", "governo", "meio ambiente", "esporte", "cultura", "transporte", "defesa civil"]:
            if sec in last_msg or sec in query_lower:
                entity = sec
                break
                
        # Fallback: Mapeia termos de serviços comuns no histórico para suas respectivas secretarias
        if not entity:
            service_to_sec = {
                "buraco": "obras",
                "tapa": "obras",
                "iptu": "fazenda",
                "taxa": "fazenda",
                "vacina": "saúde",
                "consulta": "saúde",
                "médico": "saúde",
                "medico": "saúde",
                "escola": "educação",
                "creche": "educação",
                "lixo": "transportes e serviços públicos"
            }
            for term, sec in service_to_sec.items():
                if term in last_msg:
                    entity = sec
                    break
                    
        # Encontra a intenção de informação solicitada (endereço, telefone, email, etc.)
        intent_type = "endereço"
        if any(w in query_lower or w in last_msg for w in ["telefone", "fone", "contato", "chamar"]):
            intent_type = "telefone"
        elif any(w in query_lower or w in last_msg for w in ["email", "correio"]):
            intent_type = "e-mail"
        elif any(w in query_lower or w in last_msg for w in ["horario", "funcionamento", "horas"]):
            intent_type = "horário de funcionamento"
            
        if entity:
            resolved_heuristic = f"Qual é o {intent_type} da secretaria de {entity}?"
            print(f"[Heuristic Rewriter] Resolvido offline: '{query}' -> '{resolved_heuristic}'")

    # Se estiver offline ou sem chave, usa a heurística local se resolvida
    if not gemini_client or len(gemini_client.api_keys) == 0:
        return resolved_heuristic if resolved_heuristic else query
        
    history_context = "\n".join([f"Mensagem anterior: {msg}" for msg in history[-3:]])
    
    prompt = (
        "Dada uma conversa recente e uma pergunta atual que pode conter pronomes de continuidade, "
        "referências implícitas ou perguntas curtas de acompanhamento (ex: 'e o de obras?', 'qual o endereço?', 'e o telefone?'), "
        "sua tarefa é reescrever a pergunta atual para torná-la uma pergunta de busca RAG totalmente autossuficiente e completa, "
        "preservando a intenção original.\n\n"
        "Regras:\n"
        "1. Se a pergunta atual já for completa e não depender de contexto anterior, retorne-a idêntica.\n"
        "2. Se a pergunta atual for vaga ou contiver pronomes/continuidade ('e o de...', 'qual o endereço de...', 'e o telefone dele?'), "
        "use o histórico para resolver essas referências. Exemplo: se antes perguntou 'endereço do urbanismo' e agora pergunta 'e o de obras?', "
        "reescreva para 'qual o endereço da secretaria de obras?'.\n"
        "3. Retorne APENAS o texto da pergunta reescrita de forma direta, sem explicações, prefixos ou aspas.\n\n"
        f"Histórico recente de mensagens:\n{history_context}\n\n"
        f"Pergunta atual: \"{query}\"\n\n"
        "Pergunta reescrita autossuficiente:"
    )
    
    try:
        rewritten = gemini_client.generate_response(prompt, model="gemini-3.1-flash-lite").strip()
        rewritten = re.sub(r'^["\']|["\']$', '', rewritten).strip()
        return rewritten
    except Exception as e:
        print(f"[Query Rewriter Warning] Falha ao reescrever query (usando heurística): {e}", file=sys.stderr)
        return resolved_heuristic if resolved_heuristic else query

class BaseHandler:
    """Classe base para todos os Handlers de intenção."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        raise NotImplementedError


class SecurityHandler(BaseHandler):
    """Trata intenções de segurança e LGPD/Bloqueios locais."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        intent = triage_info.get("intent")
        elapsed = time.time() - start_time
        
        if intent == "LGPD":
            ans = "Por motivos de segurança e privacidade (LGPD), não tenho autorização para fornecer dados pessoais, CPFs ou andamento de solicitações de terceiros. Por favor, consulte o andamento de suas próprias solicitações nos canais oficiais identificados."
            intent_detected = "blocked_privacy"
        elif intent == "ESCALONAMENTO_HUMANO":
            ans = "Sua solicitação envolve assuntos sensíveis ou denúncias que requerem atenção direta e sigilosa. Este canal informativo não processa esse tipo de demanda automaticamente. Por favor, registre formalmente sua manifestação na **Ouvidoria Geral de Duque de Caxias**: telefone **(21) 2652-3835**, e-mail **ouvidoria@duquedecaxias.rj.gov.br** ou presencialmente na **Alameda Esmeralda, 206 - Jardim Primavera**."
            intent_detected = "human_escalation"
        elif intent == "FORA_COMPETENCIA":
            ans = "Esta pergunta não está inserida nos temas que são de responsabilidade da Prefeitura de Duque de Caxias. O metrô, por exemplo, é um transporte de âmbito estadual, e não compete à prefeitura municipal."
            intent_detected = "out_of_competency"
        elif intent == "JURIDICO":
            ans = "Como assistente virtual informativo, não realizo pareceres jurídicos, defesas, recursos ou interpretações de leis, nem formulo argumentos contra a administração pública. Para suporte legal, favor contatar a Procuradoria Geral do Município ou os órgãos competentes."
            intent_detected = "blocked_legal"
        else:
            ans = "Requisição bloqueada por motivos de segurança (Input Guardrail)."
            intent_detected = "blocked"

        return {
            "answer": ans,
            "sources": [],
            "confidence": 0.0,
            "intent_detected": intent_detected,
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }

class ConversationHandler(BaseHandler):
    """Trata cumprimentos e interações de bate-papo informal."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        intent = triage_info.get("intent")
        elapsed = time.time() - start_time
        
        # Resposta padrão fallback
        if intent == "SAUDACAO":
            ans = ("Olá! Sou o **DUQUE IA**, assistente virtual da Prefeitura de Duque de Caxias.\n\n"
                   "Como posso ajudar você hoje? Pode perguntar sobre secretarias, serviços municipais, "
                   "endereços, ouvidoria ou qualquer outro assunto relacionado à prefeitura.")
            intent_detected = "saudacao"
        else:
            ans = "Olá! Sou o Duque IA, assistente virtual de Duque de Caxias. Estou aqui para tirar dúvidas sobre secretarias, IPTU, Ouvidoria e outros serviços da nossa cidade. Como posso ajudar com Duque de Caxias hoje?"
            intent_detected = "conversa_casual"

        if agent.using_real:
            try:
                if intent == "SAUDACAO":
                    sys_instruct = (
                        "Você é o Duque IA, assistente virtual da Prefeitura de Duque de Caxias.\n"
                        "O munícipe enviou uma saudação. Responda de forma calorosa e descontraída, no mesmo tom dele, "
                        "e pergunte em que pode ajudar. Seja breve: máximo 2 frases."
                    )
                else:
                    sys_instruct = (
                        "Você é o Duque IA, assistente virtual da Prefeitura de Duque de Caxias.\n"
                        "O cidadão fez um bate-papo informal. Responda de forma simpática e curta (máximo 3 frases), "
                        "lembre-o com leveza que sua especialidade é Duque de Caxias (serviços, secretarias, endereços)."
                    )
                ans = agent.gemini_client.generate_response(query, system_instruction=sys_instruct, model="gemini-3.1-flash-lite").strip()
            except Exception:
                pass
        
        return {
            "answer": ans,
            "sources": [],
            "confidence": triage_info.get("confidence", 0.95),
            "intent_detected": intent_detected,
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }

class CollectorHandler(BaseHandler):
    """Trata fluxos de Ouvidoria (reclamação, denúncia, sugestão, elogio) e triagem incremental."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        elapsed = time.time() - start_time
        tipo = triage_info.get("tipo_manifestacao", "geral")
        
        if triage_info.get("needs_clarification"):
            answer = agent.gerar_esclarecimento_contextual(query, triage_info)
            return {
                "answer": answer,
                "sources": [],
                "confidence": triage_info.get("confidence", 0.8),
                "intent_detected": f"ouvidoria_{tipo}",
                "triage_info": triage_info,
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(query)
                }
            }
            
        _LABELS = {
            "elogio":     "elogio",
            "denuncia":   "denúncia",
            "sugestao":   "sugestão",
            "reclamacao": "reclamação",
            "geral":      "manifestação",
        }
        
        # Se a query contém "falar com o prefeito" ou similar, e o tipo veio como "reclamacao" padrão mas a palavra "reclamacao"
        # não foi dita pelo cidadão, suavizamos para usar "manifestação".
        query_lower = query.lower()
        if "prefeito" in query_lower and tipo == "reclamacao" and "reclam" not in query_lower and "denunc" not in query_lower:
            label = "manifestação"
        else:
            label = _LABELS.get(tipo, "manifestação")
        
        # Usando LLM se disponível para gerar uma resposta acolhedora e natural baseada no serviço encontrado

        if agent.using_real:
            service_context = ""
            try:
                # Tenta buscar estruturado primeiro sem histórico para evitar falso positivo de endereços
                keywords = extract_query_keywords(query)
                struct_res = retrieve_structured_service(agent.db_path, query, keywords, agent.using_real)
                if history and not struct_res:
                    search_query = f"{query} {' '.join(history)}"
                    keywords = extract_query_keywords(search_query)
                    struct_res = retrieve_structured_service(agent.db_path, search_query, keywords, agent.using_real)
                if struct_res:
                    best_struct = struct_res[0]
                    title_servico = best_struct.get("title", "")
                    content_str = best_struct.get("content", "")
                    sec_match = re.search(r"Secretaria Responsável: ([^\n]+)", content_str)
                    sec_nome = sec_match.group(1).strip() if sec_match else "Secretaria responsável"
                    service_context = f"Serviço Oficial Identificado: \"{title_servico}\" da {sec_nome}.\nDetalhes adicionais: {content_str[:500]}"
            except Exception:
                pass

            system_instruction = (
                "Você é o DUQUE IA, assistente virtual oficial de Duque de Caxias — RJ.\n"
                "O cidadão deseja abrir uma manifestação (reclamação, denúncia, elogio ou sugestão).\n"
                "Sua missão é validar o sentimento dele com simpatia e orientá-lo de forma direta (em até 4 frases) "
                "de como preencher essa solicitação no aplicativo **Colab** ou pelo site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/).\n\n"
                "INSTRUÇÕES DE PREENCHIMENTO:\n"
                "1. Com base na reclamação/mensagem do munícipe, diga a ele claramente qual **Tema** e **Assunto** selecionar dentro do Colab. Exemplo:\n"
                "   - Se for buraco de asfalto/drenagem: Tema **Obras**.\n"
                "   - Se for capina, roçagem, lixo ou entulho: Tema **Limpeza Urbana**.\n"
                "   - Se for lâmpada apagada no poste: Tema **Transportes, Serviços Públicos e Troca de Lâmpadas**.\n"
                "   CRÍTICO: Você deve sugerir APENAS nomes de temas e assuntos reais cadastrados no sistema municipal do Colab. Nunca invente ou crie nomes de temas/assuntos (por exemplo, sugira 'Conduta irregular de funcionário' ou 'Funcionário', nunca invente 'Denúncia contra Servidor').\n"
                "2. Informe os canais da Ouvidoria Geral como alternativa: telefone **(21) 2652-3835** e e-mail **ouvidoria@duquedecaxias.rj.gov.br**.\n"
                "3. Dica rápida: oriente-o a ter em mãos a foto e o endereço correto para o registro no Colab ([duquedecaxias.colab.re](https://duquedecaxias.colab.re/)).\n"
                "4. Mantenha a resposta concisa, calorosa, objetiva e sem saudações repetidas se o diálogo já estiver em andamento."
            )

            prompt = (
                f"Contexto do serviço encontrado (USE APENAS SE FOR DIRETAMENTE RELACIONADO AO ASSUNTO DO USUÁRIO):\n{service_context}\n\n"
                f"Tipo da manifestação: {label}\n"
                f"Mensagem atual do cidadão: \"{query}\"\n\n"
                f"Gere a resposta humana de orientação:"
            )

            try:
                answer = agent.gemini_client.generate_response(prompt, system_instruction=system_instruction, model="gemini-3.1-flash-lite").strip()
            except Exception:
                # Fallback offline em caso de erro da API
                answer = (
                    f"Entendi perfeitamente o seu problema. Para registrar essa sua **{label}**, o caminho oficial é através da nossa Ouvidoria Geral de Duque de Caxias. "
                    f"Você pode registrar diretamente pelo aplicativo **Colab**, no site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/), ligando para **(21) 2652-3835** ou enviando um e-mail para **ouvidoria@duquedecaxias.rj.gov.br**.\n\n"
                    f"**Dica de amigo:** Quando for registrar no Colab, lembre-se de colocar o endereço bem certinho, com ponto de referência e, se tiver, anexar fotos ou vídeos do local. Isso agiliza muito o trabalho da secretaria para resolver o problema!"
                )
        else:
            sugerido_txt = ""
            try:
                keywords = extract_query_keywords(query)
                struct_res = retrieve_structured_service(agent.db_path, query, keywords, agent.using_real)
                if struct_res:
                    best_struct = struct_res[0]
                    title_servico = best_struct.get("title", "")
                    content_str = best_struct.get("content", "")
                    sec_match = re.search(r"Secretaria Responsável: ([^\n]+)", content_str)
                    sec_nome = sec_match.group(1).strip() if sec_match else "Secretaria responsável pelo setor"
                    
                    sugerido_txt = (
                        f"Identifiquei em nossa base que sua manifestação se enquadra no serviço oficial **\"{title_servico}\"** "
                        f"da **{sec_nome}**.\n\n"
                    )
            except Exception as e:
                print(f"[Ouvidoria DB Suggest Warning] Erro ao sugerir secretaria/servico: {e}", file=sys.stderr)

            answer = (
                f"{sugerido_txt}"
                f"Para dar andamento à sua **{label}**, você pode registrá-la diretamente nos canais oficiais da nossa **Ouvidoria Geral de Duque de Caxias**:\n\n"
                f"• Telefone: **(21) 2652-3835**\n"
                f"• E-mail: **ouvidoria@duquedecaxias.rj.gov.br**\n"
                f"• Online: aplicativo **Colab** ou site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/).\n\n"
                f"**Dica de amigo para agilizar o seu atendimento:**\n"
                f"Ao registrar sua manifestação no Colab, procure incluir o **endereço completo do fato** (com ponto de referência), uma **descrição bem detalhada** do que está acontecendo e, se possível, anexe **fotos ou vídeos** bem nítidos do local. Isso nos ajuda a encaminhar o problema muito mais rápido para a secretaria responsável!"
            )

        return {
            "answer": answer,
            "sources": [],
            "confidence": triage_info.get("confidence", 0.9),
            "intent_detected": f"ouvidoria_{tipo}_redirect",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }

class AmbiguityHandler(BaseHandler):
    """Trata conflitos de ambiguidade (luz/lâmpada/barulho) de forma inteligente."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        intent = triage_info.get("intent")
        elapsed = time.time() - start_time
        
        # 1. Se o modelo real (Gemini) estiver disponível, gera resposta dinâmica e interpretativa
        if agent.using_real:
            history_context = ""
            if history:
                history_context = "\n".join([f"Mensagem anterior: {msg}" for msg in history[-4:]])
                
            system_instruction = (
                "Você é o DUQUE IA, assistente virtual oficial da Prefeitura de Duque de Caxias — RJ.\n"
                "O cidadão está em uma conversa sobre um assunto ambíguo (falta de luz, troca de lâmpada ou barulho) e precisamos esclarecer ou confirmar a intenção dele.\n"
                "REGRAS DE CONVERSA:\n"
                "1. Se a última mensagem do cidadão (ou o histórico recente) permitir inferir com razoável certeza qual é a intenção dele, confirme essa escolha de forma natural e dê as orientações de imediato (sem fazer a pergunta de escolha de novo). Exemplo: se ele diz 'lâmpada' ou 'lâmpada queimada' após perguntarmos se era na casa ou no poste, infira que é iluminação pública. Responda: 'Entendi! Você está falando de uma lâmpada de um poste de iluminação pública, certo? Se for isso, o serviço é realizado pela Prefeitura...'\n"
                "2. Se ainda for totalmente ambíguo (sem nenhuma pista no histórico), peça esclarecimento de forma amigável, listando as opções de forma clara (ex: falta de luz em casa = Light; poste apagado na rua = Prefeitura).\n"
                "3. Ao indicar a abertura de chamados para iluminação pública ou manutenção urbana, instrua o cidadão a registrar no aplicativo Colab (duquedecaxias.colab.re) e peça para ele informar:\n"
                "   - Endereço completo\n"
                "   - Ponto de referência\n"
                "   - Número aproximado do poste (se houver)\n"
                "   - Anexar fotos do local (opcional)\n"
                "4. Se for barulho de residência/vizinho, direcione estritamente para a Polícia Militar (190). Se for evento/rua, direcione para Ordem Urbana via Colab.\n"
                "5. Formate informações importantes em **negrito** (números, telefones, links, temas).\n"
                "6. NUNCA use saudações repetitivas (como 'Olá', 'Oi') se o diálogo já estiver em andamento. Vá direto ao ponto de forma calorosa.\n"
                "7. Mantenha a resposta curta, objetiva, prestativa e calorosa. Máximo 4 frases."
            )
            
            prompt = (
                f"Histórico recente de mensagens:\n{history_context}\n\n"
                f"Mensagem atual do cidadão: \"{query}\"\n"
                f"Intenção detectada (triagem): {intent}\n"
                f"Necessita esclarecimento (needs_clarification): {triage_info.get('needs_clarification')}\n\n"
                f"Gere a resposta humana de orientação ou esclarecimento:"
            )
            
            try:
                answer = agent.gemini_client.generate_response(
                    prompt,
                    system_instruction=system_instruction,
                    model="gemini-3.1-flash-lite",
                    temperature=0.2,
                    max_output_tokens=250
                ).strip()
                return {
                    "answer": answer,
                    "sources": [],
                    "confidence": triage_info.get("confidence", 0.9),
                    "intent_detected": "ambiguity_resolved_dynamic",
                    "triage_info": triage_info,
                    "metrics": {
                        "retrieval_time_ms": 0,
                        "llm_time_ms": round((time.time() - start_time) * 1000, 2),
                        "total_time_ms": round((time.time() - start_time) * 1000, 2),
                        "tokens_used": len(query) // 4 + len(prompt) // 4,
                        "keywords": extract_query_keywords(query)
                    }
                }
            except Exception as e:
                print(f"[AmbiguityHandler Warning] Falha na geração dinâmica, usando fallback offline: {e}", file=sys.stderr)

        # 2. Fallback offline tradicional (caso esteja offline)
        if not triage_info.get("needs_clarification"):
            q_lower = query.lower()
            if any(w in q_lower for w in ["poste", "rua", "pública", "publica", "fora", "calçada", "calcada", "dois", "3 postes", "lampada apagada"]):
                has_address = False
                full_context = query.lower()
                if history:
                    full_context += " " + " ".join(history).lower()
                    
                address_indicators = ["rua ", "av. ", "avenida ", "travessa ", "alameda ", "estrada ", "rodovia ", "bairro ", "no jardim", "em xerém", "xerem", "primavera", "saracuruna", "25 de agosto"]
                if any(ind in full_context for ind in address_indicators):
                    has_address = True
                    
                if has_address:
                    answer = (
                        "Entendi perfeitamente! Como se trata de um problema de **iluminação pública** (lâmpada apagada ou poste quebrado na rua) "
                        "e o local já foi identificado, você já pode registrar essa solicitação pelo aplicativo **Colab** ou pelo site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/), selecionando o assunto **Iluminação Pública**.\n\n"
                        "A solicitação vai direto para a **Subsecretaria de Iluminação Pública** para agendarem o reparo.\n"
                        "**Uma dica:** Se o poste tiver algum número de identificação marcado nele, informe no aplicativo e envie uma foto do local! Isso ajuda bastante a equipe a localizar o poste certo."
                    )
                else:
                    answer = (
                        "Entendi! Trata-se de um problema de **iluminação pública** (poste apagado ou lâmpada com defeito na rua).\n\n"
                        "Para que eu possa te orientar bem e ajudar a registrar o pedido no setor correto, poderia me dizer **qual é o endereço completo ou ponto de referência desse poste com problema?**"
                    )
                
                if hasattr(agent, "_history"):
                    prev = agent._history.get(conversation_id, [])
                    agent._history[conversation_id] = (prev + [query])[-2:]
                    
                return {
                    "answer": answer,
                    "sources": [],
                    "confidence": triage_info.get("confidence", 0.9),
                    "intent_detected": "RAG_GERAL",
                    "triage_info": triage_info,
                    "metrics": {
                        "retrieval_time_ms": 0,
                        "llm_time_ms": 0,
                        "total_time_ms": round(elapsed * 1000, 2),
                        "tokens_used": 0,
                        "keywords": extract_query_keywords(query)
                    }
                }
        
        if intent == "AMBIGUO_LUZ":
            answer = (
                "Você poderia me esclarecer se a sua dúvida é sobre **falta de energia elétrica dentro da sua residência** "
                "ou se é sobre **iluminação pública (como um poste apagado ou lâmpada com problema na rua)**?\n\n"
                "• Se for **falta de luz na sua casa**, a concessionária responsável é a **Light** (você pode falar com eles pelo WhatsApp no número **(21) 99981-1920** ou pelo telefone **0800-282-0120**).\n"
                "• Se for **poste apagado ou problema na rua**, o serviço é da Prefeitura! Você pode pedir a manutenção direto pelo aplicativo **Colab**, no site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/) ou ligando para o telefone **(21) 2961-9000** (Subsecretaria de Iluminação Pública)."
            )
        elif intent == "AMBIGUO_BARULHO":
            answer = (
                "Você poderia me esclarecer se o som alto vem de uma **residência particular (como a casa de um vizinho, apartamento ou festa privada)** "
                "ou se é de um **evento realizado em espaço público (como um show na rua, praça pública ou festa aberta à população)**?\n\n"
                "• Se for barulho de **vizinho ou residência particular**, a competência de atendimento é da **Polícia Militar (ligue para 190)**.\n"
                "• Se for um **evento ou show em espaço público/rua**, a reclamação deve ser registrada para a **Ordem Urbana** da Prefeitura pelo aplicativo **Colab** ou site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/)."
            )
        else:
            answer = (
                "Para eu te orientar direitinho, a troca de lâmpada que você precisa é **dentro da sua casa (área particular)** "
                "ou em um **poste de iluminação pública no meio da rua**?\n\n"
                "• Se for em um **poste da rua**, a Prefeitura faz o serviço! Você pode solicitar a troca registrando o pedido no aplicativo **Colab**, no site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/) ou falando com a Subsecretaria de Iluminação Pública pelo telefone **(21) 2961-9000**.\n"
                "• Se for **dentro de casa**, a manutenção interna e particular fica sob a responsabilidade do próprio morador, tudo bem?"
            )
            
        return {
            "answer": answer,
            "sources": [],
            "confidence": triage_info.get("confidence", 0.0),
            "intent_detected": "ambiguity_resolved",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }

class PrivateResponsibilityHandler(BaseHandler):
    """Trata o escopo privado de residências/condomínios."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        elapsed = time.time() - start_time
        return {
            "answer": "Olha, a manutenção elétrica interna, como trocar lâmpadas de dentro de casa, do comércio ou em áreas internas de condomínios fechados, é de **responsabilidade particular** do próprio morador ou proprietário. Por isso, a Prefeitura não consegue realizar esse serviço específico.",
            "sources": [],
            "confidence": triage_info.get("confidence", 0.0),
            "intent_detected": "private_responsibility",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }

class ProgramacaoHandler(BaseHandler):
    """Trata fora-de-escopo de código/programação."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        elapsed = time.time() - start_time
        return {
            "answer": "Como o assistente virtual oficial de Duque de Caxias, sou especializado em serviços públicos do município, endereços de secretarias, contatos e carta de serviços. Não realizo desenvolvimento de software ou geração de código de programação.",
            "sources": [],
            "confidence": triage_info.get("confidence", 1.0),
            "intent_detected": "programacao_block",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }


class RagHandler(BaseHandler):
    """Handler principal para consultas informativas via RAG."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        from agent.router import QueryAnalyzer
        
        # Reescreve a query com o histórico se aplicável para resolver pronomes e continuity queries
        effective_query = query
        if history:
            effective_query = rewrite_query_with_history(query, history, agent.gemini_client)
        
        # 1. Análise da Query (Roteamento/Informações adicionais)
        intent_info = QueryAnalyzer.analyze(effective_query, agent.gemini_client)
        
        # 2. Busca RAG Híbrida
        retrieval_start = time.time()
        results = retrieve_context(
            effective_query, agent.db_path, agent.using_real, agent.similarity_threshold,
            agent.gemini_client, agent.reranker, top_k=3, intent_info=intent_info
        )
        
        # Se a busca falhar com o limite padrão, tenta recuperar buscando com a query concatenada em último caso
        if history and (not results or results[0].get("similarity", 0.0) < 0.65) and effective_query == query:
            search_query = f"{query} {' '.join(history[-2:])}"
            history_results = retrieve_context(
                search_query, agent.db_path, agent.using_real, agent.similarity_threshold,
                agent.gemini_client, agent.reranker, top_k=3, intent_info=intent_info
            )
            if history_results and (not results or history_results[0].get("similarity", 0.0) > results[0].get("similarity", 0.0)):
                results = history_results
                effective_query = search_query
                
        retrieval_time = time.time() - retrieval_start
        
        # 3. Guardrail de Retrieval
        query_lower = effective_query.lower()
        essential_keywords = ["prefeito", "secretaria", "ouvidoria", "fundec", "colab", "telefone"]
        is_essential = any(k in query_lower for k in essential_keywords)
        effective_threshold = 0.25 if is_essential else agent.similarity_threshold
        
        if not results or results[0]["similarity"] < effective_threshold:
            elapsed = time.time() - start_time
            agent.log_execution_metrics(query, retrieval_time, 0, elapsed, 0, 0, 0)
            return {
                "answer": build_fallback_guidance(query),
                "sources": [],
                "confidence": 0.0,
                "intent_detected": intent_info["intent"].value,
                "triage_info": triage_info,
                "metrics": {
                    "retrieval_time_ms": round(retrieval_time * 1000, 2),
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(query)
                }
            }
            
        relevant_results = [r for r in results if r["similarity"] >= effective_threshold]
        
        # 5. Calibração da Confiança (Antecipada)
        base_score = relevant_results[0]["similarity"]
        confidence = calibrate_confidence(base_score, query, relevant_results)
        
        # Se a confiança for baixa (< 0.60) e estiver online, gera uma pergunta de clarificação em vez de responder incorretamente
        if base_score < 0.60 and agent.using_real:
            llm_start = time.time()
            system_instruction = (
                "Você é o DUQUE IA, assistente virtual oficial da Prefeitura de Duque de Caxias — RJ.\n"
                "A busca obteve baixa confiança e o assunto ou o local exato pode não estar claro.\n"
                "Sua missão é gerar uma pergunta de confirmação/esclarecimento muito simpática, natural e humana.\n"
                "Você DEVE citar expressamente o nome do resultado/órgão/local mais provável encontrado no contexto da base de dados e perguntar se o cidadão está falando dele ou de outro assunto/local.\n"
                "Exemplo: se o cidadão pergunta 'como ir no adão pereira' e o resultado mais provável é 'Hospital Municipal Dr. Adão Pereira Nunes', pergunte: 'Só para confirmar: você está falando do Adão Pereira, o Hospital Municipal Dr. Adão Pereira Nunes, ou de outro local?'\n"
                "Seja extremamente curto, educado e caloroso. Máximo 2 frases."
            )
            prompt = (
                f"Mensagem do cidadão: \"{query}\"\n"
                f"Melhor resultado da base (baixa confiança): \"{relevant_results[0].get('title')}\" - \"{relevant_results[0].get('content')[:250]}\"\n\n"
                f"Gere a pergunta de clarificação/confirmação:"
            )
            try:
                clarification_query = agent.gemini_client.generate_response(
                    prompt,
                    system_instruction=system_instruction,
                    model="gemini-3.1-flash-lite",
                    temperature=0.2,
                    max_output_tokens=150
                ).strip()
                llm_time = time.time() - llm_start
                total_time = time.time() - start_time
                agent.log_execution_metrics(query, retrieval_time, llm_time, total_time, base_score, len(query)//4 + len(prompt)//4, 0.0)
                return {
                    "answer": clarification_query,
                    "sources": [],
                    "confidence": confidence,
                    "retrieved_chunks": [],
                    "intent_detected": "low_confidence_clarification",
                    "triage_info": triage_info,
                    "metrics": {
                        "retrieval_time_ms": round(retrieval_time * 1000, 2),
                        "llm_time_ms": round(llm_time * 1000, 2),
                        "total_time_ms": round(total_time * 1000, 2),
                        "tokens_used": len(query) // 4 + len(prompt) // 4,
                        "keywords": extract_query_keywords(query)
                    }
                }
            except Exception as e:
                print(f"[Low Confidence Clarification Warning] Falha na chamada da LLM: {e}", file=sys.stderr)

        sources_list = list(set(r["source"] for r in relevant_results))
        
        # 4. Geração de Resposta (LLM ou Fallback Offline)
        llm_start = time.time()
        structured_parts = []
        complementary_parts = []
        
        if agent.using_real:
            for r in relevant_results:
                source_upper = r['source'].upper()
                content_block = f"[{r['title']}]:\n{r['content']}"
                if "SECRETARIAS" in source_upper or "VW_IA_SERVICOS" in source_upper:
                    structured_parts.append(content_block)
                else:
                    complementary_parts.append(content_block)
            
            context_blocks = []
            if structured_parts:
                context_blocks.append("=== INFORMAÇÕES OFICIAIS ESTRUTURADAS (PRIORIDADE MÁXIMA) ===\n" + "\n\n".join(structured_parts))
            if complementary_parts:
                context_blocks.append("=== CONTEXTO COMPLEMENTAR DE APOIO ===\n" + "\n\n".join(complementary_parts))
                
            context_str = "\n\n".join(context_blocks)
            agent._last_context = context_str
            is_list_result = any(r.get("is_list_result") for r in relevant_results)
            
            system_instruction = (
                "Você é o DUQUE IA, assistente virtual oficial da Prefeitura de Duque de Caxias — RJ.\n"
                "Sua personalidade deve ser extremamente simpática, calorosa, prestativa e humana (aumente a empatia e use palavras acolhedoras). Responda com um sorriso virtual e gentileza genuína.\n"
                "Apesar de muito caloroso, seja objetivo e preciso. Prefira respostas de 2 a 4 frases — suficientes para ser muito útil e acolhedor, sem exageros.\n"
                "\n"
                "REGRA DE FONTES (CRÍTICO):\n"
                "- 'INFORMAÇÕES OFICIAIS ESTRUTURADAS' têm precedência absoluta sobre qualquer outro contexto.\n"
                "- Para endereço, telefone, e-mail e horário: use EXCLUSIVAMENTE os dados estruturados.\n"
                "- O 'CONTEXTO COMPLEMENTAR' serve apenas para enriquecer com descrições, nunca para substituir dados oficiais.\n"
                "\n"
                "REGRA CRÍTICA DE COMPETÊNCIA — PERTURBAÇÃO DO SOSSEGO / BARULHO:\n"
                "- Se o cidadão reclamar de barulho, som alto, festa ou algazarra vindo de um **vizinho, residência particular, apartamento ou casa ao lado**: a competência é da **POLÍCIA MILITAR** — oriente-o a ligar para o **190**. NÃO direcione ao Colab, Ordem Urbana ou Ouvidoria para este caso.\n"
                "- Se o cidadão reclamar de barulho vindo de **evento em espaço público (rua, praça, evento aberto, baile funk)**: direcione à **Ordem Urbana** pelo **Colab** ([duquedecaxias.colab.re](https://duquedecaxias.colab.re/)), tema **Veículo Abandonado, Ordem Pública (Bares, Eventos e Feiras)**.\n"
                "\n"
                "DIRETRIZES CONVERSACIONAIS:\n"
                "1. Use **negrito** para telefones, endereços e horários.\n"
                "2. Fale com autoridade, clareza e acolhimento. Jamais use 'pelo que sei', 'não tenho certeza' ou termos de hesitação.\n"
                "3. Se o cidadão deseja pedir um serviço de zeladoria urbana pela primeira vez (como tapar buraco, retirar entulho, limpar bueiro, capina ou trocar lâmpada pública), oriente-o claramente e com muita simpatia a abrir uma **Solicitação de Serviço** no Colab ([duquedecaxias.colab.re](https://duquedecaxias.colab.re/)) e não reclamação na Ouvidoria, apontando a categoria correta: **Obras** (asfalto/drenagem), **Limpeza Urbana** (lixo/entulho/mato) ou **Transportes** (iluminação pública). Para agilizar o atendimento de zeladoria, lembre o munícipe de informar: endereço completo do fato com ponto de referência, número aproximado do poste (se aplicável) e se puder anexar uma foto no app Colab.\n"
                "4. Se o cidadão solicitar genericamente os serviços atendidos pela zeladoria urbana ou serviços urbanos, liste de forma clara e organizada os seguintes itens: **Tapa-buraco**, **Limpeza de ruas**, **Capina**, **Roçada**, **Retirada de entulho**, **Coleta de galhos**, **Iluminação pública**, **Desobstrução de bueiros**, **Limpeza de rios e canais**, **Manutenção de praças**.\n"
                "5. Se o cidadão solicitar o **endereço** de uma secretaria, órgão ou equipamento público (ex: Guarda Municipal, CRAS, etc.), forneça a resposta principal em **negrito** e ofereça proativamente fornecer outros detalhes se ele desejar, como: telefone, horário de funcionamento, como chegar ou serviços oferecidos no local.\n"
                "6. NÃO repita saudações se o diálogo já está em andamento. Comece a resposta de forma direta e natural.\n"
                "7. NÃO use 'com base nos documentos', 'segundo o contexto' ou 'de acordo com a base de dados'.\n"
                "8. Ao indicar temas ou assuntos do Colab, utilize sempre os nomes exatos e reais constantes nas fontes de dados (ex: 'Conduta irregular de funcionário' ou 'Funcionário'), sem inventar ou parafrasear os botões do formulário."
            )
            
            prompt = (
                f"Contexto oficial (use SOMENTE estas informações para responder):\n"
                f"{context_str}\n\n"
                f"Pergunta do cidadão:\n{effective_query}\n\n"
                f"Resposta simpática, calorosa, objetiva e precisa:"
            )
            
            from agent.agent import DuqueIAAgent
            session_model = DuqueIAAgent._model_sessions.get(conversation_id) if conversation_id and hasattr(DuqueIAAgent, "_model_sessions") else None
            
            if not hasattr(DuqueIAAgent, "_interaction_map"):
                DuqueIAAgent._interaction_map = {}
            gemini_interaction_id = DuqueIAAgent._interaction_map.get(conversation_id) if conversation_id else None
            
            try:
                answer, new_conv_id, working_model = agent.gemini_client.generate_interaction(
                    prompt,
                    system_instruction=system_instruction,
                    model=session_model,
                    previous_interaction_id=gemini_interaction_id,
                    temperature=0.15,
                    max_output_tokens=350
                )
                if new_conv_id and conversation_id:
                    DuqueIAAgent._interaction_map[conversation_id] = new_conv_id
                    if hasattr(DuqueIAAgent, "_model_sessions") and working_model:
                        DuqueIAAgent._model_sessions[conversation_id] = working_model
            except Exception as e:
                print(f"[Gemini Interaction Warning] Falha na chamada da LLM (usando fallback offline): {e}", file=sys.stderr)
                best_match = relevant_results[0]
                clean_content = best_match["content"].strip()
                if "FONTE OFICIAL ESTRUTURADA" in clean_content:
                    answer = (
                        f"**{best_match['title']}**\n\n"
                        + clean_content +
                        f"\n\n*Fonte: {best_match['source']} (Dados Oficiais)*"
                    )
                else:
                    sentences = [s.strip() for s in clean_content.split("\n") if s.strip()]
                    answer = (
                        f"**{best_match['title']}**\n\n"
                        + "\n".join(f"- {s}" for s in sentences[:5]) +
                        f"\n\n*Fonte: {best_match['source']} (Fallback Offline)*"
                    )
        else:
            best_match = relevant_results[0]
            clean_content = best_match["content"].strip()
            if "FONTE OFICIAL ESTRUTURADA" in clean_content:
                answer = (
                    f"**{best_match['title']}**\n\n"
                    + clean_content +
                    f"\n\n*Fonte: {best_match['source']} (Dados Oficiais)*"
                )
            else:
                sentences = [s.strip() for s in clean_content.split("\n") if s.strip()]
                answer = (
                    f"**{best_match['title']}**\n\n"
                    + "\n".join(f"- {s}" for s in sentences[:5]) +
                    f"\n\n*Fonte: {best_match['source']}*"
                )
            
        # Se houver um acerto em Carta de Serviços estruturada (vw_ia_servicos) no Top-1 ou com alta similaridade,
        # anexa os detalhes estruturados de passo a passo e documentos logo abaixo da resposta gerada.
        extra_info = ""
        # Só anexa passo a passo se o chunk for o primeiro resultado (mais relevante) ou tiver similaridade muito próxima
        if relevant_results:
            top_match = relevant_results[0]
            if "vw_ia_servicos" in top_match.get("source", "").lower():
                content = top_match.get("content", "")
                
                # Extrai seção de Documentos Necessários
                doc_match = re.search(r"Documentos Necessários:\n(.*?)(?=\n\n|\n[A-Z]|$)", content, re.DOTALL)
                docs_text = doc_match.group(1).strip() if doc_match else ""
                
                # Extrai seção de Passo a Passo
                steps_match = re.search(r"Passo a Passo de Acesso:\n(.*?)(?=\n\n|\n[A-Z]|$)", content, re.DOTALL)
                steps_text = steps_match.group(1).strip() if steps_match else ""
                
                if docs_text or steps_text:
                    extra_info += f"\n\n**Como proceder para solicitar o serviço \"{top_match.get('title')}\":**"
                    if docs_text:
                        # Limpa os passos redundantes da lista de documentos se houver
                        clean_docs = "\n".join(line.strip() for line in docs_text.split("\n") if line.strip() and "Abertura de processo" not in line)
                        if clean_docs:
                            extra_info += f"\n\n📋 **Documentos Necessários:**\n{clean_docs}"
                    if steps_text:
                        # Reconstrói os passos de forma amigável removendo quebras vazias ou truncadas
                        clean_steps = []
                        for line in steps_text.split("\n"):
                            line_strip = line.strip()
                            if line_strip:
                                # Junta linhas que foram divididas pela quebra de palavra errada da planilha
                                if clean_steps and not line_strip.startswith("Passo"):
                                    clean_steps[-1] = clean_steps[-1] + " " + line_strip
                                else:
                                    clean_steps.append(line_strip)
                        
                        extra_info += "\n\n👣 **Passo a Passo:**\n" + "\n".join(clean_steps)

        if extra_info:
            answer = answer.strip() + extra_info


        llm_time = time.time() - llm_start
        total_time = time.time() - start_time
        
        # 5. Calibração da Confiança
        base_score = relevant_results[0]["similarity"]
        confidence = calibrate_confidence(base_score, query, relevant_results)
        
        # 6. Métricas
        tokens_usados = len(query) // 4 + sum(len(r["content"]) for r in relevant_results) // 4
        embedding_cost = (tokens_usados / 1000) * 0.00002 if agent.using_real else 0.0
        
        # Detecta se houve acerto em fonte estruturada
        structured_hit = any("SECRETARIAS" in r["source"].upper() or "VW_IA_SERVICOS" in r["source"].upper() for r in relevant_results)
        
        agent.log_execution_metrics(
            user_query=query,
            retrieval_time=retrieval_time,
            llm_time=llm_time,
            total_time=total_time,
            similarity_score=base_score,
            tokens_usados=tokens_usados,
            embedding_cost=embedding_cost,
            rewritten_query=effective_query,
            structured_hit=structured_hit,
            vector_count=len(results),
            selected_sources=sources_list
        )

        
        chunks_info = []
        for r in relevant_results:
            chunks_info.append({
                "source": r["source"],
                "category": r["category"],
                "title": r["title"],
                "snippet": (
                    r["content"][:300].strip() + "..."
                    if len(r["content"]) > 300
                    else r["content"].strip()
                )
            })
            
        sql_query = None
        for r in relevant_results:
            if "vw_ia_servicos" in r.get("source", ""):
                search_words = [w for w in extract_query_keywords(query) if len(w) >= 3 and w not in ["como", "onde", "para", "quero", "saber"]]
                if search_words:
                    conditions = [f"(servico_nome LIKE '%{w}%' OR descricao LIKE '%{w}%')" for w in search_words]
                    sql_query = f"SELECT * FROM vw_ia_servicos WHERE {' OR '.join(conditions)};"
                break
                
        return {
            "answer": answer.strip(),
            "sources": sources_list,
            "confidence": confidence,
            "retrieved_chunks": chunks_info,
            "intent_detected": intent_info["intent"].value,
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": round(retrieval_time * 1000, 2),
                "llm_time_ms": round(llm_time * 1000, 2),
                "total_time_ms": round(total_time * 1000, 2),
                "tokens_used": tokens_usados,
                "keywords": extract_query_keywords(query),
                "internal_sql_query": sql_query,
                "structured_hit": structured_hit,
                "vector_candidates": len(results),
                "official_sources": len([s for s in sources_list if "SECRETARIAS" in s.upper() or "VW_IA_SERVICOS" in s.upper()]),
                "response_source": "structured" if structured_hit and not complementary_parts else ("hybrid" if structured_hit else "complementary"),
                "query_was_rewritten": effective_query != query
            }
        }
