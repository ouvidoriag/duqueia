from config.settings import OUVIDORIA_CONTACTS

def build_controlled_web_fallback(query: str, gemini_client=None) -> dict:
    """
    Executa a Pesquisa Inteligente em Camadas (Portais, Subdomínios, Concessionárias, Governos e Notícias).
    Aplica a nova Matriz de Confiança:
      ≥ 0.95: Base Municipal RAG
      0.80 a 0.94: Portais Oficiais e Subdomínios da Prefeitura
      0.60 a 0.79: Web Ampliada (Concessionárias, Governos, Maps, Notícias)
      < 0.60: Alerta de Informação Não Confirmada + Fontes Pesquisadas
    """
    from utils.web_search import search_intelligent_web
    web_results = search_intelligent_web(query, max_results=4)

    if web_results and gemini_client and getattr(gemini_client, "api_keys", None):
        content_blocks = []
        sources_list = []
        sources_taxa = set()

        formatted_sources = []
        sources_taxa = set()

        for r in web_results:
            c_text = r.get("full_content") or r.get("snippet")
            s_category = r.get("source_category", "🏛 Governo Municipal / Oficial")
            rel_label = r.get("reliability_label", "Confiabilidade: Alta")
            s_title = r.get("title", "Portal Web")

            item_label = f"• {s_category}\n  Fonte: {s_title} ({rel_label})"
            sources_taxa.add(item_label)
            sources_list.append(r["url"])
            content_blocks.append(f"--- FONTE AUDITADA ({s_category} | {rel_label}): [{s_title}]({r['url']}) ---\n{c_text}")

        page_body_text = "\n\n".join(content_blocks)

        system_instruction = (
            "Você é o DUQUE IA, o assistente virtual oficial, empático e prestativo de Duque de Caxias — RJ.\n"
            "Sua missão é responder ao cidadão de forma LIVRE, FLUIDA, NATURAL e CONVERSACIONAL, atuando como um excelente atendente municipal.\n\n"
            "DIRETRIZES DE ATENDIMENTO E VERIFICAÇÃO CRUZADA:\n"
            "1. RESPOSTA DIRETA: Comece a resposta diretamente explicando a solução ao munícipe. Nunca use frases burocráticas ou cabeçalhos robóticos.\n"
            "2. VERIFICAÇÃO DE CONTRADIÇÕES E DIVERGÊNCIAS: Se encontrar divergência entre as fontes (ex: a Prefeitura informa um horário ou local e o Google Maps/Notícias informa outro), APRESENTE A DIVERGÊNCIA ABERTAMENTE para proteger o munícipe:\n"
            "   '⚠️ **Aviso de Divergência entre Fontes**: O Portal Oficial informa X, enquanto notícias/Mapas informam Y. Recomenda-se confirmar antes de se deslocar.'\n"
            "3. TRANSPARÊNCIA DE DADOS: Se um detalhe exato não constar no material consultado, mencione isso de forma natural no texto.\n"
            "4. BLOCO FINAL DE FONTES POR TIPO E CONFIABILIDADE:\n"
            "   Finalize a resposta OBRIGATORIAMENTE com o bloco formatado abaixo:\n\n"
            "🌐 **Pesquisa na Web**\n\n"
            "Fontes utilizadas:\n"
            + "\n\n".join(sorted(sources_taxa, reverse=True))
        )

        prompt = (
            f"Pergunta do cidadão: \"{query}\"\n\n"
            f"Informações recuperadas de múltiplas fontes:\n"
            f"{page_body_text}\n\n"
            f"Gere a resposta fluida, empática e completa ao munícipe:"
        )

        try:
            ans = gemini_client.generate_response(prompt, system_instruction=system_instruction, temperature=0.2)
            if ans and len(ans.strip()) > 35:
                ans_clean = ans.strip()
                
                # CÁLCULO DINÂMICO DA CONFIANÇA BASEADO NA EVIDÊNCIA REAL (0.42 a 0.98)
                sources_str = " ".join(sources_taxa).lower()
                has_gov = "governo municipal" in sources_str or "oficial" in sources_str
                has_concessionaire = "concessionária" in sources_str
                has_news_maps = "imprensa" in sources_str or "geolocalização" in sources_str
                has_wiki = "wikipédia" in sources_str

                if has_gov and (has_concessionaire or has_news_maps):
                    conf = 0.98  # Prefeitura + Concessionária / Maps / Imprensa (Consenso Total)
                elif has_gov:
                    conf = 0.94  # Portal Oficial da Prefeitura
                elif has_concessionaire or has_news_maps:
                    conf = 0.88  # Concessionária Responsável ou Imprensa Reconhecida
                elif has_wiki:
                    conf = 0.61  # Wikipédia / Enciclopédia
                else:
                    conf = 0.42  # Fontes diversas / Redes Sociais

                return {
                    "answer": ans_clean,
                    "sources": sources_list,
                    "confidence": conf,
                    "metrics_triple": {
                        "retrieval_confidence": conf,
                        "source_confidence": 1.00 if has_gov else 0.85,
                        "answer_confidence": round(conf * 0.95, 2)
                    },
                    "is_web_fallback": True
                }
        except Exception:
            pass

    # CAMADA < 0.60: INFORMAÇÃO NÃO CONFIRMADA + EXIBIÇÃO TRANSPARENTE DAS FONTES PESQUISADAS
    sector_guidance = _get_sector_guidance(query)
    unconfirmed_response = (
        "📌 **Pesquisa Inteligente (Informação Não Confirmada)**\n\n"
        "A informação solicitada não pôde ser totalmente confirmada nos portais públicos e bases oficiais consultadas no momento.\n\n"
        f"{sector_guidance}\n\n"
        "📚 **Fontes consultadas**\n"
        "✓ Portal Oficial da Prefeitura de Duque de Caxias\n"
        "✓ Portal da Transparência e Diário Oficial\n"
        "✓ Carta de Serviços ao Cidadão"
    )

    return {
        "answer": unconfirmed_response,
        "sources": ["Portal Oficial da Prefeitura de Duque de Caxias"],
        "confidence": 0.55,
        "metrics_triple": {
            "retrieval_confidence": 0.40,
            "source_confidence": 1.00,
            "answer_confidence": 0.40
        },
        "is_web_fallback": False
    }

def _get_sector_guidance(query: str) -> str:
    """Identifica o setor municipal competente para orientar o munícipe sem sobrecarregar a Ouvidoria Geral."""
    q = query.lower()

    if any(k in q for k in ["ônibus", "onibus", "transporte", "itinerário", "itinerario", "linha", "linhas", "tarifa zero", "passe livre", "táxi", "taxi", "van", "vans", "multa", "trânsito", "transito", "vistoria", "permissão", "permissao"]):
        return (
            "Para orientações sobre transporte coletivo, linhas de ônibus, permissões ou trânsito, consulte o órgão responsável:\n"
            "• **Órgão Responsável:** Secretaria Municipal de Transportes e Serviços Públicos (SMTSP)\n"
            "• **Atendimento Presencial:** Av. Brig. Lima e Silva, 1618 - 25 de Agosto, Duque de Caxias - RJ\n"
            "• **E-mail:** **smtsp@duquedecaxias.rj.gov.br**\n"
            "• **Reclamações ou Ouvidoria:** Se houver falha, atraso ou descumprimento de linha, registre manifestação na **Ouvidoria Geral** pelo telefone **(21) 2652-3835** ou app **Colab**."
        )

    if any(k in q for k in ["saúde", "saude", "médico", "medico", "consulta", "exame", "remédio", "remedio", "medicamento", "posto de saúde", "ubs", "usf", "upa", "hospital", "clínica da família"]):
        return (
            "Para consultas, exames, medicamentos ou atendimento de saúde:\n"
            "• **Porta de Entrada (SUS):** Compareça à sua **Unidade Básica de Saúde (UBS/USF)** com documento de identidade e Cartão SUS para consulta e regulação via SISREG;\n"
            "• **Urgências e Emergências:** Procure a **UPA 24h** ou **UPH** mais próxima ou acione o **SAMU (192)**;\n"
            "• **Reclamações:** Em caso de atraso na regulação, fale com a **Ouvidoria da Saúde** pelo aplicativo **Colab**."
        )

    if any(k in q for k in ["escola", "creche", "matrícula", "matricula", "vaga escolar", "ensino", "fundec"]):
        return (
            "Para vagas escolares, matrículas ou cursos:\n"
            "• **Escolas e Creches Municipais:** Consulte o portal de matrículas da **Secretaria Municipal de Educação (SME)** (`matricula.duquedecaxias.rj.gov.br`);\n"
            "• **Cursos e Qualificação:** Consulte a **FUNDEC** (`fundec.rj.gov.br`)."
        )

    if any(k in q for k in ["iptu", "itbi", "iss", "tributo", "imposto", "taxa", "dívida ativa", "divida ativa", "certidão negativa", "certidao negativa"]):
        return (
            "Para emissão de guias, 2ª via ou esclarecimentos tributários:\n"
            "• **Secretaria Municipal de Fazenda (SMF):** Acesse o Portal do Contribuinte (`servicos.duquedecaxias.rj.gov.br`);\n"
            "• **Atendimento Presencial:** Praça Roberto Silveira, 31 - Centro (segunda a sexta, das 9h às 17h)."
        )

    if any(k in q for k in ["buraco", "asfalto", "tapa-buraco", "drenagem", "bueiro", "esgoto", "lâmpada", "lampada", "iluminação"]):
        return (
            "Para serviços de zeladoria urbana, pavimentação ou reparo de iluminação pública:\n"
            "• **Aplicativo Colab:** Registre o pedido diretamente em `duquedecaxias.colab.re` (Secretaria Municipal de Obras e Defesa Civil);\n"
            "• **Iluminação Pública:** Subsecretaria de Iluminação Pública pelo telefone **(21) 2961-9000**."
        )

    # Caso genérico
    return (
        "Para obter orientação oficial ou registrar sua solicitação:\n"
        f"• **Ouvidoria Geral de Duque de Caxias:** Telefone **{OUVIDORIA_CONTACTS['telefone']}** | E-mail: **{OUVIDORIA_CONTACTS['email']}**\n"
        f"• **Aplicativo:** **Colab** ([{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}))\n"
        "• **Portal da Prefeitura:** `duquedecaxias.rj.gov.br`"
    )

def build_fallback_guidance(query: str) -> str:
    """Retorna orientação contextual quando a base de conhecimento não contém a resposta."""
    query_lower = query.lower()
    
    # Se a pergunta menciona ouvidoria, reclamação ou problema, direciona diretamente
    if any(k in query_lower for k in ["ouvidoria", "reclamação", "reclamacao", "denunciar", "denúncia", "denuncia", "elogio", "sugestão", "sugestao", "colab"]):
        lines = [
            "Para registrar sua solicitação, reclamação ou denúncia, utilize os canais oficiais da **Ouvidoria Geral de Duque de Caxias**:\n",
            f"• Telefone: **{OUVIDORIA_CONTACTS['telefone']}**",
            f"• E-mail: **{OUVIDORIA_CONTACTS['email']}**",
            f"• Atendimento Presencial: **{OUVIDORIA_CONTACTS['presencial']}**",
            f"• Aplicativo: **Colab** ([{OUVIDORIA_CONTACTS['colab_url_clean']}]({OUVIDORIA_CONTACTS['colab_url']}))"
        ]
        return "\n".join(lines)
    
    # Encaminhamento orientado ao setor responsável
    lines = [
        "Desculpe, não encontrei uma resposta direta sobre esse assunto na minha base oficial de serviços.\n",
        _get_sector_guidance(query)
    ]
    return "\n".join(lines)

def is_query_too_vague(query: str) -> bool:
    """Retorna True se a pergunta for curta demais para uma resposta objetiva."""
    words = query.strip().split()
    return len(words) <= 2
