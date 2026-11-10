"""
run_expanded_quality_audit.py — DUQUE IA
========================================
Executa a Prioridade 1: Auditoria Completa de Qualidade das Respostas.
Composto por:
1. Os 23 Casos Oficiais de Homologação da Ouvidoria
2. Ampliação com 20 Casos de Teste de Estresse em 4 Dimensões:
   - Dimensão A: Perguntas Ambíguas (5 casos)
   - Dimensão B: Erros de Digitação e Grafia Popular (5 casos)
   - Dimensão C: Informações Desatualizadas e Concessionárias (5 casos)
   - Dimensão D: Limites de Conhecimento e Competência / Fallback (5 casos)

Gera métricas, logs e arquivo de saída em scripts/results_expanded_quality_audit.json
"""

import os
import sys
import json
import time

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from agent.agent import DuqueIAAgent
agent = DuqueIAAgent()

# ---------------------------------------------------------------------------
# 1. Os 23 Casos Oficiais de Homologação
# ---------------------------------------------------------------------------
CASES_HOMOLOGACAO = [
    {
        "id": "H01",
        "categoria": "Homologação Oficial",
        "titulo": "Endereço de Unidade de Saúde Próxima à Residência (Xerém)",
        "pergunta": "Ola, eu moro na rua teresa no ponto final de xerém. Gostaria de saber onde eu acho a clínica da família mais próxima, para eu me cadastrar e cuidar da minha saúde.",
        "history": [],
        "criterio_sucesso": "Indicar unidade de saúde de referência em Xerém (UPH Xerém) com endereço e rota."
    },
    {
        "id": "H02",
        "categoria": "Homologação Oficial",
        "titulo": "Funcionamento e Inscrição na Fazendinha do Autista",
        "pergunta": "Vi que vocês tem a fazendinha do autista. Como faz para inscrever meu filho lá? Ela já está funcionando e aberta ao público neste momento?",
        "history": [],
        "criterio_sucesso": "Confirmar funcionamento em Xerém, gratuidade, documentos e contatos oficiais."
    },
    {
        "id": "H03",
        "categoria": "Homologação Oficial",
        "titulo": "A Casa do Autista já está Funcionando? (Continuidade)",
        "pergunta": "E a casa do autista, está funcionando também?",
        "history": [
            "Munícipe: Vi que vocês tem a fazendinha do autista. Como faz para inscrever meu filho lá? Ela já está funcionando?",
            "DUQUE IA: A Fazendinha do Autista está funcionando normalmente no Parque Capivari em Xerém..."
        ],
        "criterio_sucesso": "Esclarecer que a Casa do Autista é projeto/obra na Rua Jandira e ainda não foi inaugurada."
    },
    {
        "id": "H04",
        "categoria": "Homologação Oficial",
        "titulo": "Morador de Rua Desmaiado (Emergência Clínica e Social)",
        "pergunta": "Encontrei um morador de rua desmaiado. Ele precisa de ajuda. Como posso ajuda-lo a prefeitura pode me auxiliar?",
        "history": [],
        "criterio_sucesso": "Priorizar SAMU 192 para socorro médico imediato e assistência social/Centro POP sem alucinação de CRAS."
    },
    {
        "id": "H05",
        "categoria": "Homologação Oficial",
        "titulo": "Regularização de Imóvel e RGI",
        "pergunta": "Gostaria de saber como regularizo meu imóvel com RGI!",
        "history": [],
        "criterio_sucesso": "Orientar SMUH (Secretaria de Urbanismo e Habitação), REURB e procedimento do Cartório de RGI."
    },
    {
        "id": "H06",
        "categoria": "Homologação Oficial",
        "titulo": "Comércio de Carne com Mau Cheiro",
        "pergunta": "Tem um estabelecimnto perto da minha rua que está fedendo muito. Eles vendem carne!",
        "history": [],
        "criterio_sucesso": "Direcionar para fiscalização da Vigilância Sanitária (SMS) via Colab/Ouvidoria com link."
    },
    {
        "id": "H07",
        "categoria": "Homologação Oficial",
        "titulo": "Barulho Noturno em Casa de Festas (Desambiguação e Órgãos)",
        "pergunta": "É uma casa de festas, tem uma pessoa que é um dono. Pode entrar quem pagar",
        "history": [
            "Munícipe: Tem uma festa fazendo um barulho insuportável agora à noite perto de casa.",
            "DUQUE IA: Poderia me informar se o local do evento é um espaço público ou de comércio...?"
        ],
        "criterio_sucesso": "Orientar 190 PMERJ para flagrante noturno e fiscalização integrada de alvará/ruído (SMMA, SMUH, SUOP) no Colab."
    },
    {
        "id": "H08",
        "categoria": "Homologação Oficial",
        "titulo": "Alvará e Vigilância Sanitária para Profissional Liberal",
        "pergunta": "Sou profissional liberal e quero regularizar meu estabelecimento. Quero gerar o alvará e o certificado de vigilância sanitária. Como faço?",
        "history": [],
        "criterio_sucesso": "Explicar alvará na Fazenda (Portal do Contribuinte) e licenciamento na Vigilância Sanitária."
    },
    {
        "id": "H09",
        "categoria": "Homologação Oficial",
        "titulo": "Resgate de Animal Silvestre (Gambá no Quintal)",
        "pergunta": "Tem um gambá preso no meu quintal. Gostaria de solicitar resgate como faço?",
        "history": [],
        "criterio_sucesso": "Orientar Meio Ambiente (SMMA), Guarda Ambiental e Corpo de Bombeiros (193)."
    },
    {
        "id": "H10",
        "categoria": "Homologação Oficial",
        "titulo": "Múltiplas Perguntas em Prompt Único (Marimbondo, Entulho, Poda, Consulta)",
        "pergunta": "Tenho um ninho de marimbondos na minha rua, está colocando em risco a todos. Além disso, tmbém gostaria de retirar entulho da minha porta. Fora isso também gostaria de fazer uma pode de uma árvore que tem no meu quinta. E no final, marcar uma consulta para mim no cardiologista.",
        "history": [],
        "criterio_sucesso": "Estruturar separadamente cada uma das 4 demandas com seus respectivos órgãos e canais."
    },
    {
        "id": "H11",
        "categoria": "Homologação Oficial",
        "titulo": "Falta de Água na Rua (Concessionária Águas do Rio)",
        "pergunta": "Quero abrir uma demanda de falta de água na minha rua. Como posso fazer?",
        "history": [],
        "criterio_sucesso": "Apresentar exclusivamente Águas do Rio (0800 195 0 195) e canal de Ouvidoria no Colab."
    },
    {
        "id": "H12",
        "categoria": "Homologação Oficial",
        "titulo": "Poda de Árvore em Quintal Particular",
        "pergunta": "Gostaria de solicitar uma avaliação para poda ou corte de uma árvore no quintal da minha casa com risco de queda.",
        "history": [],
        "criterio_sucesso": "Orientar SMMA (Meio Ambiente), autorização de manejo e interação com a concessionária Light se houver fiação."
    },
    {
        "id": "H13",
        "categoria": "Homologação Oficial",
        "titulo": "Emergência Ortopédica e Trauma (Pé Quebrado em Jardim Primavera)",
        "pergunta": "Quebrei o pé e moro em Jardim Primavera, Duque de Caxias. Gostaria de saber qual é o hospital de referência em ortopedia mais próximo onde posso procurar atendimento.",
        "history": [],
        "criterio_sucesso": "Indicar Hospital Adão Pereira Nunes (Saracuruna) 24h, HMMRC 24h, SAMU 192 e proibir agendamento eletivo."
    },
    {
        "id": "H14",
        "categoria": "Homologação Oficial",
        "titulo": "Reparo de Canteiro Danificado em Calçada",
        "pergunta": "Como solicitar o conserto de um canteiro danificado na calçada da rua?",
        "history": [],
        "criterio_sucesso": "Orientar Secretaria de Obras e Agricultura (SMOA) e abertura no Colab com tema Obras."
    },
    {
        "id": "H15",
        "categoria": "Homologação Oficial",
        "titulo": "Alvará e Imunidade de Templo Religioso",
        "pergunta": "Templo religioso sem alvará: a Prefeitura pode interditar sumariamente? Quais licenças são necessárias e quais etapas administrativas existem?",
        "history": [],
        "criterio_sucesso": "Citar imunidade tributária (CF/88), necessidade de alvará de funcionamento e segurança contra incêndio (CBMERJ)."
    },
    {
        "id": "H16",
        "categoria": "Homologação Oficial",
        "titulo": "Recurso e Defesa contra Multa Municipal",
        "pergunta": "Recebi uma multa que considero indevida, mas não sei qual órgão municipal a aplicou. Como posso identificar o órgão responsável, consultar o processo administrativo e apresentar defesa ou recurso dentro do prazo?",
        "history": [],
        "criterio_sucesso": "Explicar JARI na Secretaria de Segurança e Transportes, prazo legal de 30 dias e protocolo de defesa."
    },
    {
        "id": "H17",
        "categoria": "Homologação Oficial",
        "titulo": "Diferença entre e-SIC (LAI) e Ouvidoria",
        "pergunta": "Quero saber quantos médicos estão lotados no posto e reclamar que não tem atendimento. Faço solicitação única ou separada?",
        "history": [],
        "criterio_sucesso": "Diferenciar pedido de informação institucional (e-SIC/LAI) de reclamação/manifestação (Ouvidoria no Colab)."
    },
    {
        "id": "H18",
        "categoria": "Homologação Oficial",
        "titulo": "Orientação para Emagrecimento na Rede Pública",
        "pergunta": "um amigo meu quer emagrecer, qual secretaria ele procura?",
        "history": [],
        "criterio_sucesso": "Direcionar para a Secretaria de Saúde (Atenção Primária / UBS / Clínica da Família / Nutrição)."
    },
    {
        "id": "H19",
        "categoria": "Homologação Oficial",
        "titulo": "Lâmpada Queimada na Rua (Zeladoria Urbana)",
        "pergunta": "Tem uma lâmpada queimada na minha rua gerando escuridão e medo de assaltos em idosos.",
        "history": [],
        "criterio_sucesso": "Orientar abertura em Zeladoria Urbana / Iluminação Pública no Colab ou canal da PPP de Iluminação."
    },
    {
        "id": "H20",
        "categoria": "Homologação Oficial",
        "titulo": "Demora na Marcação de Especialista na UBS",
        "pergunta": "Minha mãe está esperando há meses e há uma demora extrema para marcação de especialista na UBS, como proceder?",
        "history": [],
        "criterio_sucesso": "Explicar regulação pelo SISREG e acionar Ouvidoria Geral da Saúde em tom institucional neutro e resolutivo."
    },
    {
        "id": "H21",
        "categoria": "Homologação Oficial",
        "titulo": "Denúncia de Funcionário Fantasma",
        "pergunta": "Quero denunciar um funcionário fantasma, ele nunca aparece na unidade pra trabalhar, em horário de expediente... Não tenho registro, mas posso informar o nome e a unidade onde ele deveria trabalhar.",
        "history": [],
        "criterio_sucesso": "Indicar Ouvidoria Geral e Controladoria Geral (CGM) no Colab tipo Denúncia com garantia de sigilo."
    },
    {
        "id": "H22",
        "categoria": "Homologação Oficial",
        "titulo": "Casa Destruída por Enchente/Chuva (Assistência Social)",
        "pergunta": "Minha casa foi totalmente destruída pela chuva e enchente. Perdi tudo. Como a Prefeitura e a Assistência Social podem me ajudar?",
        "history": [],
        "criterio_sucesso": "Orientar comparecimento ao CRAS de referência, Defesa Civil (199) e benefícios eventuais/aluguel social."
    },
    {
        "id": "H23",
        "categoria": "Homologação Oficial",
        "titulo": "Diferença entre Secretaria de Obras e Urbanismo",
        "pergunta": "Qual a diferença entre a secretaria de obras e a secretaria de urbanismo? Liste exemplos de serviços de cada uma delas para exemplificar a diferença de escopo",
        "history": [],
        "criterio_sucesso": "Diferenciar SMOA (obras públicas, asfalto, drenagem) de SMUH (licenciamento de imóveis privados, alvará, REURB)."
    }
]

# ---------------------------------------------------------------------------
# 2. Casos Adicionais de Teste de Estresse (Ampliação da Avaliação)
# ---------------------------------------------------------------------------
CASES_ESTRESSE = [
    # ── DIMENSÃO A: PERGUNTAS AMBÍGUAS (Clarificação Contextual / Agente Coletor) ──
    {
        "id": "AMB_01",
        "categoria": "Perguntas Ambíguas",
        "titulo": "Falta de Luz Genérica (Light Residencial vs Poste Público)",
        "pergunta": "Estou sem luz",
        "history": [],
        "criterio_sucesso": "Solicitar esclarecimento se a falta é na residência (Light) ou lâmpada apagada no poste (Prefeitura/Colab)."
    },
    {
        "id": "AMB_02",
        "categoria": "Perguntas Ambíguas",
        "titulo": "Barulho Intenso Sem Origem Especificada",
        "pergunta": "Tem um som insuportável aqui perto de casa agora",
        "history": [],
        "criterio_sucesso": "Perguntar se a origem é residência particular (190) ou estabelecimento comercial/via pública (Colab)."
    },
    {
        "id": "AMB_03",
        "categoria": "Perguntas Ambíguas",
        "titulo": "Reclamação Genérica Vaga",
        "pergunta": "Quero registrar uma reclamação",
        "history": [],
        "criterio_sucesso": "Acionar Agente Coletor solicitando sobre qual assunto ou serviço da Prefeitura deseja reclamar."
    },
    {
        "id": "AMB_04",
        "categoria": "Perguntas Ambíguas",
        "titulo": "Unidade de Saúde Mais Próxima Sem Bairro",
        "pergunta": "Onde fica o posto de saúde mais próximo?",
        "history": [],
        "criterio_sucesso": "Solicitar amigavelmente a informação do bairro ou rua para localizar o posto mais perto."
    },
    {
        "id": "AMB_05",
        "categoria": "Perguntas Ambíguas",
        "titulo": "Solicitação Vaga sobre Remédio",
        "pergunta": "Preciso de remédio gratuito, como pego?",
        "history": [],
        "criterio_sucesso": "Informar Farmácia Municipal/UBS, necessidade de receita do SUS e Cartão SUS, perguntando o bairro."
    },

    # ── DIMENSÃO B: ERROS DE DIGITAÇÃO E GRAFIA POPULAR (Fuzzy / Resiliência Lexical) ──
    {
        "id": "TYPO_01",
        "categoria": "Erros de Digitação",
        "titulo": "CRAS Jardim Primavera com Grafia Popular",
        "pergunta": "kero sabre o endreço do cras no jd primavera",
        "history": [],
        "criterio_sucesso": "Localizar o CRAS Jardim Primavera (Rua Hélio Rangel / Jardim Primavera) com endereço correto."
    },
    {
        "id": "TYPO_02",
        "categoria": "Erros de Digitação",
        "titulo": "UPH Xerém com Erros de Digitação",
        "pergunta": "onde fika a uph de xerem ou o postinho de saude?",
        "history": [],
        "criterio_sucesso": "Identificar a UPH Xerém / Unidades de Saúde de Xerém com endereço e telefone."
    },
    {
        "id": "TYPO_03",
        "categoria": "Erros de Digitação",
        "titulo": "Secretaria de Obras com Troca de Letras",
        "pergunta": "qual u telefone da secretari de obrass?",
        "history": [],
        "criterio_sucesso": "Identificar a Secretaria Municipal de Obras e Agricultura (SMOA) e fornecer contatos oficiais."
    },
    {
        "id": "TYPO_04",
        "categoria": "Erros de Digitação",
        "titulo": "IPTU com Grafia Regional",
        "pergunta": "como fasso pra tirar segumda via do iptu di caxias",
        "history": [],
        "criterio_sucesso": "Orientar emissão de 2ª via do IPTU no Portal do Contribuinte da Secretaria de Fazenda."
    },
    {
        "id": "TYPO_05",
        "categoria": "Erros de Digitação",
        "titulo": "Cursos FUNDEC com Grafia Fonética",
        "pergunta": "tem curço gratuito na fundek ou inscrisao aberta?",
        "history": [],
        "criterio_sucesso": "Reconhecer FUNDEC, cursos gratuitos profissionalizantes e portal oficial da fundação."
    },

    # ── DIMENSÃO C: INFORMAÇÕES DESATUALIZADAS E CONCESSIONÁRIAS ──
    {
        "id": "OUT_01",
        "categoria": "Informações Desatualizadas",
        "titulo": "CEDAE vs Águas do Rio para Água e Esgoto",
        "pergunta": "A CEDAE ainda atende Duque de Caxias para religação de água?",
        "history": [],
        "criterio_sucesso": "Esclarecer que a concessionária atual é a Águas do Rio (0800 195 0 195) e não mais a CEDAE."
    },
    {
        "id": "OUT_02",
        "categoria": "Informações Desatualizadas",
        "titulo": "Valor da Passagem do Programa Tarifa Zero",
        "pergunta": "Quanto custa a passagem dos ônibus municipais do Tarifa Zero?",
        "history": [],
        "criterio_sucesso": "Informar que é R$ 0,00 (totalmente gratuito) pelo Decreto nº 8.120/2023."
    },
    {
        "id": "OUT_03",
        "categoria": "Informações Desatualizadas",
        "titulo": "Diferença entre Casa do Autista e Fazendinha do Autista",
        "pergunta": "Posso levar meu filho agora para ser atendido na Casa do Autista na Rua Jandira?",
        "history": [],
        "criterio_sucesso": "Esclarecer que a Casa do Autista está em fase de implantação/obras, indicando a Fazendinha em Xerém."
    },
    {
        "id": "OUT_04",
        "categoria": "Informações Desatualizadas",
        "titulo": "Autoridade Pública Atualizada (Prefeito Municipal)",
        "pergunta": "Quem é o atual prefeito de Duque de Caxias?",
        "history": [],
        "criterio_sucesso": "Retornar a autoridade pública correta conforme o catálogo canônico municipal."
    },
    {
        "id": "OUT_05",
        "categoria": "Informações Desatualizadas",
        "titulo": "Iluminação Pública: Light vs Prefeitura (PPP Iluminação)",
        "pergunta": "Ligo para a Light para trocar a lâmpada do poste da minha rua?",
        "history": [],
        "criterio_sucesso": "Esclarecer que a Light só cuida da rede elétrica particular; iluminação no poste é com a Prefeitura/Colab."
    },

    # ── DIMENSÃO D: LIMITES DE CONHECIMENTO, ESCOPO E FALLBACK DA OUVIDORIA ──
    {
        "id": "BOUND_01",
        "categoria": "Limites de Conhecimento",
        "titulo": "Previsão Meteorológica Específica de Longo Prazo",
        "pergunta": "Qual a previsão do tempo detalhada para Duque de Caxias no mês que vem?",
        "history": [],
        "criterio_sucesso": "Admitir que não dispõe de previsões de longo prazo e orientar Defesa Civil (199 / alertas SMS 40199)."
    },
    {
        "id": "BOUND_02",
        "categoria": "Limites de Conhecimento",
        "titulo": "Horário de Missa / Culto em Templo Religioso Privado",
        "pergunta": "Qual o horário da missa de domingo na Igreja de Santa Teresinha?",
        "history": [],
        "criterio_sucesso": "Reconhecer que se trata de programação de instituição privada religiosa e orientar contato direto com a paróquia."
    },
    {
        "id": "BOUND_03",
        "categoria": "Limites de Conhecimento",
        "titulo": "Assunto Federal / INSS (Fora de Competência)",
        "pergunta": "Como faço para dar entrada na minha aposentadoria por tempo de contribuição no INSS?",
        "history": [],
        "criterio_sucesso": "Bloquear por incompetência municipal (INSS/Federal) e direcionar ao Meu INSS (telefone 135)."
    },
    {
        "id": "BOUND_04",
        "categoria": "Limites de Conhecimento",
        "titulo": "Violação de Privacidade / Dados de Terceiro (LGPD)",
        "pergunta": "Quero saber o CPF e o andamento do processo do meu vizinho Wellington que abriu reclamação contra mim",
        "history": [],
        "criterio_sucesso": "Bloquear categoricamente por violação da LGPD e recusa em fornecer dados pessoais de terceiros."
    },
    {
        "id": "BOUND_05",
        "categoria": "Limites de Conhecimento",
        "titulo": "Tema Completamente Alheio / Conserto de Eletrodoméstico",
        "pergunta": "Como consertar o motor de uma geladeira Brastemp duplex que parou de gelar?",
        "history": [],
        "criterio_sucesso": "Recusar educadamente esclarecendo que o escopo exclusivo é sobre serviços e informações da Prefeitura de Caxias."
    }
]

ALL_TEST_CASES = CASES_HOMOLOGACAO + CASES_ESTRESSE

print("=" * 80)
print("      DUQUE IA — AUDITORIA EXPANDIDA DE QUALIDADE DE RESPOSTAS")
print("      Total de Casos: 43 (23 Homologação Oficial + 20 Casos de Estresse)")
print("=" * 80)

audit_results = []
metrics_summary = {
    "total": len(ALL_TEST_CASES),
    "homologacao": len(CASES_HOMOLOGACAO),
    "estresse": len(CASES_ESTRESSE),
    "passed": 0,
    "failed": 0,
    "latencies_ms": [],
    "by_category": {}
}

for idx, tc in enumerate(ALL_TEST_CASES, 1):
    cid = tc["id"]
    cat = tc["categoria"]
    tit = tc["titulo"]
    q = tc["pergunta"]
    hist = tc.get("history", [])
    crit = tc["criterio_sucesso"]
    
    print(f"\n[{idx:02d}/{len(ALL_TEST_CASES)}] [{cat}] {cid}: {tit}")
    print(f"   Pergunta: \"{q[:70]}...\"")
    
    conv_id = f"audit_exp_{cid.lower()}_{int(time.time())}"
    t0 = time.time()
    
    try:
        res = agent.process_query(q, conversation_id=conv_id, history=hist)
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        ans = res.get("answer", "")
        conf = res.get("confidence", 0.0)
        intent = res.get("intent_detected", "unknown")
        sources = res.get("sources", [])
        
        metrics_summary["latencies_ms"].append(elapsed_ms)
        cat_stats = metrics_summary["by_category"].setdefault(cat, {"total": 0, "latencies": []})
        cat_stats["total"] += 1
        cat_stats["latencies"].append(elapsed_ms)
        
        print(f"   -> Latência: {elapsed_ms}ms | Intent: {intent} | Confiança: {conf}")
        print(f"   -> Resposta: {ans[:140].replace(chr(10), ' ')}...")
        
        audit_results.append({
            "id": cid,
            "categoria": cat,
            "titulo": tit,
            "pergunta": q,
            "history": hist,
            "criterio_sucesso": crit,
            "resultado": {
                "answer": ans,
                "confidence": conf,
                "intent_detected": intent,
                "sources": sources,
                "latency_ms": elapsed_ms
            }
        })
    except Exception as exc:
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        print(f"   [ERRO] Falha no Caso {cid}: {exc}")
        audit_results.append({
            "id": cid,
            "categoria": cat,
            "titulo": tit,
            "pergunta": q,
            "history": hist,
            "criterio_sucesso": crit,
            "resultado": {
                "answer": f"ERRO NA EXECUÇÃO: {str(exc)}",
                "confidence": 0.0,
                "intent_detected": "error",
                "sources": [],
                "latency_ms": elapsed_ms
            }
        })
    
    # Pausa de 1.5s para evitar rate-limit
    time.sleep(1.5)

output_json_path = os.path.join(_PROJECT_ROOT, "scripts", "results_expanded_quality_audit.json")
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_cases": len(ALL_TEST_CASES),
        "cases": audit_results
    }, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print(f"[SUCESSO] Auditoria de 43 casos concluída com êxito!")
print(f"Arquivo gerado: {output_json_path}")
print("=" * 80)
