import re
import json
import time
import sys
from config.settings import DEFAULT_DB_PATH, OUVIDORIA_CONTACTS
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
            print(f"[Heuristic Rewriter] Resolvido offline: '{query}' -> '{resolved_heuristic}'", file=sys.stderr)

    # Se estiver offline ou sem chave, usa a heurística local se resolvida
    if not gemini_client or len(gemini_client.api_keys) == 0:
        return resolved_heuristic if resolved_heuristic else query
        
    from agent.memory import ConversationMemory
    history_context = ConversationMemory.get_context(history, gemini_client)
    
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
            q_low = query.lower()
            if any(w in q_low for w in ["menor", "criança", "crianca", "filho", "filha", "agressão", "agressao", "maus-tratos"]):
                ans = (
                    "**Atenção**: Esta é uma situação de extrema gravidade que envolve a proteção e os direitos da criança e do adolescente.\n\n"
                    "• **Emergência Imediata**: Caso a agressão ou risco esteja ocorrendo agora, entre em contato imediatamente com a **Polícia Militar pelo 190** ou com o **Disque Direitos Humanos (Disque 100)**.\n"
                    "• **Denúncia Municipal**: Você pode registrar denúncia no **Conselho Tutelar de Duque de Caxias** ou na **Ouvidoria Geral de Duque de Caxias**: telefone **(21) 2652-3835**, ou pelo aplicativo **Colab** (categoria Assistência Social e Direitos Humanos)."
                )
            else:
                ans = f"Sua solicitação envolve assuntos sensíveis ou denúncias que requerem atenção direta e sigilosa. Este canal informativo não processa esse tipo de demanda automaticamente. Por favor, registre formalmente sua manifestação na **Ouvidoria Geral de Duque de Caxias**: telefone **{OUVIDORIA_CONTACTS['telefone']}**, e-mail **{OUVIDORIA_CONTACTS['email']}** ou presencialmente na **{OUVIDORIA_CONTACTS['presencial']}**."
            intent_detected = "human_escalation"
        elif intent == "DEFESA_CIVIL_EMERGENCIA":
            ans = (
                "**Emergência de Defesa Civil**: Em casos de risco de desabamento, desabamento de imóvel, deslizamento de terra ou alagamento grave, a prioridade absoluta é garantir a sua segurança!\n\n"
                "• **Telefones de Emergência 24h**: Ligue imediatamente para a **Defesa Civil pelo 199** ou **(21) 2676-8000**.\n"
                "• **Acompanhamento no Colab**: Para solicitar vistoria técnica preventiva ou registro de ocorrência, acesse o aplicativo **Colab** no tema **Defesa Civil**."
            )
            intent_detected = "defesa_civil_emergencia"
        elif intent == "SEGURANCA_PUBLICA_EMERGENCIA":
            ans = (
                "**Segurança Pública e Crimes**: Para situações que envolvem tráfico de drogas, tiroteios ou emergências criminais, o atendimento presencial urgente cabe à força policial:\n\n"
                "• **Urgência Policial**: Ligue imediatamente para a **Polícia Militar no 190**.\n"
                "• **Denúncias e Ordem Pública**: Para registrar relatórios sobre o local ou fiscalização de ordem pública, acesse o aplicativo **Colab** ou site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/) selecionando a categoria **Segurança Pública (SMSP)**."
            )
            intent_detected = "seguranca_publica_emergencia"
        elif intent == "FORA_COMPETENCIA":
            query_lower = query.lower()
            if any(w in query_lower for w in ["metro", "metrô", "trem", "supervia"]):
                ans = "Assuntos sobre transporte ferroviário e metrô são de âmbito estadual (Governo do Estado do RJ) e não competem à Prefeitura de Duque de Caxias."
            elif any(w in query_lower for w in ["inss", "aposentadoria", "cpf", "receita federal"]):
                ans = "Assuntos sobre INSS, aposentadoria e CPF/Receita Federal são de âmbito federal e não competem à Prefeitura de Duque de Caxias."
            else:
                ans = "Esta pergunta aborda um tema fora do âmbito das atribuições da Prefeitura de Duque de Caxias. Como assistente virtual municipal, meu foco é orientar sobre secretarias, tributos, escolas, postos de saúde, zeladoria e serviços da nossa cidade."
            intent_detected = "out_of_competency"
        elif intent == "JURIDICO":
            query_lower = query.lower()
            # Perguntas institucionais sobre a função de órgãos municipais (ex: Procuradoria) ou legislação são respondidas pelo RAG
            if any(w in query_lower for w in ["procuradoria", "pgm", "lei orgânica", "lei organica", "código tributário", "codigo tributario"]) and any(w in query_lower for w in ["função", "funcao", "atribuição", "atribuicao", "papel", "competência", "competencia", "o que faz", "estrutura", "qual", "quais", "artigo"]):
                rag_h = agent.handlers.get("RAG_HANDLER")
                if rag_h:
                    return rag_h.execute(query=query, triage_info=triage_info, agent=agent, conversation_id=conversation_id, start_time=start_time, history=history)

            if any(w in query_lower for w in ["árvore", "arvore", "carro", "veículo", "veiculo", "casa", "indenização", "indenizacao", "prejuízo", "prejuizo"]):
                ans = (
                    "Para solicitações de indenização, ressarcimento ou análise de responsabilidade por danos materiais (como queda de árvore sobre veículos ou imóveis), a Prefeitura não realiza acordos ou pareceres formais via chat de atendimento virtual.\n\n"
                    "**Como Proceder:**\n"
                    "• O cidadão deve abrir um **Processo Administrativo de Avaliação de Danos** junto à **Procuradoria Geral do Município** ou dar entrada via **Ouvidoria Geral** (telefone **(21) 2652-3835** ou e-mail **ouvidoria@duquedecaxias.rj.gov.br**).\n"
                    "• É necessário apresentar documentação do bem danificado, fotos do local e Registro de Ocorrência (se houver)."
                )
            else:
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
            if not history:
                ans = ("Olá! Sou o **DUQUE IA**, assistente virtual da Prefeitura de Duque de Caxias.\n\n"
                       "Como posso ajudar você hoje? Pode perguntar sobre secretarias, serviços municipais, "
                       "endereços, ouvidoria ou qualquer outro assunto relacionado à prefeitura.")
            else:
                ans = "Claro! Como posso ajudar você hoje com mais alguma informação ou serviço da Prefeitura de Duque de Caxias?"
            intent_detected = "saudacao"
        else:
            ans = "Estou aqui para tirar dúvidas sobre secretarias, IPTU, Ouvidoria e outros serviços da nossa cidade. Como posso ajudar com Duque de Caxias hoje?"
            intent_detected = "conversa_casual"

        if agent.using_real:
            try:
                if intent == "SAUDACAO":
                    if not history:
                        sys_instruct = (
                            "Você é o Duque IA, assistente virtual da Prefeitura de Duque de Caxias.\n"
                            "O munícipe enviou uma saudação inicial. Responda de forma muito calorosa, descontraída e "
                            "diga: 'Olá! Sou o DUQUE IA, assistente virtual da Prefeitura de Duque de Caxias. Como posso ajudar você hoje?'"
                        )
                    else:
                        sys_instruct = (
                            "Você é o Duque IA, assistente virtual da Prefeitura de Duque de Caxias.\n"
                            "O diálogo já está em andamento (não é a primeira interação). O munícipe enviou uma saudação ou quer retomar.\n"
                            "NUNCA use saudações como 'Olá!', 'Oi!', 'Bom dia!' ou qualquer frase de boas-vindas inicial.\n"
                            "Responda diretamente e de forma casual, mostrando-se à disposição (ex: 'Claro, em que posso ajudar?', 'À disposição, o que você precisa?', 'Pode falar, como posso ajudar?').\n"
                            "Seja muito breve: no máximo 1 ou 2 frases."
                        )
                else:
                    sys_instruct = (
                        "Você é o Duque IA, assistente virtual da Prefeitura de Duque de Caxias.\n"
                        "O cidadão fez um bate-papo informal ou casual. Responda de forma simpática e curta (máximo 3 frases).\n"
                        "NUNCA use saudações redundantes ou inicie a resposta com 'Olá!' ou 'Oi!' se o diálogo já começou.\n"
                        "Lembre-o com leveza que sua especialidade é Duque de Caxias (serviços, secretarias, endereços)."
                    )
                hist_text = "\n".join(history[-4:]) if history else ""
                hist_ctx = f"Contexto recente da conversa:\n{hist_text}\n\n" if hist_text else ""
                full_prompt = f"{hist_ctx}Mensagem do munícipe: \"{query}\""
                ans = agent.gemini_client.generate_response(full_prompt, system_instruction=sys_instruct, model="gemini-3.1-flash-lite").strip()
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
        intent = triage_info.get("intent")
        effective_query = (triage_info.get("rewritten_query") or query).strip()
        effective_lower = effective_query.lower()
        
        # Tratamento especial para relatos de possível conduta inadequada / ofensas (POSSIVEL_DENUNCIA)
        if intent == "POSSIVEL_DENUNCIA":
            from agent.triage import POSSIVEL_DENUNCIA_FAST_PATTERNS
            is_servidor_misconduct = (
                any(re.search(pat, effective_lower) for pat, _, _ in POSSIVEL_DENUNCIA_FAST_PATTERNS) or
                any(w in effective_lower for w in ["servidor", "funcionário", "funcionario", "atendente", "médico", "medico", "guarda", "posto de saúde", "secretaria", "prefeitura", "mau atendimento", "mal atendido", "grosseria", "xing"])
            ) and not any(w in effective_lower for w in ["som alto", "barulho", "comércio", "comercio", "estabelecimento", "obra", "buraco", "lixo", "iluminação", "festa", "festas", "casa de festa", "casa de festas", "evento", "boate", "clube", "rua", "música", "musica"])

            if is_servidor_misconduct:
                if agent.using_real:
                    system_instruction = (
                        "Você é o DUQUE IA, assistente virtual oficial da Prefeitura de Duque de Caxias — RJ.\n"
                        "O cidadão fez um relato indicando possível má conduta, ofensa ou irregularidade envolvendo atendimento ou servidor público (possível denúncia).\n"
                        "Sua missão é responder com empatia e imparcialidade, tratando o caso estritamente como um **relato a ser apurado** (NUNCA assuma ou afirme que a irregularidade foi comprovada), e:\n"
                        "1. Informar os canais formais de registro na **Ouvidoria Geral / Controladoria Geral (CGM)**: aplicativo **Colab** (`duquedecaxias.colab.re`, tipo **Denúncia**) ou telefone **(21) 2652-3835**, esclarecendo que é possível solicitar **sigilo da identidade** conforme a legislação.\n"
                        "2. Convidá-lo a informar em qual **secretaria, posto ou unidade** o fato ocorreu (1 pergunta simples) para orientar eventuais detalhes específicos.\n"
                        "3. Mantenha a resposta concisa (máximo 4 frases) e sem saudações redundantes."
                    )
                    prompt = (
                        f"Mensagem do cidadão: \"{effective_query}\"\n\n"
                        f"Gere a resposta acolhedora de orientação:"
                    )
                    try:
                        answer = agent.gemini_client.generate_response(
                            prompt,
                            system_instruction=system_instruction,
                            model="gemini-3.1-flash-lite",
                            temperature=0.15,
                            max_output_tokens=800
                        ).strip()
                    except Exception:
                        answer = (
                            "Sinto muito pelo ocorrido. Se essa situação aconteceu com um servidor público municipal "
                            "ou durante um atendimento da Prefeitura de Duque de Caxias, você pode registrar uma manifestação "
                            "(reclamação ou denúncia) nos canais oficiais da nossa Ouvidoria Geral.\n\n"
                            "Para eu te orientar sobre como proceder, poderia me informar em qual **secretaria, posto ou órgão** isso ocorreu?"
                        )
                else:
                    answer = (
                        "Sinto muito pelo ocorrido. Se essa situação aconteceu com um servidor público municipal "
                        "ou durante um atendimento da Prefeitura de Duque de Caxias, você pode registrar uma manifestação "
                        "(reclamação ou denúncia) nos canais oficiais da nossa Ouvidoria Geral.\n\n"
                        "Para eu te orientar sobre como proceder, poderia me informar em qual **secretaria, posto ou órgão** isso ocorreu?"
                    )
                    
                return {
                    "answer": answer,
                    "sources": [],
                    "confidence": triage_info.get("confidence", 0.95),
                    "intent_detected": "possivel_denuncia_redirect",
                    "triage_info": triage_info,
                    "metrics": {
                        "retrieval_time_ms": 0,
                        "llm_time_ms": 0,
                        "total_time_ms": round(elapsed * 1000, 2),
                        "tokens_used": 0,
                        "keywords": extract_query_keywords(effective_query)
                    }
                }
            else:
                # Não é má conduta de servidor: normaliza para reclamação regular de serviço/fiscalização
                tipo = triage_info.get("tipo_manifestacao") or "reclamacao"
        else:
            tipo = triage_info.get("tipo_manifestacao", "geral")
        
        # Se for relato de poluição sonora, barulho, evento ou casa de festas, delega diretamente ao RagHandler
        # para aplicar a regra canônica oficial (190 PMERJ + fiscalização SMMA/SMUH/SUOP), evitando loops de perguntas.
        if any(w in effective_lower for w in ["casa de festas", "casa de festa", "som alto", "barulho", "poluicao sonora", "poluição sonora", "festa noturna"]):
            rag_h = RagHandler()
            return rag_h.execute(query=query, triage_info=triage_info, agent=agent, conversation_id=conversation_id, start_time=start_time, history=history)

        if triage_info.get("needs_clarification"):
            answer = agent.gerar_esclarecimento_contextual(effective_query, triage_info)
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
                    "keywords": extract_query_keywords(effective_query)
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
        if "prefeito" in effective_lower and tipo == "reclamacao" and "reclam" not in effective_lower and "denunc" not in effective_lower:
            label = "manifestação"
        else:
            label = _LABELS.get(tipo, "manifestação")
        
        # Usando LLM se disponível para gerar uma resposta acolhedora e natural baseada no serviço encontrado
        if agent.using_real:
            service_context = ""
            try:
                # Tenta buscar estruturado primeiro usando a query efetiva completa
                keywords = extract_query_keywords(effective_query)
                struct_res = retrieve_structured_service(agent.db_path, effective_query, keywords, agent.using_real)
                if history and not struct_res:
                    search_query = f"{effective_query} {' '.join(history)}"
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
                f"Sua missão é validar a demanda dele com simpatia e orientá-lo de forma direta (em até 4 frases) "
                f"de como registrar essa solicitação no aplicativo **Colab** ou pelo site [{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}).\n\n"
                "INSTRUÇÕES DE PREENCHIMENTO:\n"
                "1. Com base na manifestação do munícipe, diga a ele claramente qual **Tema** e **Assunto** selecionar dentro do Colab. Exemplo:\n"
                "   - Se for buraco de asfalto/drenagem: Tema **Obras**.\n"
                "   - Se for capina, roçagem, lixo ou entulho: Tema **Limpeza Urbana**.\n"
                "   - Se for lâmpada apagada no poste: Tema **Transportes, Serviços Públicos e Troca de Lâmpadas**.\n"
                "   - Se for som alto em estabelecimento comercial, bar ou restaurante: Tema **Ordem Pública** (ruídos de bares, restaurantes e comércios). Informe que para a fiscalização atuar é fundamental fornecer o nome e endereço completo do estabelecimento e os horários de pico do barulho.\n"
                "   - Se for som automotivo, carro com som ou paredão na rua: Tema **Ordem Pública** (categoria som automotivo/via pública). Informe a necessidade de indicar a rua, ponto de referência e horários.\n"
                "   - Se for evento ou show em via pública/praça: Tema **Ordem Pública / Meio Ambiente** (fiscalização de eventos e perturbação da ordem).\n"
                "   CRÍTICO: Sugira temas/categorias oficiais e reais. Nunca invente órgãos ou temas inexistentes.\n"
                f"2. Informe os canais da Ouvidoria Geral como alternativa: telefone **{OUVIDORIA_CONTACTS['telefone']}** e e-mail **{OUVIDORIA_CONTACTS['email']}**.\n"
                f"3. Dica rápida: oriente-o a ter em mãos a foto/vídeo e o endereço correto para o registro no Colab ([{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']})).\n"
                "4. Mantenha a resposta concisa, calorosa, objetiva e sem saudações repetidas se o diálogo já estiver em andamento. NÃO faça perguntas desnecessárias se a demanda já estiver clara.\n"
                "5. **Distinção entre Pedido de Informação (e-SIC / LAI) e Reclamação (Ouvidoria)**: Se o cidadão perguntar se deve fazer solicitação única ou separada para obter dados/estatísticas públicas (ex: quantos médicos trabalham no posto) e reclamar de atendimento, oriente expressamente que DEVEM ser feitas em solicitações SEPARADAS: 1) O pedido de informação tramita pelo portal do **e-SIC da Prefeitura** (`https://duquedecaxias.rj.gov.br/e-sic`) com prazo de até 20 dias; 2) A reclamação sobre a falta de atendimento tramita pela **Ouvidoria Geral no aplicativo Colab** (`https://duquedecaxias.colab.re`) com prazo de até 30 dias. NUNCA oriente a registrar os dois juntos em uma única solicitação."
            )

            prompt = (
                f"Contexto do serviço encontrado (USE APENAS SE FOR DIRETAMENTE RELACIONADO AO ASSUNTO DO USUÁRIO):\n{service_context}\n\n"
                f"Tipo da manifestação: {label}\n"
                f"Demanda do cidadão: \"{effective_query}\"\n\n"
                f"Gere a resposta humana de orientação:"
            )

            try:
                answer = agent.gemini_client.generate_response(prompt, system_instruction=system_instruction, model="gemini-3.1-flash-lite").strip()
            except Exception:
                # Fallback offline em caso de erro da API
                if any(w in effective_lower for w in ["som alto", "barulho", "poluição sonora", "comércio", "comercio", "bar"]):
                    answer = (
                        "Entendi perfeitamente! Como a perturbação por som alto é proveniente de um **estabelecimento comercial**, "
                        "a fiscalização compete à Prefeitura através da **Secretaria de Ordem Pública** e da **Secretaria de Meio Ambiente**.\n\n"
                        f"Você pode registrar essa reclamação diretamente no aplicativo **Colab** ou pelo site [{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}), "
                        "selecionando a categoria **Ordem Pública** (ruídos de bares, restaurantes e comércios) ou **Meio Ambiente**.\n\n"
                        "**Dica importante para a fiscalização:** Ao registrar, informe o **nome e endereço completo do estabelecimento**, os **dias e horários** em que o som alto costuma acontecer e, se possível, anexe fotos ou vídeos.\n\n"
                        f"Caso prefira, você também pode registrar através da Ouvidoria Geral: Telefone **{OUVIDORIA_CONTACTS['telefone']}** ou e-mail **{OUVIDORIA_CONTACTS['email']}**."
                    )
                else:
                    answer = (
                        f"Entendi perfeitamente o seu problema. Para registrar essa sua **{label}**, o caminho oficial é através da nossa Ouvidoria Geral de Duque de Caxias. "
                        f"Você pode registrar diretamente pelo aplicativo **Colab**, no site [{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}), ligando para o telefone **{OUVIDORIA_CONTACTS['telefone']}** ou enviando um e-mail para **{OUVIDORIA_CONTACTS['email']}**.\n\n"
                        f"**Dica de amigo:** Quando for registrar no Colab, lembre-se de colocar o endereço bem certinho, com ponto de referência e, se tiver, anexar fotos ou vídeos do local. Isso agiliza muito o trabalho da secretaria para resolver o problema!"
                    )
        else:
            if any(w in effective_lower for w in ["som alto", "barulho", "poluição sonora", "comércio", "comercio", "bar"]):
                answer = (
                    "Entendi perfeitamente! Como a perturbação por som alto é proveniente de um **estabelecimento comercial**, "
                    "a fiscalização compete à Prefeitura através da **Secretaria de Ordem Pública** e da **Secretaria de Meio Ambiente**.\n\n"
                    f"Você pode registrar essa reclamação diretamente no aplicativo **Colab** ou pelo site [{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}), "
                    "selecionando a categoria **Ordem Pública** (ruídos de bares, restaurantes e comércios) ou **Meio Ambiente**.\n\n"
                    "**Dica importante para a fiscalização:** Ao registrar, informe o **nome e endereço completo do estabelecimento**, os **dias e horários** em que o som alto costuma acontecer e, se possível, anexe fotos ou vídeos.\n\n"
                    f"Caso prefira, você também pode registrar através da Ouvidoria Geral: Telefone **{OUVIDORIA_CONTACTS['telefone']}** ou e-mail **{OUVIDORIA_CONTACTS['email']}**."
                )
            else:
                sugerido_txt = ""
                try:
                    keywords = extract_query_keywords(effective_query)
                    struct_res = retrieve_structured_service(agent.db_path, effective_query, keywords, agent.using_real)
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
                    f"• Telefone: **{OUVIDORIA_CONTACTS['telefone']}**\n"
                    f"• E-mail: **{OUVIDORIA_CONTACTS['email']}**\n"
                    f"• Online: aplicativo **Colab** ou site [{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}).\n\n"
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
                "keywords": extract_query_keywords(effective_query)
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
                "4. Se o assunto for barulho, som alto ou perturbação do sossego:\n"
                "   - Em caso de flagrante de perturbação do sossego alheio, som alto, brigas ou ilícitos penais em andamento (inclusive em casas de festas, bares e eventos noturnos): a competência imediata é de **Segurança Pública**, oriente ligar para a **Polícia Militar pelo 190**.\n"
                "   - Para denúncia e fiscalização administrativa da Prefeitura via **Colab** ou **Ouvidoria Geral ((21) 2652-3835)**, oriente a atuação integrada dos órgãos municipais:\n"
                "     * **Secretaria Municipal de Meio Ambiente (SMMA)**: fiscalização técnica de poluição sonora com decibelímetro e infração ambiental (Colab: Meio Ambiente -> Fiscalização legal de poluição sonora);\n"
                "     * **Secretaria Municipal de Urbanismo (SMUU / Posturas)**: fiscalização do alvará de funcionamento, exigência de isolamento acústico e interdição do imóvel;\n"
                "     * **Superintendência de Ordem Pública (SUOP)**: fiscalização ostensiva com unidades móveis em bares e vias públicas, desobstrução de calçadas e apreensão de aparelhagem de som com a Guarda Municipal.\n"
                "   - NUNCA mencione 'horário administrativo'.\n"
                "5. Formate informações importantes em **negrito** (números, telefones, links, temas).\n"
                "6. NUNCA use saudações repetitivas (como 'Olá', 'Oi') se o diálogo já estiver em andamento. Vá direto ao ponto de forma calorosa.\n"
                "7. Mantenha a resposta curta, objetiva, prestativa e calorosa. Máximo 4 frases."
            )
            
            if history:
                system_instruction += (
                    "\nREGRA DE CONVERSA EM ANDAMENTO:\n"
                    "- A conversa já está em andamento. NUNCA comece a resposta com saudações, saudações de boas-vindas, ou cumprimentos (como 'Olá', 'Oi', 'Bom dia', 'Tudo bem', 'Que bom ver você', etc.).\n"
                    "- Vá direto para o assunto."
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
                    max_output_tokens=1000
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
                "Se o som vier de uma **residência particular** (como casa de vizinho, apartamento ou festa privada), "
                "a orientação é acionar a **Polícia Militar pelo 190**, pois a Prefeitura não tem competência legal para intervir em áreas privadas.\n\n"
                "Se vier de **estabelecimento comercial, obra ou veículo em via pública**, a solicitação pode ser registrada pelo aplicativo **Colab** "
                "ou site [duquedecaxias.colab.re](https://duquedecaxias.colab.re/), selecionando a categoria correspondente:\n"
                "• **Ordem Pública**: Bares, restaurantes, comércios e locutores;\n"
                "• **Guarda Municipal**: Veículos não oficiais (som automotivo/paredão);\n"
                "• **Urbanismo**: Obras em andamento;\n"
                "• **Meio Ambiente**: Demais casos de poluição sonora."
            )
        elif intent == "AMBIGUO_LOCALIZACAO":
            answer = (
                "Para eu te indicar a **unidade ou creche mais próxima de você**, por favor me informe o seu **Bairro** e a sua **Rua**.\n\n"
                "Com a sua localização exata, poderei verificar o equipamento público municipal mais conveniente!"
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


def extract_service_details(content: str) -> dict:
    details = {}
    
    # 1. Formato estruturado (vw_ia_servicos)
    if "[FONTE OFICIAL ESTRUTURADA]" in content:
        # Endereço de Atendimento
        addr_match = re.search(r"Endereço de Atendimento:\s*(.*)", content)
        if addr_match:
            addr = addr_match.group(1).strip()
            if addr and addr.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["endereco"] = addr
                
        # Telefones de Contato
        phone_match = re.search(r"Telefones de Contato:\s*(.*)", content)
        if phone_match:
            phone = phone_match.group(1).strip()
            if phone and phone.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["telefones"] = phone
                
        # E-mails de Contato
        email_match = re.search(r"E-mails de Contato:\s*(.*)", content)
        if email_match:
            email = email_match.group(1).strip()
            if email and email.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["emails"] = email
                
        # Links / Canais Digitais
        links_match = re.search(r"Links / Canais Digitais:\s*(.*)", content)
        if links_match:
            links = links_match.group(1).strip()
            if links and links.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["links"] = links
                
        # Documentos Necessários
        doc_match = re.search(r"Documentos Necessários:\n(.*?)(?=\n\n|\n[A-Z]|$)", content, re.DOTALL)
        if doc_match:
            docs = doc_match.group(1).strip()
            clean_docs = "\n".join(line.strip() for line in docs.split("\n") if line.strip() and "Abertura de processo" not in line)
            if clean_docs:
                details["documentos"] = clean_docs
                
        # Passo a Passo de Acesso
        steps_match = re.search(r"Passo a Passo de Acesso:\n(.*?)(?=\n\n|\n[A-Z]|$)", content, re.DOTALL)
        if steps_match:
            steps = steps_match.group(1).strip()
            clean_steps = []
            for line in steps.split("\n"):
                line_strip = line.strip()
                if line_strip:
                    if clean_steps and not line_strip.startswith("Passo"):
                        clean_steps[-1] = clean_steps[-1] + " " + line_strip
                    else:
                        clean_steps.append(line_strip)
            if clean_steps:
                details["passo_a_passo"] = "\n".join(clean_steps)
    else:
        # 2. Formato serializado de planilha Excel (ex: CARTA_DE_SERVICO)
        # Exemplo: Servico: Teste Rápido de Gravidez | Orgao responsavel: ... | Como acessar: ...
        how_match = re.search(r"Como acessar:\s*([^|]+)", content)
        if how_match:
            how = how_match.group(1).strip()
            if how and how.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["passo_a_passo"] = f"Passo 1: {how}"
                
        links_match = re.search(r"(?:Links|Canais Digitais|Link):\s*([^|]+)", content)
        if links_match:
            lnk = links_match.group(1).strip()
            if lnk and lnk.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["links"] = lnk
                
        phone_match = re.search(r"(?:Telefone|Telefones):\s*([^|]+)", content)
        if phone_match:
            phn = phone_match.group(1).strip()
            if phn and phn.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["telefones"] = phn
                
        email_match = re.search(r"(?:E-mail|Email|E-mails):\s*([^|]+)", content)
        if email_match:
            eml = email_match.group(1).strip()
            if eml and eml.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["emails"] = eml
                
        addr_match = re.search(r"(?:Endereço|Endereco|Local):\s*([^|]+)", content)
        if addr_match:
            adr = addr_match.group(1).strip()
            if adr and adr.lower() not in ("não cadastrado", "não disponível", "nan", ""):
                details["endereco"] = adr
                
    return details


def _build_rag_system_instruction(effective_query: str, context_str: str, history: list) -> str:
    """Monta a system_instruction modular do RagHandler: Core Rules + Domain Rules dinâmicas."""
    haystack = f"{effective_query} {context_str}".lower()

    core_rules = [
        "Você é o DUQUE IA, assistente virtual oficial da Prefeitura de Duque de Caxias — RJ.",
        "Sua missão é dar a resposta ideal adaptada ao tipo de pergunta do cidadão, usando com prioridade máxima os dados oficiais fornecidos no contexto.",
        "",
        "REGRAS PRINCIPAIS DE FORMATAÇÃO, ESTILO E CONFIABILIDADE:",
        "1. **Anti-Fluff (Direto ao Ponto)**: NUNCA comece a resposta com saudações genéricas ou preâmbulos desnecessários ('Olá!', 'Bom dia!', 'Compreendo sua dúvida!', 'Com certeza!'). Vá direto à informação útil.",
        "2. **Organização e Formatação Limpa**: Organize as respostas estruturadamente usando marcadores bem definidos em **negrito** (ex: **Quem pode solicitar**, **Documentos Necessários**, **Como Solicitar**, **Contatos / Onde ir**). Evite blocos de texto corrido extensos ou poluídos.",
        "3. **Perguntas Diretas e Pontuais**: Responda de forma direta e concisa (1 a 3 frases), destacando o dado solicitado em **negrito**.",
        "4. **Consultas sobre Serviços**: Forneça orientação clara adaptada ao serviço, cobrindo: **Órgão Responsável**, **Como Solicitar / Passo a Passo**, **Documentos** (se houver), **Prazo**, **Custo** e **Canais de Atendimento** (contatos em **negrito**).",
        "5. **Demandas Múltiplas Coordenadas**: Se o cidadão solicitou mais de um serviço ou fez perguntas sobre temas variados na mesma mensagem (ex: alvará E vigilância sanitária; ou ninho de marimbondo, remoção de entulho, poda de árvore e consulta de cardiologista), estruture OBRIGATORIAMENTE a resposta em tópicos numerados ou seções separadas para cada tema/órgão (ex: 1. Ninho de Marimbondos: Defesa Civil 199 / Bombeiros 193; 2. Retirada de Entulho: Secretaria de Obras via Colab; 3. Poda de Árvore: Secretaria de Meio Ambiente; 4. Consulta Médica: UBS/USF da Saúde -> SISREG). NUNCA omita nenhuma das demandas solicitadas nem junte temas distintos em respostas vagas!",
        "6. **Perguntas Quantitativas / Contagem Exata**: Se o contexto fornecido NÃO apresentar a quantidade exata total, DECLARE EXPLICITAMENTE que a quantidade total não está detalhada na base oficial interna.",
        "7. **Anti-Placeholder**: NUNCA imprima linhas como '**Documentos**: Não especificado no contexto', '**Custo**: Não especificado' ou similares. Se um dado específico não constar no contexto oficial, simplesmente OMITA o marcador correspondente ou oriente consultar o canal oficial.",
        "8. **Foco e Relevância Estrita**: NUNCA mencione ou justifique serviços irrelevantes que aparecerem acidentalmente no contexto se não tiverem relação direta com a pergunta do munícipe (ex: não cite 'tabagismo' ou 'banco de leite' se a pergunta for sobre água ou rua). Responda com foco exclusivo no que foi perguntado!",
        "9. **Anti-Vazamento de Metadados Internos e OCR**: NUNCA exponha nomes de arquivos técnicos, códigos de chunks (ex: 'carta_01237'), termos de scanner óptico (ex: 'OCR Óptico', 'Página 1 *(OCR Óptico)*') ou prefixos de pastas (ex: '07_Secretaria...'). Use SEMPRE o nome oficial e humanizado do órgão ou serviço público.",
        "10. **Proibição de WhatsApp para a Ouvidoria Geral**: A Ouvidoria Geral de Duque de Caxias NÃO POSSUI WhatsApp. O número (21) 99824-5903 NÃO EXISTE. É terminantemente proibido citar canal de WhatsApp para a Ouvidoria Geral. Os canais oficiais são exclusivamente: Telefone fixo (21) 2652-3835, e-mail ouvidoria@duquedecaxias.rj.gov.br e aplicativo Colab.",
        "11. **Honestidade Factual e Humildade Epistêmica**: Quando o contexto oficial não confirmar um dado específico (como vagas abertas no momento, disponibilidade atual de benefício, existência de consulta pública específica ou detalhe jurídico do caso concreto), declare explicitamente que essa informação atualizada não consta na base consultada e indique o canal oficial para confirmação, evitando afirmações categóricas sem respaldo.",
    ]

    domain_rules = []

    if any(k in haystack for k in ("emprego", "vaga", "sine", "concurso", "edital", "processo seletivo", "fundec", "curso", "trabalho")):
        domain_rules.append(
            "- **Vagas de Emprego e Concursos**: Diferencie claramente o catálogo geral de cursos/serviços da disponibilidade de **turmas ou vagas abertas no momento**. Informe que a abertura de inscrições, editais e vagas disponíveis deve ser confirmada nos canais oficiais da **FUNDEC**, do **Sine Caxias** ou no portal oficial de concursos. NUNCA invente, presuma ou informe datas ou quantidades de vagas abertas que não constem expressamente no contexto oficial."
        )

    if any(k in haystack for k in ("poda", "árvore", "arvore", "galho", "alta tensão", "alta tensao", "fio", "eletricidade", "quintal", "smma", "meio ambiente")):
        domain_rules.append(
            "- **Poda de Árvores em Alta Tensão**: Se a árvore estiver encostada em fios de eletricidade/alta tensão, alerte sobre o risco elétrico e explique que a poda exige atuação conjunta/desligamento por parte da concessionária de energia (**Light**), devendo o pedido ser aberto no app **Colab** (Meio Ambiente) e comunicado à Light."
        )
        domain_rules.append(
            "- **Poda de Árvore em Quintal Particular**: Solicitação presencial na **Secretaria Municipal de Meio Ambiente (SMMA)** com **RG, CPF e comprovante de residência/posse**. NÃO oriente o cidadão a ligar antes apenas para perguntar os documentos se ele já vai comparecer presencialmente."
        )

    if any(k in haystack for k in ("terreno", "lote", "mato", "abandonado", "baldio", "smuh", "limpeza")):
        domain_rules.append(
            "- **Terreno Abandonado**: Explique a diferença entre terreno particular (Fiscalização Urbanística - SMUH) e área pública (Limpeza Urbana - Colab)."
        )

    if any(k in haystack for k in ("barulho", "som", "sossego", "poluição sonora", "poluicao sonora", "festa", "boate", "música", "musica", "suop", "decibel")):
        domain_rules.append(
            "- **Barulho / Perturbação do Sossego**: Flagrante noturno, desordem ou ilícitos oriente ligar para a **Polícia Militar (190)**; fiscalização administrativa de poluição sonora comercial oriente os órgãos competentes (**Meio Ambiente / SMMA** para decibelímetro, **Urbanismo / SMUU** para alvará/isolamento acústico e **Superintendência de Ordem Pública (SUOP)** para ordem pública e apreensão de aparelhagem de som com a Guarda Municipal)."
        )

    if any(k in haystack for k in ("quebrei", "fratura", "torção", "torcao", "trauma", "ortoped", "acidente", "emergência", "emergencia", "urgência", "urgencia", "hospital", "upa", "uph", "adão pereira", "moacyr")):
        domain_rules.append(
            "- **Emergências e Traumas Ortopédicos**: Em relatos de trauma físico agudo ou acidentes (ex: 'quebrei o pé', 'fratura', 'torção grave'), indique SEMPRE os hospitais municipais de referência: o **Hospital Estadual/Municipal Adão Pereira Nunes (Saracuruna)** — referência regional de trauma e cirurgia ortopédica — e o **Hospital Municipal Dr. Moacyr Rodrigues do Carmo (HMMRC)**, ou a UPH/UPA 24h mais próxima. NUNCA cite programas eletivos ambulatoriais (como 'Chegaram os Especialistas') em emergências!"
        )

    if any(k in haystack for k in ("silvestre", "gambá", "gamba", "sariguê", "sarigue", "cobra", "serpente", "jacaré", "jacare", "coruja", "morcego", "gavião", "gaviao", "resgate", "animal", "bicho", "fauna")):
        domain_rules.append(
            "- **Resgate de Animais Silvestres**: Para animais silvestres sem risco iminente (gambás, sariguês, cobras, corujas, morcegos em quintal ou via), a competência é da **Guarda Ambiental / Secretaria Municipal de Meio Ambiente (SMMA)** via app **Colab** (Meio Ambiente -> Resgate de Animais Silvestres). Se houver risco iminente ou animal agressivo, acione o **Corpo de Bombeiros (193)**."
        )

    if any(k in haystack for k in ("água", "agua", "esgoto", "águas do rio", "aguas do rio", "luz", "energia", "light", "agenersa", "procon", "abastecimento", "falta d", "desabastecimento")):
        domain_rules.append(
            "- **Concessionárias (Água e Luz) e Desabastecimento Crônico**:\n"
            "   * A responsabilidade operacional direta pelo abastecimento de água e esgoto em Duque de Caxias é da concessionária **Águas do Rio** (Telefone: **0800 195 0 195** | WhatsApp: **(21) 97211-8064**). Para rede elétrica, é a **Light** (**0800 021 0196**).\n"
            "   * A agência reguladora estadual responsável pela fiscalização do contrato de concessão de saneamento é a **AGENERSA** (Ouvidoria: **0800 024 9040** | `agenersa.rj.gov.br`).\n"
            "   * **Papel da Prefeitura de Duque de Caxias**: Quando a concessionária não resolve o problema ou descumpre prazos, a Prefeitura atua através da **Ouvidoria Geral de Duque de Caxias** e do **PROCON Caxias** para notificar e cobrar providências. O munícipe pode registrar no app **Colab (duquedecaxias.colab.re)** (categoria **Concessionárias > Água e Esgoto**) ou Telefone **(21) 2652-3835**. NUNCA emita fallback em dúvidas sobre falta de água!"
        )

    if any(k in haystack for k in ("templo", "igreja", "religios", "culto", "imunidade", "interdição", "interdicao")):
        domain_rules.append(
            "- **Templos Religiosos e Imunidade**: Evite transformar orientação geral em regra jurídica universal. Esclareça que a imunidade tributária constitucional (Art. 150 CF) refere-se a impostos sobre patrimônio, renda e serviços vinculados às finalidades essenciais, e NÃO afasta automaticamente o cumprimento de normas de segurança, prevenção contra incêndio (CBMERJ) e posturas/licenciamento, cuja exigência específica depende da legislação municipal aplicável e da análise técnica dos órgãos competentes (SMF/SMUH)."
        )

    if any(k in haystack for k in ("multa", "jari", "infração", "infracao", "trânsito", "transito", "recurso")):
        domain_rules.append(
            "- **Recurso de Multas Municipais (JARI)**: Para recorrer de multas municipais, o órgão competente é a **JARI (Junta Administrativa de Recursos de Infrações)** da Secretaria de Transportes/Segurança Pública. O prazo legal é de até **30 dias** contados da notificação, protocolado presencialmente no Protocolo Geral da Prefeitura ou pelos canais do Portal Cidadão."
        )

    if any(k in haystack for k in ("e-sic", "esic", "lai", "informação", "informacao", "contrato", "gasto", "prestação de contas", "prestacao de contas", "pss", "temporário", "temporario", "preterição", "nepotismo", "portal cidadão")):
        domain_rules.append(
            "- **e-SIC (LAI) vs Ouvidoria Geral**: Diferencie claramente o **e-SIC** (acesso a dados públicos, cópia de contratos, prestação de contas, estatísticas de gastos, relação nominal de contratados PSS - prazo de 20 dias, via **Portal Cidadão**: `https://portal.duquedecaxias.rj.gov.br` ou `https://duquedecaxias.rj.gov.br/e-sic`) da **Ouvidoria Geral / CGM** (reclamações, denúncias de preterição, nepotismo, desvio de função, elogios - prazo de 30 dias, via `https://duquedecaxias.colab.re`). Forneça o link do **Portal Cidadão** e instrua expressamente a NÃO juntar pedidos de informação e denúncias disciplinares no mesmo protocolo (LAI Lei 12.527/2011 vs Lei 13.460/2017)."
        )

    if any(k in haystack for k in ("emagrec", "nutri", "obesidade", "peso", "dieta")):
        domain_rules.append(
            "- **Emagrecimento e Nutrição**: A porta de entrada no SUS é a **Atenção Primária à Saúde**: comparecer à sua **UBS ou USF (Clínica da Família)** para consulta com clínico geral e posterior encaminhamento ao serviço de **Nutrição** ou programas preventivos. NUNCA mencione PGM ou FUNDEC para emagrecer."
        )

    if any(k in haystack for k in ("lâmpada", "lampada", "poste", "iluminação", "iluminacao", "buraco", "tapa-buraco", "canteiro", "zeladoria", "asfalto")):
        domain_rules.append(
            "- **Zeladoria Urbana vs Ouvidoria**: Lâmpadas apagadas, postes com defeito, canteiros danificados ou buracos são serviços primários de **Zeladoria Urbana** (abertos no app Colab). A Ouvidoria Geral só deve ser acionada caso a solicitação de zeladoria não seja atendida no prazo."
        )

    if any(k in haystack for k in ("sisreg", "consulta", "exame", "especialista", "regulação", "regulacao", "demora", "marcação", "marcacao", "ubs", "posto")):
        domain_rules.append(
            "- **Tom Institucional e Demora no SISREG**: Ao orientar sobre regulação de consultas ou exames e demora para marcação com especialista na UBS, instrua a solicitar na recepção da UBS o **número da solicitação / comprovante do SISREG** para acompanhamento da regulação com transparência e respeito à equipe. Se os prazos clínicos forem extrapolados injustificadamente, oriente registrar manifestação na **Ouvidoria da Saúde** pelo app **Colab** (Saúde > Ouvidoria/Reclamação) ou canais da Ouvidoria Geral."
        )

    if any(k in haystack for k in ("servidor", "funcionário", "funcionario", "fantasma", "plantão", "plantao", "corrupção", "corrupcao", "denúncia", "denuncia", "cgm")):
        domain_rules.append(
            "- **Denúncia de Servidores Irregulares**: Denúncias de conduta de funcionários públicos (como funcionário fantasma ou ausência de plantão) competem à **Ouvidoria Geral / Controladoria Geral (CGM)** via Colab (tipo **Denúncia**), com sigilo da identidade garantido por lei. NUNCA atribua o caso a secretarias arbitrárias não citadas pelo munícipe."
        )

    if any(k in haystack for k in ("chuva", "enchente", "alagamento", "desastre", "desabrigado", "moradia", "aluguel social", "cesta básica", "cesta basica", "cadúnico", "cadunico", "cras", "defesa civil", "smasdh")):
        domain_rules.append(
            "- **Auxílio para Famílias Atingidas por Chuvas e Enchentes**: Para emergência e risco ativo, oriente imediatamente a **Defesa Civil (199)** ou **Bombeiros (193)**. Para suporte social, oriente procurar o **CRAS** de referência ou a **SMASDH** para **acolhimento e avaliação socioassistencial**. Deixe explícito que eventual concessão de benefícios eventuais (como Aluguel Social, Cesta Básica ou inclusão no CadÚnico) **não é automática**, dependendo de avaliação técnica, critérios legais e disponibilidade do programa. NUNCA oriente procurar postos de saúde (UBS/SMS) para benefício de enchente!"
        )

    if any(k in haystack for k in ("obra", "obras", "smoa", "smuh", "urbanismo", "habite-se", "pavimentação", "pavimentacao", "drenagem", "encosta", "quebra-molas", "reurb", "numeração predial", "alvará de construção")):
        domain_rules.append(
            "- **Diferença entre Secretaria de Obras (SMOA) e Secretaria de Urbanismo (SMUH)**: A **Secretaria Municipal de Obras e Agricultura (SMOA)** cuida da execução física da infraestrutura e obras públicas (pavimentação, tapa-buraco, drenagem, dragagem, contenção de encostas e quebra-molas). A **Secretaria Municipal de Urbanismo e Habitação (SMUH)** cuida do planejamento urbano e licenciamento privado (Alvará de Construção, Habite-se, posturas edilícias, numeração predial e REURB)."
        )

    if any(k in haystack for k in ("medicamento", "remédio", "remedio", "farmácia", "farmacia", "idoso", "acamado", "locomoção", "locomocao", "usf", "acs")):
        domain_rules.append(
            "- **Falta de Medicamentos e Pacientes Idosos / Com Mobilidade Reduzida**:\n"
            "   * **Priorize o Cuidado de Saúde**: Oriente buscar apoio na **USF (Clínica da Família)** ou UBS de referência; equipes da ESF e **ACS** realizam visitas domiciliares para facilitar receitas e dispensação (Farmácia Básica / polos SMS).\n"
            "   * **Canais Remotos**: Informe app **Colab (duquedecaxias.colab.re)** e Ouvidoria Geral **(21) 2652-3835**.\n"
            "   * **Separação Clara & Sem Burocracia**: Separe suporte assistencial (USF/ACS) da reclamação (Ouvidoria da Saúde) e NÃO imponha listas burocráticas rígidas de documentos para relatar falta de medicamento (basta nome do paciente, medicamento/dosagem, unidade e data)."
        )

    if any(k in haystack for k in ("calçada", "calcada", "lava-jato", "lava jato", "cone", "cavalete", "barraca", "obstáculo", "obstaculo", "suop", "ordem pública", "ordem publica", "ameaça", "ameaca", "intimidação", "intimidacao")):
        domain_rules.append(
            "- **Fiscalização de Calçadas, Lava-Jatos Irregulares e Ameaças**:\n"
            "   * Desobstrução de calçadas e retirada de obstáculos na via (cones, cavaletes, barracas, lava-jatos irregulares) são executadas pelas **unidades móveis da Superintendência de Ordem Pública (SUOP)** e Guarda Municipal, com apoio da SMUH (Posturas) e SMMA.\n"
            "   * Denúncia pelo app **Colab (duquedecaxias.colab.re)** em **Ordem Pública / Fiscalização** ou **Urbanismo** com endereço, ponto de referência e fotos.\n"
            "   * **Ameaças**: Ameaças ou intimidações constituem crime; em flagrante acione a **Polícia Militar (190)** e registre Boletim de Ocorrência na Polícia Civil."
        )

    if any(k in haystack for k in ("alvará", "alvara", "vizinho", "terceiro", "sigilo", "fazenda", "smf", "comércio", "comercio", "estabelecimento", "sem licença", "irregular")):
        domain_rules.append(
            "- **Sigilo Fiscal e Alvará de Terceiros**: Diferencie dados fiscais protegidos por sigilo (Art. 198 do Código Tributário Nacional — a Secretaria de Fazenda não fornece fichas fiscais ou dados tributários privados de terceiros no balcão) de eventuais informações públicas de licenciamento ou pedidos formais via **e-SIC** (`https://portal.duquedecaxias.rj.gov.br`), esclarecendo que a confirmação de eventual consulta pública disponível deve ser verificada nos portais oficiais. Se houver suspeita de funcionamento irregular, oriente registrar **Denúncia de Estabelecimento Irregular** pelo app **Colab** ou Ouvidoria Geral para vistoria da fiscalização."
        )

    instruction = "\n".join(core_rules)
    if domain_rules:
        instruction += "\n\nREGRAS ESPECÍFICAS APLICÁVEIS AO TEMA:\n" + "\n".join(domain_rules)

    if history:
        instruction += (
            "\n\nREGRA DE CONVERSA EM ANDAMENTO (ANTI-REDUNDÂNCIA):\n"
            "- A conversa já está em andamento. NUNCA comece a resposta com saudações ou cumprimentos (como 'Olá', 'Oi', 'Bom dia').\n"
            "- Se as regras gerais ou procedimentos do serviço já foram explicados na mensagem anterior do histórico, NÃO repita as instruções genéricas anteriores. Responda estritamente à pergunta específica do turno atual."
        )

    return instruction


class RagHandler(BaseHandler):
    """Handler principal para consultas informativas via RAG."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        from agent.router import QueryAnalyzer
        
        # A1: Usa rewritten_query já gerada pela triagem (fusão Triage+Rewriter = -1 chamada LLM)
        # Só chama o rewriter separado se a triagem não veio do LLM (ex: FAST_GATE, SQLITE_CACHE)
        effective_query = query
        triage_source = triage_info.get("source", "")
        triage_rewritten = triage_info.get("rewritten_query", "")
        if triage_rewritten and triage_rewritten.strip() and triage_source == "GEMINI_LLM":
            effective_query = triage_rewritten.strip()
        elif history:
            effective_query = rewrite_query_with_history(query, history, agent.gemini_client)

        
        handler_start = time.time()
        
        # 1. Análise da Query (Roteamento/Informações adicionais)
        router_start = time.time()
        triage_intent = (triage_info.get("intent") or "").lower()
        if triage_intent in ("gis", "institutional", "general"):
            from agent.models import QueryIntent
            intent_map = {"gis": QueryIntent.GIS, "institutional": QueryIntent.INSTITUTIONAL, "general": QueryIntent.GENERAL}
            intent_info = {"intent": intent_map[triage_intent], "confidence": triage_info.get("confidence", 0.9), "entities": []}
        else:
            intent_info = QueryAnalyzer.analyze(effective_query, gemini_client=None)
        router_ms = (time.time() - router_start) * 1000.0
        
        # 2. Busca RAG Híbrida (com Multi-Query Decomposer para demandas múltiplas coordenadas)
        retrieval_start = time.time()
        tools_selected = triage_info.get("tools_selected")

        eff_lower = effective_query.lower()
        sub_queries = []
        if ("alvará" in eff_lower or "alvara" in eff_lower) and any(w in eff_lower for w in ["vigilância", "vigilancia", "sanitária", "sanitaria"]):
            sub_queries = [
                "regularização profissional liberal alvará de funcionamento inscrição municipal secretaria municipal de fazenda",
                "licença e certificado de vigilância sanitária municipal estabelecimento saúde secretaria municipal de saúde"
            ]
        elif any(w in eff_lower for w in ["marimbondo", "vespa", "abelha"]) and any(w in eff_lower for w in ["entulho", "poda", "árvore", "arvore", "cardiologista", "consulta"]):
            sub_queries = [
                "ninho de marimbondo vespas abelhas na rua pública defesa civil 199 bombeiros 193",
                "remoção e retirada de entulho calçada porta de casa secretaria municipal de obras colab",
                "poda de árvore em quintal particular secretaria municipal de meio ambiente",
                "marcar consulta médica cardiologista posto de saúde clínica da família regulação sisreg"
            ]

        if sub_queries:
            combined_results = []
            seen_sources = set()
            for sq in sub_queries:
                sub_res = retrieve_context(
                    sq, agent.db_path, agent.using_real, 0.25,
                    agent.gemini_client, agent.reranker, top_k=4, intent_info=intent_info,
                    tools_selected=tools_selected
                )
                for r in sub_res:
                    src_key = r.get("source") or r.get("title") or r.get("id")
                    if src_key and src_key not in seen_sources:
                        seen_sources.add(src_key)
                        combined_results.append(r)
            results = combined_results if combined_results else retrieve_context(
                effective_query, agent.db_path, agent.using_real, agent.similarity_threshold,
                agent.gemini_client, agent.reranker, top_k=6, intent_info=intent_info,
                tools_selected=tools_selected
            )
        else:
            results = retrieve_context(
                effective_query, agent.db_path, agent.using_real, agent.similarity_threshold,
                agent.gemini_client, agent.reranker, top_k=6, intent_info=intent_info,
                tools_selected=tools_selected
            )
        
        # Se a busca falhar com o limite padrão, tenta recuperar buscando com a query concatenada em último caso
        if history and (not results or results[0].get("similarity", 0.0) < 0.65) and effective_query == query:
            search_query = f"{query} {' '.join(history[-2:])}"
            history_results = retrieve_context(
                search_query, agent.db_path, agent.using_real, agent.similarity_threshold,
                agent.gemini_client, agent.reranker, top_k=6, intent_info=intent_info,
                tools_selected=tools_selected
            )
            if history_results and (not results or history_results[0].get("similarity", 0.0) > results[0].get("similarity", 0.0)):
                results = history_results
                effective_query = search_query
                
        retrieval_ms = (time.time() - retrieval_start) * 1000.0
        retrieval_time = retrieval_ms / 1000.0
        
        # 3. Guardrail de Retrieval
        query_lower = effective_query.lower()
        essential_keywords = ["prefeito", "secretaria", "ouvidoria", "fundec", "colab", "telefone"]
        is_essential = any(k in query_lower for k in essential_keywords)
        effective_threshold = 0.25 if is_essential else agent.similarity_threshold
        
        relevant_results = [r for r in results if r.get("similarity", 0.0) >= effective_threshold]
        relevant_results.sort(key=lambda r: r.get("similarity", 0.0), reverse=True)

        if not relevant_results:
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
        
        # 5. Calibração da Confiança (Antecipada)
        base_score = relevant_results[0]["similarity"]
        confidence = calibrate_confidence(base_score, query, relevant_results)
        
        # A2: Clarificação de Baixa Confiança Off-LLM (sem chamada extra à API)
        # Usa o título e categoria do Top-1 para gerar pergunta de confirmação local.
        if base_score < 0.60:
            query_norm = query.lower()
            is_factual_query = any(kw in query_norm for kw in ["quantos", "quantas", "onde", "quais", "lista", "praça", "praças", "hospital", "hospitais", "escola", "escolas", "creche", "creches"])
            if is_factual_query:
                from agent.fallback import build_controlled_web_fallback
                web_fb = build_controlled_web_fallback(effective_query, agent.gemini_client)
                if web_fb and web_fb.get("is_web_fallback"):
                    total_time = time.time() - start_time
                    return {
                        "answer": web_fb["answer"],
                        "sources": web_fb["sources"],
                        "confidence": web_fb["confidence"],
                        "confidence_matrix": web_fb.get("metrics_triple", {}),
                        "intent_detected": "web_fallback_low_confidence",
                        "triage_info": triage_info,
                        "metrics": {
                            "retrieval_time_ms": round(retrieval_time * 1000, 2),
                            "llm_time_ms": round((total_time - retrieval_time) * 1000, 2),
                            "total_time_ms": round(total_time * 1000, 2),
                            "tokens_used": 150,
                            "keywords": extract_query_keywords(query)
                        }
                    }

            top_title = relevant_results[0].get("title", "")
            top_category = relevant_results[0].get("category", "")
            if top_title and top_category in ("carta_servicos", "secretarias", "unidades"):
                clarification_query = (
                    f"Só para confirmar: você está perguntando sobre **\"{top_title}\"**, "
                    f"ou sobre outro serviço/local? Me diga mais detalhes para eu te ajudar melhor! 😊"
                )
            elif top_title:
                clarification_query = (
                    f"Poderia esclarecer um pouco mais sua dúvida? "
                    f"O assunto mais próximo que encontrei foi **\"{top_title}\"** — é sobre isso ou sobre algo diferente?"
                )
            else:
                clarification_query = (
                    "Poderia detalhar um pouco mais sua dúvida? "
                    "Não encontrei uma correspondência exata — quanto mais específico você for, melhor posso te ajudar!"
                )
            total_time = time.time() - start_time
            agent.log_execution_metrics(query, retrieval_time, 0, total_time, base_score, 0, 0.0)
            return {
                "answer": clarification_query,
                "sources": [],
                "confidence": confidence,
                "retrieved_chunks": [],
                "intent_detected": "low_confidence_clarification",
                "triage_info": triage_info,
                "metrics": {
                    "retrieval_time_ms": round(retrieval_time * 1000, 2),
                    "llm_time_ms": 0,
                    "total_time_ms": round(total_time * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(query)
                }
            }



        sources_list = list(set(r["source"] for r in relevant_results))
        
        # 4. Geração de Resposta (LLM ou Fallback Offline)
        llm_start = time.time()
        # 3. Conversão de Candidatos e Aplicação do Motor Declarativo de Ranking
        from agent.candidate import Candidate
        from agent.ranking import CandidateRanker
        from agent.context_builder import ContextBuilder
        from agent.telemetry import PermanentTelemetry

        candidate_objects = []
        for r in relevant_results:
            c_obj = Candidate(
                source=r.get("source", "desconhecido"),
                title=r.get("title", ""),
                category=r.get("category", "geral"),
                content=r.get("content", ""),
                semantic_score=r.get("semantic_score", 0.0),
                keyword_score=r.get("keyword_score", 0.0),
                retrieval_score=r.get("similarity", 0.0),
                chunk_keywords=r.get("chunk_keywords", [])
            )
            candidate_objects.append(c_obj)

        ranking_start = time.time()
        ranked_candidates = CandidateRanker.apply_ranking(effective_query, candidate_objects)
        ranking_ms = (time.time() - ranking_start) * 1000.0

        confidence_level, top_score = CandidateRanker.evaluate_confidence(ranked_candidates)

        # ------------------------------------------------------------------ #
        # CONFIDENCE GATE & ZONA CINZENTA (0.50 - 0.85):                      #
        # - top_score < 0.50: Baixa confiança de dados locais -> Web Search   #
        # - 0.50 <= top_score < 0.85: RAG com fallback pós-LLM                #
        # ------------------------------------------------------------------ #
        if top_score < 0.50:
            from agent.fallback import build_controlled_web_fallback
            web_fb = build_controlled_web_fallback(effective_query, agent.gemini_client)

            total_time = time.time() - start_time
            agent.log_execution_metrics(
                user_query=query,
                retrieval_time=retrieval_time,
                llm_time=total_time - retrieval_time,
                total_time=total_time,
                similarity_score=top_score,
                tokens_usados=150,
                embedding_cost=0.0,
                rewritten_query=effective_query if effective_query != query else None,
                structured_hit=False,
                vector_count=len(relevant_results),
                selected_sources=web_fb["sources"]
            )

            return {
                "answer": web_fb["answer"],
                "sources": web_fb["sources"],
                "confidence": web_fb["confidence"],
                "confidence_matrix": web_fb.get("metrics_triple", {}),
                "intent_detected": "web_fallback_low_confidence",
                "triage_info": triage_info,
                "metrics": {
                    "retrieval_time_ms": round(retrieval_ms, 2),
                    "ranking_time_ms": round(ranking_ms, 2),
                    "llm_time_ms": round((total_time - retrieval_time) * 1000, 2),
                    "total_time_ms": round(total_time * 1000, 2),
                    "tokens_used": 150,
                    "keywords": extract_query_keywords(query)
                }
            }

        # 4. Construção de Contexto Oficial
        context_start = time.time()
        context_str, selected_sources, top_candidates = ContextBuilder.build_context(ranked_candidates, top_k=6)
        context_ms = (time.time() - context_start) * 1000.0

        agent._last_context = context_str
        
        # 5. Geração de Resposta (LLM ou Fallback Offline)
        llm_start = time.time()
        prompt_start = time.time()
        
        if agent.using_real:
            system_instruction = _build_rag_system_instruction(effective_query, context_str, history)
            
            prompt = (
                f"Contexto oficial da Carta de Serviços (use SOMENTE estas informações para responder):\n"
                f"{context_str}\n\n"
                f"Pergunta do cidadão:\n{effective_query}\n\n"
                f"Gere uma resposta clara, objetiva e adaptada ao tipo de pergunta, sem preâmbulos desnecessários:"
            )
            
            from agent.agent import DuqueIAAgent
            session_model = DuqueIAAgent._model_sessions.get(conversation_id) if conversation_id and hasattr(DuqueIAAgent, "_model_sessions") else None
            
            if not hasattr(DuqueIAAgent, "_interaction_map"):
                DuqueIAAgent._interaction_map = {}
            gemini_interaction_id = DuqueIAAgent._interaction_map.get(conversation_id) if conversation_id else None
            
            prompt_ms = (time.time() - prompt_start) * 1000.0
            gemini_start = time.time()
            try:
                answer, new_conv_id, working_model = agent.gemini_client.generate_interaction(
                    prompt,
                    system_instruction=system_instruction,
                    model=session_model,
                    previous_interaction_id=gemini_interaction_id,
                    temperature=0.15,
                    max_output_tokens=8192
                )
                if new_conv_id and conversation_id:
                    DuqueIAAgent._interaction_map[conversation_id] = new_conv_id
                    if hasattr(DuqueIAAgent, "_model_sessions") and working_model:
                        DuqueIAAgent._model_sessions[conversation_id] = working_model
            except Exception as e:
                print(f"[Gemini Interaction Warning] Falha na chamada da LLM (usando fallback offline): {e}", file=sys.stderr)
                if base_score < effective_threshold:
                    answer = build_fallback_guidance(query)
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
                            f"\n\n*Fonte: {best_match['source']} (Fallback Offline)*"
                        )
            gemini_ms = (time.time() - gemini_start) * 1000.0
            post_start = time.time()

            # Sanitização determinística de campos nulos/None na resposta final
            patterns_null = [
                r"(?i)\(?\s*WhatsApp:\s*(?:None|null|undefined|N/A)\s*\)?",
                r"(?i)\(?\s*Telefone:\s*(?:None|null|undefined|N/A)\s*\)?",
                r"(?i)\(?\s*Endereço:\s*(?:None|null|undefined|N/A)\s*\)?",
                r"(?i)\(?\s*E-mail:\s*(?:None|null|undefined|N/A)\s*\)?"
            ]
            for pat in patterns_null:
                answer = re.sub(pat, "", answer)
            # Remove linhas com marcadores de campos não especificados (Anti-Placeholder)
            answer = re.sub(r'(?m)^[•\*\-]?\s*\*\*(?:Documentos|Documentos Necessários|Custo|Taxa|Prazo|Canais de Atendimento)\*\*:\s*(?:Não especificado|Não informado|Não consta|Não detalhad)[^\n]*\n?', '', answer)
            # Remove eventuais menções a serviços irrelevantes que vazaram no contexto (ex: tabagismo/banco de leite)
            answer = re.sub(r'(?i)^.*?(?:Tratamento para Fumantes|Banco de Leite Humano).*?$\n?', '', answer, flags=re.MULTILINE)
            answer = re.sub(r'(?i)^.*?as informações que possuo no momento são sobre os serviços de.*?$\n?', '', answer, flags=re.MULTILINE)
            # Sanitização determinística de vazamento de metadados internos, OCR óptico e códigos de chunks
            answer = re.sub(r'\s*\*?\(OCR[^\)]*\)\*?', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'###\s*Página\s*\d+\s*\*?\(OCR[^\)]*\)\*?', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'\b\d{2}_([A-Za-z0-9_]+):\s*Página\s*\d+', lambda m: m.group(1).replace('_', ' '), answer)
            answer = re.sub(r'\bcarta_\d+\b', '', answer, flags=re.IGNORECASE)
            # Remove qualquer alusão a WhatsApp da Ouvidoria ou ao número 99824-5903 (a Ouvidoria NÃO tem WhatsApp)
            answer = re.sub(r'(?i)[•\*\-]?\s*(?:\*\*)?(?:WhatsApp(?:\s+da\s+Ouvidoria(?:\s+Geral)?)?|WhatsApp:?)(?:\*\*)?:?\s*(?:\(21\)\s*)?99824[-.\s]?5903[^\n]*\n?', '', answer)
            answer = re.sub(r'(?i)(?:,\s*)?(?:e\s+)?WhatsApp(?:\s+da\s+Ouvidoria(?:\s+Geral)?)?\s*(?:\*\*)?(?:\(21\)\s*)?99824[-.\s]?5903(?:\*\*)?', '', answer)
            answer = re.sub(r'(?i)(?:\(21\)\s*)?99824[-.\s]?5903', '', answer)
            answer = re.sub(r'\(\s*\)', '', answer)
            answer = re.sub(r'\s*\(\s*$', '.', answer)  # Remove parêntese órfão no final substituindo por ponto
            answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer).strip()

            # FALLBACK PÓS-LLM: Se a resposta do LLM declarar que o dado não consta nos dados locais
            # Regras canônicas de governança têm prioridade máxima e NUNCA sofrem override por busca web
            has_regra = any("regra" in str(c.get("category", "")).lower() or "regra" in str(c.get("source", "")).lower() for c in relevant_results)
            
            unprovided_triggers = [
                "não especificam", "não especifica", "não detalham", "não detalha", "não está detalhad",
                "não constam", "não consta", "não contêm", "não contém", "não informam", "não informa",
                "não há registro", "não há informação", "não foram encontrad", "não foi possível localizar",
                "não foi possível determinar", "não foi possível encontrar", "não temos essa informação",
                "não possui informação", "não há dados disponíveis sobre"
            ]
            ans_lower = answer.lower()
            if top_score < 0.70 and not has_regra and any(trig in ans_lower for trig in unprovided_triggers):
                try:
                    from agent.fallback import build_controlled_web_fallback
                    web_fb = build_controlled_web_fallback(effective_query, agent.gemini_client)
                    if web_fb and web_fb.get("is_web_fallback"):
                        answer = web_fb["answer"]
                        sources_list = web_fb.get("sources", sources_list)
                        confidence = web_fb.get("confidence", confidence)
                        confidence_level = "MEDIA"
                except Exception as e_web:
                    print(f"[RAGHandler Post-LLM Fallback Warning] Falha na busca web pós-LLM: {e_web}", file=sys.stderr)
        else:
            prompt_ms = 0.0
            gemini_ms = 0.0
            post_start = time.time()
            if base_score < effective_threshold:
                answer = build_fallback_guidance(query)
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
            

        # A síntese gerada pela LLM via RAG já contém todos os fatos, endereços e passos necessários.
        # Desativamos a concatenação mecânica de blocos brutos (Informações Adicionais / Passo a Passo presencial)
        # para evitar contradições com os canais digitais do Colab e informações descontextualizadas.

        # Aplicação da Política de Resposta via ResponseComposer (Orquestração de Intenção)
        from agent.composer import ResponseComposer
        answer = ResponseComposer.compose(query, answer, intent=intent_info["intent"].value)


        llm_time = time.time() - llm_start
        total_time = time.time() - start_time

        try:
            PermanentTelemetry.log_execution(
                query=effective_query,
                retrieval_ms=retrieval_time * 1000.0,
                ranking_ms=ranking_ms,
                context_ms=context_ms,
                llm_ms=llm_time * 1000.0,
                candidates_found=len(relevant_results),
                top_candidates=top_candidates,
                answer=answer,
                sources_used=selected_sources,
                confidence_level=confidence_level
            )
        except Exception as e_tel:
            print(f"[Telemetry Warning] Erro ao gravar estatísticas: {e_tel}", file=sys.stderr)
        
        # 5. Calibração da Confiança
        base_score = relevant_results[0]["similarity"]
        confidence = calibrate_confidence(base_score, query, relevant_results)
        
        top_hybrid_score = relevant_results[0].get("hybrid_score_original", base_score)
        top_cross_score = relevant_results[0].get("cross_encoder_score", 0.0)
        
        # 6. Métricas com cálculo real de custos Gemini (Input, Output e Embeddings)
        input_tokens = len(effective_query) // 4 + sum(len(r["content"]) for r in relevant_results) // 4
        output_tokens = len(answer) // 4
        tokens_usados = input_tokens + output_tokens
        # Custo real: ~$0.075/1M tokens entrada + ~$0.30/1M tokens saída + $0.02/1M tokens embedding
        embedding_cost = round((input_tokens * 0.000000075) + (output_tokens * 0.00000030) + (len(effective_query) // 4 * 0.00000002), 7) if agent.using_real else 0.0
        
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

        post_ms = (time.time() - post_start) * 1000.0
        total_handler_ms = (time.time() - handler_start) * 1000.0

        tree_telemetry = (
            f"\nRAG_HANDLER\n"
            f"├── retrieval/busca       : {retrieval_ms:8.2f} ms\n"
            f"├── reranking             : {ranking_ms:8.2f} ms\n"
            f"├── montagem contexto     : {context_ms:8.2f} ms\n"
            f"├── montagem prompt       : {prompt_ms:8.2f} ms\n"
            f"├── Gemini                : {gemini_ms:8.2f} ms\n"
            f"├── pós-processamento     : {post_ms:8.2f} ms\n"
            f"└── TOTAL                 : {total_handler_ms:8.2f} ms\n"
        )
        print(tree_telemetry, file=sys.stderr)
                
        return {
            "answer": answer.strip(),
            "sources": sources_list,
            "confidence": confidence,
            "retrieved_chunks": chunks_info,
            "intent_detected": intent_info["intent"].value,
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": round(retrieval_ms, 2),
                "ranking_time_ms": round(ranking_ms, 2),
                "context_time_ms": round(context_ms, 2),
                "prompt_time_ms": round(prompt_ms, 2),
                "gemini_time_ms": round(gemini_ms, 2),
                "post_processing_time_ms": round(post_ms, 2),
                "total_handler_time_ms": round(total_handler_ms, 2),
                "llm_time_ms": round(llm_time * 1000, 2),
                "total_time_ms": round(total_time * 1000, 2),
                "tokens_used": tokens_usados,
                "keywords": extract_query_keywords(query),
                "internal_sql_query": sql_query,
                "structured_hit": structured_hit,
                "vector_candidates": len(results),
                "official_sources": len([s for s in sources_list if "SECRETARIAS" in s.upper() or "VW_IA_SERVICOS" in s.upper()]),
                "response_source": "structured" if structured_hit and not any(c.category != "carta_servicos" for c in top_candidates) else ("hybrid" if structured_hit else "complementary"),
                "query_was_rewritten": effective_query != query,
                "hybrid_score": round(top_hybrid_score, 4),
                "cross_score": round(top_cross_score, 4),
                "similarity_score": round(base_score, 4),
                "cost_usd": embedding_cost
            }
        }


class AuthorityHandler(BaseHandler):
    """Handler especializado em responder consultas sobre autoridades municipais."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        import unicodedata
        import difflib
        from agent.authorities_catalog import AUTHORITIES

        elapsed = time.time() - start_time
        
        # 1. Normalizador robusto de acentos usando unicodedata e equivalência de gênero
        def _normalize(text: str) -> str:
            text = unicodedata.normalize("NFKD", text)
            t = "".join(c for c in text if not unicodedata.combining(c)).lower().strip()
            t = t.replace("secretaria", "secretario")
            t = t.replace("prefeita", "prefeito")
            t = re.sub(r'\s+de\s+duque\s+de\s+caxias\b|\s+duque\s+de\s+caxias\b', '', t)
            return t.strip()

        # 2. Parser de prefixos de perguntas de autoridades (apenas pronomes e verbos de pergunta)
        AUTHORITY_PATTERNS = [
            "voce sabe qual o nome do", "você sabe qual o nome do",
            "voce sabe qual o nome da", "você sabe qual o nome da",
            "voce sabe qual o", "você sabe qual o",
            "voce sabe qual a", "você sabe qual a",
            "voce sabe quem é o", "você sabe quem é o",
            "voce sabe quem e o", "você sabe quem e o",
            "voce sabe quem é a", "você sabe quem é a",
            "voce sabe quem e a", "você sabe quem e a",
            "voce sabe quem é", "você sabe quem é",
            "voce sabe quem e", "você sabe quem e",
            "sabe qual o nome do", "sabe qual o nome da",
            "sabe quem é o", "sabe quem e o",
            "sabe quem é a", "sabe quem e a",
            "sabe quem é", "sabe quem e",
            "qual o nome do", "qual o nome da", "qual o nome",
            "qual é o nome do", "qual é o nome da", "qual é o nome",
            "qual e o nome do", "qual e o nome da", "qual e o nome",
            "quem é o titular do", "quem é o titular da", "quem e o titular do", "quem e o titular da",
            "quem é o titular", "quem e o titular",
            "quem é o", "quem é a", "quem é",
            "quem e o", "quem e a", "quem e",
            "qual é o", "qual é a", "qual é",
            "qual e o", "qual e a", "qual e",
            "quem dirige o", "quem dirige a", "quem dirige",
            "quem administra o", "quem administra a", "quem administra",
            "quem comanda o", "quem comanda a", "quem comanda",
            "quem ocupa o cargo de", "quem ocupa o cargo da", "quem ocupa o cargo",
            "o responsável pela", "o responsavel pela",
            "o responsável pelo", "o responsavel pelo",
            "qual o", "qual a",
        ]
        AUTHORITY_PATTERNS.sort(key=len, reverse=True)

        q_clean = query.lower().strip()
        q_clean = re.sub(r'^[¿\?¡\!]+|[¿\?¡\!]+$', '', q_clean).strip() # remove pontuações finais/iniciais

        # Strip prefixes de perguntas garantindo fronteira de espaço para não cortar nomes (ex: Aline)
        for pattern in AUTHORITY_PATTERNS:
            p_with_space = pattern + " "
            if q_clean.startswith(p_with_space):
                q_clean = q_clean[len(p_with_space):].strip()
                break
            elif q_clean == pattern:
                q_clean = ""
                break

        q_normalized = _normalize(q_clean)
        auth = None
        matched_by_name = False

        # 3.1 Busca prioritária por Nome de Autoridade ou Apelido (ex: "Netinho Reis", "Boquinha", "Valber")
        q_norm_words = set(q_normalized.split())
        stopwords = {"de", "da", "do", "o", "a", "em", "para", "quem", "e", "voce", "você", "sabe", "qual", "nome"}
        q_clean_words = q_norm_words - stopwords

        for key, val in AUTHORITIES.items():
            nome_raw = val.get("nome", "")
            nome_norm = _normalize(nome_raw)
            apelidos = re.findall(r'\((.*?)\)', nome_raw)
            apelidos_norm = [_normalize(a) for a in apelidos]

            if len(q_normalized) >= 4:
                if q_normalized in nome_norm or any(q_normalized in ap for ap in apelidos_norm):
                    auth = val
                    matched_by_name = True
                    break
                if any(len(ap) >= 4 and ap in q_normalized for ap in apelidos_norm):
                    auth = val
                    matched_by_name = True
                    break
                nome_tokens = set(nome_norm.replace("(", "").replace(")", "").split()) - stopwords
                if q_clean_words and q_clean_words.issubset(nome_tokens) and len(q_clean_words) >= 1:
                    if any(len(w) >= 5 for w in q_clean_words) or len(q_clean_words) >= 2:
                        auth = val
                        matched_by_name = True
                        break

        # 3.2 Se não encontrou por nome, busca por Cargo / Secretaria via similaridade combinada
        if not auth:
            best_match_key = None
            best_match_score = 0.0

            for key in AUTHORITIES.keys():
                key_norm = _normalize(key)
                key_norm_words = set(key_norm.split())
                key_clean_words = key_norm_words - stopwords
                
                # Similaridade por interseção de palavras
                word_score = 0.0
                if key_clean_words:
                    intersection = q_clean_words.intersection(key_clean_words)
                    word_score = len(intersection) / len(key_clean_words)
                    
                # Similaridade por caracteres (difflib)
                char_score = difflib.SequenceMatcher(None, q_normalized, key_norm).ratio()
                
                # Score combinado: 70% peso nas palavras estruturais, 30% nos caracteres
                combined_score = 0.7 * word_score + 0.3 * char_score
                
                # Boost especial para substrings exatas
                if key_norm == q_normalized or (len(key_norm) > 3 and key_norm in q_normalized) or (len(q_normalized) > 3 and q_normalized in key_norm):
                    combined_score = max(combined_score, 0.90)
                    
                if combined_score > best_match_score:
                    best_match_score = combined_score
                    best_match_key = key

            # Só consideramos correspondência se o score combinado for alto (ex: >= 0.70)
            if best_match_key and best_match_score >= 0.70:
                auth = AUTHORITIES[best_match_key]

        if auth:
            nome = auth["nome"]
            cargo = auth["cargo"]
            fonte = auth["fonte"]

            # Recupera a versão do catálogo se disponível
            try:
                from agent.authorities_catalog import CATALOG_VERSION
            except ImportError:
                CATALOG_VERSION = "2026-07-13"

            # 4. Geração de sugestões dinâmicas baseadas no cargo/órgão encontrado
            cargo_lower = cargo.lower()
            sugestoes = []
            
            if "vice" in cargo_lower:
                sugestoes = [
                    "• Quem é o **Prefeito** de Duque de Caxias",
                    "• Qual o contato e localização do **Gabinete da Vice-Prefeita**",
                    "• Quais são as **Secretarias Municipais** da Prefeitura"
                ]
            elif "prefeito" in cargo_lower:
                sugestoes = [
                    "• Quem é a **Vice-Prefeita** de Duque de Caxias",
                    "• Quais são as **Secretarias Municipais** da Prefeitura",
                    "• Qual o endereço da **Prefeitura Municipal**"
                ]
            elif "saude" in cargo_lower or "saúde" in cargo_lower:
                sugestoes = [
                    "• Qual o endereço ou contato da **Secretaria de Saúde**",
                    "• Quais são os **Hospitais Municipais** e unidades de saúde 24h",
                    "• Como entrar em contato com a **Ouvidoria do SUS**"
                ]
            elif "obras" in cargo_lower:
                sugestoes = [
                    "• Qual o telefone ou canal da **Secretaria de Obras**",
                    "• Como solicitar serviço de **Tapa-Buraco** ou drenagem de via",
                    "• Onde fica a sede da Secretaria de Obras"
                ]
            elif "educa" in cargo_lower:
                sugestoes = [
                    "• Como entrar em contato com a **Secretaria de Educação**",
                    "• Onde obter informações sobre matrícula escolar em creche municipal",
                    "• Lista de escolas municipais de Duque de Caxias"
                ]
            elif "fazenda" in cargo_lower or "finança" in cargo_lower or "orcamento" in cargo_lower:
                sugestoes = [
                    "• Como solicitar a segunda via do **IPTU**",
                    "• Qual o endereço ou contato da **Secretaria de Fazenda**",
                    "• Como consultar taxas municipais"
                ]
            else:
                # Sugestões dinâmicas genéricas baseadas no órgão
                orgao = cargo.split(" de ")[-1] if " de " in cargo else "órgão"
                sugestoes = [
                    f"• Qual o endereço e contato da **Secretaria de {orgao}**",
                    f"• Quais os serviços públicos prestados pela **Secretaria de {orgao}**",
                    "• Como registrar uma solicitação oficial a esta secretaria no Colab"
                ]

            sugestoes_str = "\n".join(sugestoes)

            detalhes_raw = (auth.get('detalhes') or "").strip()
            detalhes_limpo = detalhes_raw
            if detalhes_raw:
                # Deduplica se detalhes apenas repetir literalmente nome e cargo
                d_lower = detalhes_raw.lower()
                n_lower = nome.lower()
                c_lower = cargo.lower()
                if n_lower in d_lower and c_lower in d_lower:
                    partes = [p.strip() for p in detalhes_raw.split(".") if p.strip()]
                    partes_uteis = [p for p in partes if not (any(tok in p.lower() for tok in ["netinho reis é o prefeito", "é o prefeito de duque", "é o secretário de", "é a secretária de", "é o vice-prefeito", "é a vice-prefeita"]))]
                    detalhes_limpo = ". ".join(partes_uteis) + ("." if partes_uteis else "")

            detalhes_str = f"\n\n{detalhes_limpo}" if detalhes_limpo.strip() else ""
            cargo_title = cargo if "duque de caxias" in cargo.lower() else f"{cargo} de Duque de Caxias"
            is_feminine = any(fem in cargo_title.lower() for fem in ["vice-prefeita", "prefeita", "secretária", "ouvidora", "controladora"])
            artigo = "A" if is_feminine else "O"
            verbo_cargo = "é a" if is_feminine else "é o"

            if matched_by_name:
                answer = (
                    f"**{nome}** {verbo_cargo} **{cargo_title}**.{detalhes_str}\n\n"
                    f"Essa informação consta na estrutura oficial da Prefeitura (Fonte: **{fonte}** / Versão do Catálogo: **{CATALOG_VERSION}**).\n\n"
                    f"Caso deseje, posso informar também:\n"
                    f"{sugestoes_str}"
                )
            else:
                answer = (
                    f"{artigo} **{cargo_title}** é **{nome}**.{detalhes_str}\n\n"
                    f"Essa informação consta na estrutura oficial da Prefeitura (Fonte: **{fonte}** / Versão do Catálogo: **{CATALOG_VERSION}**).\n\n"
                    f"Caso deseje, posso informar também:\n"
                    f"{sugestoes_str}"
                )
            
            if agent:
                agent._last_context = f"{nome} - {cargo} - {detalhes_limpo}"
            agent.log_execution_metrics(query, 0, 0, elapsed, 0, 0, 0)
            return {
                "answer": answer,
                "sources": [fonte],
                "confidence": 1.0,
                "intent_detected": "AUTORIDADE_PUBLICA",
                "triage_info": triage_info,
                "metrics": {
                    "retrieval_time_ms": 0,
                    "llm_time_ms": 0,
                    "total_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": 0,
                    "keywords": extract_query_keywords(query)
                }
            }
        
        # Fallback dinâmico para RAG: se não constar no catálogo estático, busca em vector.db / chunks
        if agent and hasattr(agent, "handlers") and "RAG_HANDLER" in agent.handlers:
            return agent.handlers["RAG_HANDLER"].execute(
                query=query,
                triage_info=triage_info,
                agent=agent,
                conversation_id=conversation_id,
                start_time=start_time,
                history=history
            )

        # Fallback offline se nada for encontrado (usa cópia genérica segura)
        answer = (
            "Não encontrei a autoridade correspondente na base oficial estática do município.\n\n"
            "Se for um cargo em uma secretaria, por favor me informe o nome da secretaria para eu tentar buscar nos documentos gerais."
        )
        agent.log_execution_metrics(query, 0, 0, elapsed, 0, 0, 0)
        return {
            "answer": answer,
            "sources": [],
            "confidence": 0.0,
            "intent_detected": "AUTORIDADE_PUBLICA",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }


class MemoryRecallHandler(BaseHandler):
    """Recupera informações exatas e literais do histórico da conversa a partir do SQLite persistente."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        elapsed = time.time() - start_time
        q_lower = query.lower().strip()
        agent_cls = agent.__class__
        
        # 1. Pergunta sobre a primeira pergunta ("qual foi minha primeira pergunta", etc.)
        is_asking_first = any(p in q_lower for p in ["primeira pergunta", "1ª pergunta", "1a pergunta", "primeira dúvida", "primeira duvida", "perguntei primeiro", "primeiro perguntei", "comecei perguntando", "qual foi a primeira"])
        
        # 2. Pergunta sobre o que respondeu antes / última resposta
        is_asking_last = any(p in q_lower for p in ["respondeu antes", "última resposta", "ultima resposta", "turno anterior", "resposta anterior"])
        
        # 3. Pergunta sobre resumo dos assuntos ("sobre o que estávamos conversando", etc.)
        is_asking_summary = any(p in q_lower for p in ["estávamos conversando", "estavamos conversando", "estamos conversando", "quais assuntos", "quais perguntas"])
        
        # 4. Pergunta sobre um turno numérico específico (ex: "segunda pergunta", "terceira resposta", etc.)
        ordinal_map = {
            "segunda": 2, "2ª": 2, "2a": 2,
            "terceira": 3, "3ª": 3, "3a": 3,
            "quarta": 4, "4ª": 4, "4a": 4,
            "quinta": 5, "5ª": 5, "5a": 5
        }
        specific_turn = None
        for word, t_num in ordinal_map.items():
            if word in q_lower:
                specific_turn = t_num
                break

        ans = ""
        if is_asking_first:
            first_q = agent_cls.get_first_user_question(conversation_id)
            if first_q and first_q.get("question"):
                q_text = first_q["question"]
                t_idx = first_q.get("turn_index", 1)
                ans = (
                    f"Sua primeira pergunta nesta conversa foi:\n\n"
                    f'> **"{q_text}"**\n\n'
                    f"(Registrada no **Turno {t_idx}** desta sessão). "
                    f"Como posso ajudar você a continuar?"
                )
            else:
                ans = "Esta é a sua primeira pergunta nesta conversa! Como posso ajudar você hoje?"
        elif specific_turn:
            turn_data = agent_cls.get_session_turn(conversation_id, specific_turn)
            if turn_data and (turn_data.get("user") or turn_data.get("assistant")):
                u_msg = turn_data.get("user") or ""
                a_msg = turn_data.get("assistant") or ""
                ans = (
                    f"No **Turno {specific_turn}** desta conversa:\n\n"
                    f"• **Sua pergunta foi:** *\"{u_msg}\"*\n"
                    f"• **Minha resposta foi:** {a_msg}\n\n"
                    f"Posso ajudar com mais algum esclarecimento sobre esse tema?"
                )
            else:
                total_turns = len(agent_cls.get_session_all_turns(conversation_id))
                ans = f"Não encontrei o Turno {specific_turn} nesta sessão (até agora temos {total_turns} turnos registrados)."
        elif is_asking_last:
            last_pair = agent_cls.get_last_turn_pair(conversation_id)
            if last_pair and last_pair.get("assistant"):
                ans = (
                    f"Na resposta anterior (Turno {last_pair.get('turn_index')}), quando você perguntou sobre *\"{last_pair.get('user')}\"*, eu informei:\n\n"
                    f"{last_pair.get('assistant')}\n\n"
                    f"Ficou alguma dúvida ou gostaria que eu aprofundasse?"
                )
            else:
                ans = "Ainda não temos interações anteriores registradas nesta sessão."
        elif is_asking_summary:
            all_turns = agent_cls.get_session_all_turns(conversation_id)
            if all_turns:
                linhas = []
                for t in all_turns:
                    u_preview = (t.get("user") or "").strip()
                    if u_preview:
                        if len(u_preview) > 80:
                            u_preview = u_preview[:77] + "..."
                        linhas.append(f"• **Turno {t['turn_index']}:** \"{u_preview}\"")
                ans = (
                    f"Nesta conversa, já tratamos dos seguintes tópicos ({len(all_turns)} turnos):\n\n"
                    + "\n".join(linhas) + "\n\n"
                    f"Sobre qual desses assuntos você gostaria de falar ou deseja iniciar um novo tema?"
                )
            else:
                ans = "Esta sessão ainda não possui tópicos anteriores."
        else:
            first_q = agent_cls.get_first_user_question(conversation_id)
            if first_q:
                ans = f"Sua primeira pergunta nesta conversa foi: **\"{first_q['question']}\"**."
            else:
                ans = "Não localizei mensagens anteriores registradas nesta conversa."

        return {
            "answer": ans,
            "sources": ["telemetry.db/chat_messages"],
            "confidence": 1.0,
            "intent_detected": "MEMORIA_CONVERSACIONAL",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": round(elapsed * 1000, 2),
                "llm_time_ms": 0,
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }


class ClarificationHandler(BaseHandler):
    """Trata pedidos de explicação didática, simplificação ou frustração do cidadão com a resposta anterior."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        elapsed = time.time() - start_time
        agent_cls = agent.__class__
        last_pair = agent_cls.get_last_turn_pair(conversation_id)
        q_lower = query.lower()

        if not last_pair or not last_pair.get("assistant"):
            ans = (
                "Peço desculpas se a minha comunicação não ficou clara! Estou aqui pronto para ajudar você. "
                "Poderia me dizer, de forma simples, qual serviço ou informação de Duque de Caxias você precisa?"
            )
        else:
            prev_user = last_pair.get("user") or ""
            prev_assistant = last_pair.get("assistant") or ""

            if agent.using_real and agent.gemini_client:
                try:
                    sys_instruct = (
                        "Você é o Duque IA, assistente virtual oficial da Prefeitura de Duque de Caxias.\n"
                        "O munícipe não compreendeu a resposta anterior e pediu que você esclareça ou simplifique.\n"
                        "DIRETRIZES OBRIGATÓRIAS:\n"
                        "1. Se o cidadão demonstrou irritação, comece pedindo sinceras desculpas com muita humildade e educação ('Peço sinceras desculpas se a resposta anterior ficou confusa...').\n"
                        "2. Seja extremamente claro, didático e direto ao ponto.\n"
                        "3. Use tópicos curtos (máximo 3 a 4 passos práticos).\n"
                        "4. Evite jargões burocráticos ou frases longas.\n"
                        "5. Conclua perguntando se agora ficou mais simples de entender.\n"
                        "NUNCA encaminhe para a Ouvidoria nem abra protocolo a menos que ele explicitamente solicite registrar manifestação formal."
                    )
                    prompt = (
                        f"Pergunta original do munícipe: \"{prev_user}\"\n"
                        f"Resposta anterior que ele não entendeu: \"{prev_assistant[:600]}\"\n"
                        f"Mensagem atual do munícipe: \"{query}\"\n\n"
                        "Reexplique o assunto de forma simples, prática e acolhedora:"
                    )
                    ans = agent.gemini_client.generate_response(
                        prompt,
                        system_instruction=sys_instruct,
                        model="gemini-3.1-flash-lite",
                        temperature=0.2,
                        max_output_tokens=800
                    ).strip()
                except Exception:
                    ans = (
                        "Peço desculpas se a explicação anterior ficou confusa! "
                        f"Sobre **{prev_user}**, o atendimento é realizado pelos órgãos municipais oficiais de Duque de Caxias. "
                        "Como posso explicar de forma mais simples para ajudar você?"
                    )
            else:
                ans = (
                    "Peço desculpas se a resposta anterior não foi clara! "
                    f"Resumindo de forma direta sobre *\"{prev_user}\"*: o atendimento é realizado pelos canais municipais oficiais. "
                    "Gostaria que eu detalhasse algum ponto específico?"
                )

        return {
            "answer": ans,
            "sources": [],
            "confidence": 0.98,
            "intent_detected": "CLARIFICACAO_RESPOSTA",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": round(elapsed * 1000, 2),
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }


class AIMetaHandler(BaseHandler):
    """Trata perguntas sobre integridade, transparência, limites, confiabilidade e não-invenção de dados pela IA."""
    def execute(self, query: str, triage_info: dict, agent, conversation_id: str, start_time: float, history: list) -> dict:
        elapsed = time.time() - start_time
        
        if agent.using_real and agent.gemini_client:
            try:
                sys_instruct = (
                    "Você é o DUQUE IA, assistente virtual oficial da Prefeitura de Duque de Caxias — RJ.\n"
                    "O munícipe fez uma pergunta sobre seu funcionamento, limites, confiabilidade ou se você inventa informações, protocolos ou telefones para agradá-lo.\n"
                    "DIRETRIZES DE TRANSPARÊNCIA E INTEGRIDADE:\n"
                    "1. Responda com clareza, firmeza institucional e empatia:\n"
                    "   - Afirme categoricamente que você NUNCA inventa informações, números de protocolos ou telefones.\n"
                    "   - Explique que protocolos oficiais de atendimento só existem quando gerados pelos sistemas municipais homologados (como o aplicativo Colab, o portal da Prefeitura ou o atendimento telefônico oficial).\n"
                    "   - Explique que todas as informações que você fornece vêm de fontes oficiais e da Carta de Serviços de Duque de Caxias.\n"
                    "   - Destaque que, quando um dado não consta na base ou há incerteza, seu dever é admitir a limitação com honestidade e orientar o cidadão aos canais oficiais.\n"
                    "2. Forneça os contatos da Ouvidoria Geral como canal oficial e humano:\n"
                    f"   - Telefone: **{OUVIDORIA_CONTACTS['telefone']}**\n"
                    f"   - E-mail: **{OUVIDORIA_CONTACTS['email']}**\n"
                    f"   - Online: aplicativo **Colab** ([{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}))\n"
                    "3. NUNCA mencione nem desvie para secretarias ou institutos aleatórios (como IPMDC ou Fazenda).\n"
                    "4. Mantenha tom caloroso, objetivo e educado (máximo 4 a 5 frases estruturadas)."
                )
                prompt = (
                    f"Pergunta do munícipe: \"{query}\"\n\n"
                    "Gere a resposta de integridade e transparência:"
                )
                ans = agent.gemini_client.generate_response(
                    prompt,
                    system_instruction=sys_instruct,
                    model="gemini-3.1-flash-lite",
                    temperature=0.1,
                    max_output_tokens=800
                ).strip()
            except Exception:
                ans = (
                    "**Não, de forma alguma!** Como assistente virtual oficial da Prefeitura de Duque de Caxias, sigo princípios estritos de integridade, transparência e responsabilidade com o munícipe:\n\n"
                    "• **Não invento protocolos nem encaminhamentos**: Números de protocolo oficiais só existem quando gerados por sistemas municipais homologados (como o aplicativo **Colab** ou a Central da Prefeitura). Eu nunca crio protocolos fictícios nem afirmo que uma solicitação foi encaminhada se isso não ocorreu.\n"
                    "• **Fontes oficiais e verificadas**: Todas as informações fornecidas sobre órgãos, serviços, horários, telefones e endereços são consultadas diretamente da base de dados oficial e da Carta de Serviços ao Cidadão de Duque de Caxias.\n"
                    "• **Não invento para agradar**: Minhas respostas são estritamente factuais. Se uma informação não constar em minha base oficial, informo com total transparência a limitação e oriento você a falar com a equipe humana da **Ouvidoria Geral de Duque de Caxias**:\n"
                    f"  - **Telefone**: {OUVIDORIA_CONTACTS['telefone']}\n"
                    f"  - **E-mail**: {OUVIDORIA_CONTACTS['email']}\n"
                    f"  - **Online**: aplicativo **Colab** ({OUVIDORIA_CONTACTS['colab_url_clean']})\n\n"
                    "Meu compromisso é fornecer um atendimento factual, seguro e 100% transparente para a nossa cidade."
                )
        else:
            ans = (
                "**Não, de forma alguma!** Como assistente virtual oficial da Prefeitura de Duque de Caxias, sigo princípios estritos de integridade, transparência e responsabilidade com o munícipe:\n\n"
                "• **Não invento protocolos nem encaminhamentos**: Números de protocolo oficiais só existem quando gerados por sistemas municipais homologados (como o aplicativo **Colab** ou a Central da Prefeitura). Eu nunca crio protocolos fictícios nem afirmo que uma solicitação foi encaminhada se isso não ocorreu.\n"
                "• **Fontes oficiais e verificadas**: Todas as informações fornecidas sobre órgãos, serviços, horários, telefones e endereços são consultadas diretamente da base de dados oficial e da Carta de Serviços ao Cidadão de Duque de Caxias.\n"
                "• **Não invento para agradar**: Minhas respostas são estritamente factuais. Se uma informação não constar em minha base oficial, informo com total transparência a limitação e oriento você a falar com a equipe humana da **Ouvidoria Geral de Duque de Caxias**:\n"
                f"  - **Telefone**: {OUVIDORIA_CONTACTS['telefone']}\n"
                f"  - **E-mail**: {OUVIDORIA_CONTACTS['email']}\n"
                f"  - **Online**: aplicativo **Colab** ({OUVIDORIA_CONTACTS['colab_url_clean']})\n\n"
                "Meu compromisso é fornecer um atendimento factual, seguro e 100% transparente para a nossa cidade."
            )

        return {
            "answer": ans,
            "sources": ["Diretrizes de Integridade e Transparência do Duque IA"],
            "confidence": 1.0,
            "intent_detected": "ai_meta_info",
            "triage_info": triage_info,
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": round(elapsed * 1000, 2),
                "total_time_ms": round(elapsed * 1000, 2),
                "tokens_used": 0,
                "keywords": extract_query_keywords(query)
            }
        }
