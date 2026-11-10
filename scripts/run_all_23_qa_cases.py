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

CASES_CONFIG = [
    {
        "id": 1,
        "titulo": "Endereço do Equipamento de Saúde Próximo à Residência",
        "pergunta": "Ola, eu moro na rua teresa no ponto final de xerém. Gostaria de saber onde eu acho a clínica da família mais próxima, para eu me cadastrar e cuidar da minha saúde.",
        "history": [],
        "comportamento_anterior": "Apresentou uma resposta conceitual e orientativa muito rica, explicando o papel das UBS/USF/Clínicas da Família e indicando o link do portal da Secretaria de Saúde, mas sem cruzar as coordenadas da base equipamentos.json com o endereço fornecido para dar a unidade mais próxima.",
        "avaliacao_humana": "A resposta foi muito boa a nível de orientação. Porém, seria legal se conseguíssemos fazê-la ter acesso a alguma API do Maps ou base de endereço de equipamentos, confrontando ao endereço passado pela cidadã e informar qual equipamento público mais próximo."
    },
    {
        "id": 2,
        "titulo": "Fazendinha do Autista Funciona?",
        "pergunta": "Vi que vocês tem a fazendinha do autista. Como faz para inscrever meu filho lá? Ela já está funcionando e aberta ao público neste momento?",
        "history": [],
        "comportamento_anterior": "Confirmou o funcionamento, ausência de fila de espera, passo a passo para inscrição, documentos, gratuidade, telefone, e-mail e Instagram oficial. (Padrão Ouro)",
        "avaliacao_humana": "A resposta está ótima."
    },
    {
        "id": 3,
        "titulo": "A Casa do Autista já está Funcionando?",
        "pergunta": "E a casa do autista, está funcionando também?",
        "history": [
            "Munícipe: Vi que vocês tem a fazendinha do autista. Como faz para inscrever meu filho lá? Ela já está funcionando?",
            "DUQUE IA: A Fazendinha do Autista está funcionando normalmente no Parque Capivari..."
        ],
        "comportamento_anterior": "Esclareceu imediatamente que a Casa do Autista não está funcionando ainda (obra/projeto previsto para o 1º Distrito, Rua Jandira, atrás do Restaurante Popular). (Padrão Ouro)",
        "avaliacao_humana": "A resposta está ótima."
    },
    {
        "id": 4,
        "titulo": "Auxiliar no Resgate de um Morador de Rua",
        "pergunta": "Encontrei um morador de rua desmaiado. Ele precisa de ajuda. Como posso ajuda-lo a prefeitura pode me auxiliar?",
        "history": [],
        "comportamento_anterior": "Priorizou o SAMU 192, mas na assistência social presumiu e indicou especificamente o CRAS Jardim Primavera sem saber onde o fato ocorreu (Hallucinated Specificity).",
        "avaliacao_humana": "A resposta foi boa, porém, poderia indicar o link para buscar o CRAS mais próximo e não o de Jardim Primavera, pq não disse que o ocorrido foi em Primavera."
    },
    {
        "id": 5,
        "titulo": "Como Regularizo meu Imóvel e Dou Entrada no meu RGI",
        "pergunta": "Gostaria de saber como regularizo meu imóvel com RGI!",
        "history": [],
        "comportamento_anterior": "Informou que procedimentos de RGI não constavam na base interna e ofereceu em contingência o serviço correlato de Resolução de Processos em Pendência do Código de Obras.",
        "avaliacao_humana": "A capacidade de fornecer outra resposta com proximidade conceitual, achei legal! Mas devemos verificar se não temos alguma informação sobre RGI para fornecer... Verificar nos sites oficiais e documentos do Urbanismo."
    },
    {
        "id": 6,
        "titulo": "Estabelecimento que Vende Carne Fede Muito",
        "pergunta": "Tem um estabelecimnto perto da minha rua que está fedendo muito. Eles vendem carne!",
        "history": [],
        "comportamento_anterior": "Respondeu que a base não detalha denúncia específica de mau cheiro de comércio, sugeriu registrar no Colab genericamente sem links e sem categorias corretas da Vigilância Sanitária.",
        "avaliacao_humana": "Não possui o link para o Colab. A resposta também não ficou completa. Tínhamos que explicar que é a Vigilância Sanitária que realiza essa fiscalização e que pode ser aberta uma denúncia com esse tema e o assunto correto no sistema de Ouvidoria pelo Colab."
    },
    {
        "id": 7,
        "titulo": "Barulho em Casa de Festa Noturna (Loop de Multi-turno)",
        "pergunta": "É uma casa de festas, tem uma pessoa que é um dono. Pode entrar quem pagar",
        "history": [
            "Munícipe: Tem uma festa fazendo um barulho insuportável agora à noite perto de casa.",
            "DUQUE IA: Poderia me informar se o local do evento é um espaço público ou se há algum servidor envolvido...?"
        ],
        "comportamento_anterior": "Entrou em loop repetitivo: repetiu exatamente a mesma exigência de complementação sobre servidor público ou unidade da prefeitura.",
        "avaliacao_humana": "Ela pede complemento de informações, eu envio a ela, porém não consegue assimilar e me retorna a mesma exigência de complementação. Neste caso eu já passei todas as informações de primeira, era pra ela me responder corretamente quem é o órgão que trata e me orientando a registrar uma denúncia na polícia e que não é competência da prefeitura, pois é o correto em casa de festas noturnas."
    },
    {
        "id": 8,
        "titulo": "Regularização de Situação para Profissionais Liberais",
        "pergunta": "Sou profissional liberal e quero regularizar meu estabelecimento. Quero gerar o alvará e o certificado de vigilância sanitária. Como faço?",
        "history": [],
        "comportamento_anterior": "Ignorou completamente o certificado de vigilância sanitária, informou equivocadamente que não havia dados sobre alvará para profissional liberal e recuperou dados genéricos da SMF sem buscar fontes externas.",
        "avaliacao_humana": "Resposta bem ruim. Ignorou o da Vigilância Sanitária, depois informou que não temos isso disponíveis na nossa base oficial. Depois foi lá e achou a informação do alvará da Fazenda e como solicitar. Me parece que ela não está fazendo buscas nas internet para o que não tem na nossa base. Ela precisa buscar a internet quando não encontrar e retornar com a fonte em sites oficiais."
    },
    {
        "id": 9,
        "titulo": "Retirada de Animal Silvestre (Gambá no Quintal)",
        "pergunta": "Tem um gambá preso no meu quintal. Gostaria de solicitar resgate como faço?",
        "history": [],
        "comportamento_anterior": "Disse que a base oficial não continha detalhes sobre resgate de gambá, sugeriu genericamente o Colab e preencheu campos formais vazios com 'Não especificado'. Sem link do Colab.",
        "avaliacao_humana": "Resposta não foi correta. A orientação não tem link do Colab. Disse que não temos isso na base oficial, mas o Meio Ambiente se não me engano, tem esta atribuição."
    },
    {
        "id": 10,
        "titulo": "Múltiplas Perguntas num Único Prompt + Interface do Chat",
        "pergunta": "Tenho um ninho de marimbondos na minha rua, está colocando em risco a todos. Além disso, tmbém gostaria de retirar entulho da minha porta. Fora isso também gostaria de fazer uma pode de uma árvore que tem no meu quinta. E no final, marcar uma consulta para mim no cardiologista.",
        "history": [],
        "comportamento_anterior": "Agrupou os 3 primeiros assuntos em um bloco confuso, dizendo genericamente que não havia nada na base, e respondeu apenas sobre a consulta cardiológica.",
        "avaliacao_humana": "A primeira resposta ela juntou assuntos que são de temas diferentes e disse erradamente que não tem nada base. Em mesmo que não tenha na base, não busca na internet em fontes confiáveis? Respondeu corretamente sobre a consulta. Parece que a capacidade de responder múltiplas perguntas no mesmo prompt, não está bom. OBS: NÃO FUNCIONA SHIFT+ENTER NO CHAT DA IA. DEVERIA."
    },
    {
        "id": 11,
        "titulo": "Falta de Água na Rua (Concessionárias)",
        "pergunta": "Quero abrir uma demanda de falta de água na minha rua. Como posso fazer?",
        "history": [],
        "comportamento_anterior": "Disse que não encontrou informações na base e sugeriu procurar a estatal antiga (CEDAE).",
        "avaliacao_humana": "Resposta errada. Temos agora contato com a Águas do Rio, então essas demandas podem ser abertas pelo Colab com tema da Águas do Rio em Ouvidoria, ou então procurar os canais próprios da Água do Rio. Também temos da Light e da Enel, então é bom ajustar estes contextos também."
    },
    {
        "id": 12,
        "titulo": "Poda de Árvore em Local Particular",
        "pergunta": "Gostaria de solicitar uma avaliação para poda ou corte de uma árvore no quintal da minha casa com risco de queda.",
        "history": [],
        "comportamento_anterior": "Acertou o órgão (SMMA) e a interação com a Light, mas no final recomendou ligar previamente para a secretaria para perguntar quais documentos levar.",
        "avaliacao_humana": "Resposta correta, porém, não precisa recomendar entrar em contato com a secretaria para perguntar os documentos, uma vez que o cidadão já irá comparecer presencialmente para solicitar a poda."
    },
    {
        "id": 13,
        "titulo": "Emergência em Ortopedia e Referência no Município",
        "pergunta": "Quebrei o pé e moro em Jardim Primavera, Duque de Caxias. Gostaria de saber qual é o hospital de referência em ortopedia mais próximo onde posso procurar atendimento.",
        "history": [],
        "comportamento_anterior": "Afirmou que não havia detalhes sobre hospitais específicos de emergência ortopédica e discorreu longamente sobre o programa ambulatorial eletivo 'Chegaram os Especialistas'.",
        "avaliacao_humana": "A resposta foi incorreta. Não podemos abordar somente sobre hospital de referência numa emergência médica. Precisamos recomendar a ida para o hospital de trauma mais próximo, que no nosso caso a referência é o Adão Pereira Nunes. Abordar sobre o programa Chegaram os Especialistas está errado."
    },
    {
        "id": 14,
        "titulo": "Reparo de Canteiro Danificado",
        "pergunta": "Como solicitar o conserto de um canteiro danificado na calçada da rua?",
        "history": [],
        "comportamento_anterior": "Citou genericamente Meio Ambiente ou Serviços Públicos no Colab, sem links e sem precisão sobre a secretaria responsável.",
        "avaliacao_humana": "Resposta errada. Deveria recomendar o comparecimento à Secretaria de Obras e Agricultura ou abrir uma reclamação no Colab com o tema de Obras e assunto correto. Colocar o link do Portal Cidadão."
    },
    {
        "id": 15,
        "titulo": "Alvará de Funcionamento para Templo Religioso",
        "pergunta": "Templo religioso sem alvará: a Prefeitura pode interditar sumariamente? Quais licenças são necessárias e quais etapas administrativas existem?",
        "history": [],
        "comportamento_anterior": "Respondeu de forma evasiva: 'As informações oficiais disponíveis em nossa base de dados não detalham especificamente... não é possível afirmar...'.",
        "avaliacao_humana": "Resposta errada. Alvará precisa ser dado pela Fazenda e isso tem nas nossas regras. Existe o Portal do Contribuinte. Precisamos verificar onde no Portal do Contribuinte se consegue o alvará e quais as devidas instruções. Ela não respondeu todas as questões perguntadas. Verificar se tem algum site oficial ou fonte confiável que tenha essas informações."
    },
    {
        "id": 16,
        "titulo": "Recurso e Defesa para Multas",
        "pergunta": "Recebi uma multa que considero indevida, mas não sei qual órgão municipal a aplicou. Como posso identificar o órgão responsável, consultar o processo administrativo e apresentar defesa ou recurso dentro do prazo?",
        "history": [],
        "comportamento_anterior": "Bloqueou a consulta emitindo a mensagem do Guardrail: 'Como assistente virtual informativo, não realizo pareceres jurídicos, defesas, recursos ou interpretações de leis... Bloqueio por Assunto Jurídico (BLOCKED LEGAL)'.",
        "avaliacao_humana": "Resposta errada. Tem diferentes demandas na mesma questão. O órgão responsável no município por tratar isso é a JARI na Segurança Pública. Para consultar o processo administrativo precisa entrar em contato com o órgão e verificar qual caminho correto."
    },
    {
        "id": 17,
        "titulo": "Diferença entre Pedido de Informação (e-SIC) e Manifestações (Ouvidoria)",
        "pergunta": "Quero saber quantos médicos estão lotados no posto e reclamar que não tem atendimento. Faço solicitação única ou separada?",
        "history": [],
        "comportamento_anterior": "Explicou teoricamente a diferença conceitual, mas indicou telefones gerais da Secretaria de Saúde sem fornecer o link do e-SIC nem o link da Ouvidoria do Colab.",
        "avaliacao_humana": "Resposta não foi legal. Precisava diferenciar o pedido de informação de manifestações e mandar os links separados do e-SIC e do serviço de Ouvidoria do Colab para o cidadão cadastrar as demandas. Não orientou direito e não forneceu os links corretos."
    },
    {
        "id": 18,
        "titulo": "Um Amigo Quer Emagrecer",
        "pergunta": "um amigo meu quer emagrecer, qual secretaria ele procura?",
        "history": [],
        "comportamento_anterior": "Disse que a base oficial não continha detalhes sobre emagrecimento, citou Procuradoria Geral e cursos da FUNDEC (alucinação por proximidade lexical nula) e, ao final, sugeriu procurar a Secretaria de Saúde.",
        "avaliacao_humana": "Resposta errada. Existe informação nos sites oficiais sobre emagrecimento. Inclusive na carta de serviços da Saúde tem sobre nutrição e outras questões que podem ajudar a orientar o cidadão qual unidade ele pode procurar. Parece que ela não está conseguindo concatenar os dados disponíveis e usar como fonte de conhecimento da forma correta."
    },
    {
        "id": 19,
        "titulo": "Falta de Iluminação Pública na Rua (Zeladoria vs Ouvidoria)",
        "pergunta": "Tem uma lâmpada queimada na minha rua gerando escuridão e medo de assaltos em idosos.",
        "history": [],
        "comportamento_anterior": "Citou a SMTSP e a PPP de Iluminação, mas direcionou para abertura como demanda de Ouvidoria em vez de serviço primário de Zeladoria Urbana.",
        "avaliacao_humana": "Resposta incorreta. Ela deu recomendação para abrir pela Ouvidoria, uma demanda que é para ser solicitada em Zeladoria. É importante que a IA consiga diferenciar essas situações, pois ela tem acesso a essas informações. Precisa colocar o link certo para abertura na Zeladoria e informar a categoria correta."
    },
    {
        "id": 20,
        "titulo": "Demora na Marcação de Consulta (Ajuste de Tom Institucional)",
        "pergunta": "Minha mãe está esperando há meses e há uma demora extrema para marcação de especialista na UBS, como proceder?",
        "history": [],
        "comportamento_anterior": "Orientou sobre o SISREG, mas no fechamento incluiu recomendação combativa de desconfiança contra a recepção do posto de saúde ('pergunte sobre o status do pedido para o especialista, em vez de apenas ser informada sobre a falta de vagas').",
        "avaliacao_humana": "Resposta correta, porém, precisa ajustar essa mensagem final. O trecho sublinhado em vermelho pode sair. Pode ser que isso instigue o cidadão a criar problemas na regulação."
    },
    {
        "id": 21,
        "titulo": "Denúncia de Conduta Irregular de Funcionário",
        "pergunta": "Quero denunciar um funcionário fantasma, ele nunca aparece na unidade pra trabalhar, em horário de expediente... Não tenho registro, mas posso informar o nome e a unidade onde ele deveria trabalhar.",
        "history": [],
        "comportamento_anterior": "Apresentou resposta desconexa inferindo sem fundamentação que o caso envolvia a Secretaria de Gestão, Inclusão e Mulher (SMGIM) ou SMS, citando programas como 'Atividade Educativa' e fornecendo contatos incorretos.",
        "avaliacao_humana": "Resposta sem sentido. Não foi citado o órgão e ela inferiu sem fundamentação que estava falando sobre a Secretaria de Gestão Inclusão e Mulher e Secretaria de Saúde. Deu endereço das secretarias de forma incorreta também. A resposta certa seria indicar abrir demanda pelo canal de Ouvidoria no Colab no tipo denúncia."
    },
    {
        "id": 22,
        "titulo": "Assistência por Casa Destruída por Chuva",
        "pergunta": "Minha casa foi totalmente destruída pela chuva e enchente. Perdi tudo. Como a Prefeitura e a Assistência Social podem me ajudar?",
        "history": [],
        "comportamento_anterior": "Indicou a Secretaria de Assistência Social (SMASDH), mas apontou o comparecimento físico na sede central administrativa da secretaria na Av. Brigadeiro Lima e Silva, no Jardim 25 de Agosto.",
        "avaliacao_humana": "Resposta mediana. Poderia sugerir verificar na listagem dos CRAS, identificar o mais próximo da região dela e comparecer para solicitar ajuda."
    },
    {
        "id": 23,
        "titulo": "Diferenças entre Secretaria de Obras e Secretaria de Urbanismo",
        "pergunta": "Qual a diferença entre a secretaria de obras e a secretaria de urbanismo? Liste exemplos de serviços de cada uma delas para exemplificar a diferença de escopo",
        "history": [],
        "comportamento_anterior": "Resposta perfeita e pedagógica. Diferenciou a SMOA (infraestrutura urbana pública: drenagem, asfalto, tapa-buraco, quebra-mola) da SMUH (regulação e licenciamento privado: alvarás de construção, habite-se, REURB, posturas). (Padrão Ouro)",
        "avaliacao_humana": "Resposta está boa."
    }
]

print("=" * 75)
print("      DUQUE IA — EXECUÇÃO OFICIAL DOS 23 CASOS DE QA")
print("=" * 75)

results = []

for idx, c in enumerate(CASES_CONFIG, 1):
    cid = c["id"]
    titulo = c["titulo"]
    pergunta = c["pergunta"]
    hist = c["history"]
    
    print(f"\n[{idx:02d}/23] Executando Caso {cid:02d}: {titulo}")
    print(f"   Pergunta: \"{pergunta[:75]}...\"")
    
    conv_id = f"qa_eval_case_{cid:02d}_{int(time.time())}"
    start_time = time.time()
    
    try:
        res_dict = agent.process_query(pergunta, conversation_id=conv_id, history=hist)
        ans = res_dict.get("answer", "")
        confidence = res_dict.get("confidence", 0.0)
        intent = res_dict.get("intent_detected", "")
        sources = res_dict.get("sources", [])
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        print(f"   -> Concluído em {elapsed_ms}ms | Intent: {intent} | Confiança: {confidence}")
        print(f"   -> Resposta: {ans[:150].replace(chr(10), ' ')}...")
        
        results.append({
            "id": cid,
            "titulo": titulo,
            "pergunta": pergunta,
            "history": hist,
            "comportamento_anterior": c["comportamento_anterior"],
            "avaliacao_humana": c["avaliacao_humana"],
            "nova_resposta": {
                "answer": ans,
                "confidence": confidence,
                "intent_detected": intent,
                "sources": sources,
                "elapsed_ms": elapsed_ms
            }
        })
    except Exception as e:
        print(f"   [ERRO] Falha no Caso {cid:02d}: {e}")
        results.append({
            "id": cid,
            "titulo": titulo,
            "pergunta": pergunta,
            "history": hist,
            "comportamento_anterior": c["comportamento_anterior"],
            "avaliacao_humana": c["avaliacao_humana"],
            "nova_resposta": {
                "answer": f"ERRO NA EXECUÇÃO: {str(e)}",
                "confidence": 0.0,
                "intent_detected": "error",
                "sources": [],
                "elapsed_ms": 0
            }
        })
        
    time.sleep(2.0) # Prevenção de rate-limit da API

out_path = os.path.join(_PROJECT_ROOT, "scripts", "results_23_casos_novas_respostas.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 75)
print(f"[SUCESSO] Todos os 23 casos executados e salvos em: {out_path}")
print("=" * 75)
