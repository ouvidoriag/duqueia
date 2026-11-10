# DUQUE IA — Dossiê Técnico de Diagnóstico de Causa Raiz e Soluções (QA 23 Casos)

> **Documento Técnico de Diagnóstico e Engenharia de Soluções**  
> **Sistema:** DUQUE IA — Assistente Virtual da Prefeitura de Duque de Caxias / RJ  
> **Origem dos Dados:** Relatório de Auditoria e Testes Práticos (Análises 01 a 23 + 12 Diretrizes Gerais)  
> **Elaborado por:** Arquiteto Sênior de Inteligência Artificial & Engenharia de RAG  
> **Finalidade:** Mapear a causa raiz exata pela qual o DUQUE IA gerou cada resposta e definir a arquitetura de soluções técnicas definitiva para cada observação apontada, **sem alterar o código em execução**.

---

## 📑 Sumário Executivo

Este documento disseca a totalidade das **23 análises de perguntas e respostas reais** realizadas no DUQUE IA, confrontando o comportamento observado em tela com a arquitetura interna do sistema (Filtro Rápido (Fast Gate), Base Ouro Oficial (Golden Source) de 443 unidades, Classificador de Triagem, RAG Híbrido Multiconta, Reranker e Guardrails).

Para cada caso analisado, o dossiê apresenta:
1. **O que o munícipe perguntou**;
2. **O que a IA respondeu**;
3. **A observação/avaliação humana**;
4. **O Diagnóstico da Causa Raiz no Pipeline** (*Por que a IA respondeu dessa forma?*);
5. **A Solução Técnica Recomendada** (*Engenharia de Prompt, Ontologia, Roteamento ou Dados*).

Adicionalmente, o documento traduz as **12 Diretrizes Gerais de Melhoria** em especificações técnicas de implementação para a evolução do sistema.

---

## 🔬 Parte 1: Diagnóstico Detalhado dos 23 Casos de Teste

---

### Caso 01 — Endereço do Equipamento de Saúde Próximo à Residência
* **Pergunta do Munícipe:**  
  *"Ola, eu moro na rua teresa no ponto final de xerém. Gostaria de saber onde eu acho a clínica da família mais próxima, para eu me cadastrar e cuidar da minha saúde."*
* **Comportamento da IA:**  
  Apresentou uma resposta conceitual e orientativa muito rica, explicando o papel das UBS/USF/Clínicas da Família e indicando o link do portal da Secretaria de Saúde (`https://saude.duquedecaxias.rj.gov.br/unidades-de-saude.php`).
* **Avaliação / Observação:**  
  *"A resposta foi muito boa a nível de orientação. Porém, seria legal se conseguíssemos fazê-la ter acesso a alguma API do Maps ou base de endereço de equipamentos, confrontando ao endereço passado pela cidadã e informar qual equipamento público mais próximo."*
* **Diagnóstico da Causa Raiz:**  
  O módulo `agent/entity_resolver.py` possui resolução determinística por nome de equipamento e por bairro ("xerém"), mas o pipeline atual não possui um módulo de cálculo de distância espacial (cálculo de distância geográfica (cálculo geográfico de distância (Haversine) ou Roteamento)) ativo no fluxo da rota conversacional quando o cidadão informa um logradouro específico ("rua teresa") e solicita a unidade "mais próxima". O mecanismo de busca (mecanismo de busca (retriever)) recorreu ao fragmento de texto (chunk) informativo geral de Atenção Básica da Saúde em vez de filtrar as coordenadas da base `equipamentos.json`.
* **Solução Técnica:**  
  1. **Geocodificação de Logradouro:** Conectar o resolvedor de endereços ao índice local de logradouros de Duque de Caxias ou API ArcGIS/Nominatim para obter a latitude e longitude da Rua Teresa (Xerém).  
  2. **Cálculo de Proximidade (Classificação dos Mais Próximos (Classificação dos Mais Próximos (Top-K) Geográfico)):** Executar cálculo de distância em linha reta (fórmula de cálculo geográfico de distância (Haversine)) contra os 443 equipamentos cadastrados (`data/knowledge/bancoduqueia/dados_mestres/equipamentos.json`), filtrando por `categoria == "Saúde"` e `tipo in ["UBS", "USF", "Clínica da Família"]`.  
  3. **Resposta com Georreferenciamento:** Retornar a unidade número 1 mais próxima (ex: UBS Mantiquira ou USF Xerém), com endereço exato, ponto de referência e link de rota do mapa.

---

### Caso 02 — Fazendinha do Autista Funciona?
* **Pergunta do Munícipe:**  
  *"Vi que vocês tem a fazendinha do autista. Como faz para inscrever meu filho lá? Ela já está funcionando e aberta ao público neste momento?"*
* **Comportamento da IA:**  
  Confirmou o funcionamento, ausência de fila de espera, passo a passo para inscrição, documentos, gratuidade, telefone, e-mail e Instagram oficial.
* **Avaliação / Observação:**  
  *"A resposta está ótima."*
* **Diagnóstico da Causa Raiz:**  
  Correspondência exata (match perfeito) na Camada de Governança Canônica (`regra_00004` de `bancoduqueia/dados_mestres/regras_negocio.json`). O Filtro Rápido de Segurança (Filtro Rápido (Fast Gate)) identificou a entidade única "Fazendinha do Autista" e injetou os dados auditados com 100% de confiança, sem depender de inferência estocástica do LLM.
* **Solução Técnica:**  
  Manter esse padrão estruturado como padrão de referência de ouro (padrão de referência (benchmark)) para todos os equipamentos especiais do município.

---

### Caso 03 — A Casa do Autista já está Funcionando?
* **Pergunta do Munícipe:**  
  *"E a casa do autista, está funcionando também?"*
* **Comportamento da IA:**  
  Esclareceu imediatamente que a Casa do Autista **não está funcionando ainda** (obra/projeto previsto para o 1º Distrito, Rua Jandira, atrás do Restaurante Popular).
* **Avaliação / Observação:**  
  *"A resposta está ótima."*
* **Diagnóstico da Causa Raiz:**  
  A regra canônica `regra_00015` do Bancoduqueia define explicitamente o status da obra da Casa do Autista. Além disso, a gestão de múltiplos turnos de conversa (multi-turno) (`rewrite_query_with_history`) resolveu com sucesso a partícula de continuidade *"E a casa..."*.
* **Solução Técnica:**  
  Preservar o mapeamento preventivo de equipamentos em fase de obras/projeto para evitar que a IA afirme falsamente que locais em construção já atendem o público.

---

### Caso 04 — Auxiliar no Resgate de um Morador de Rua
* **Pergunta do Munícipe:**  
  *"Encontrei um morador de rua desmaiado. Ele precisa de ajuda. Como posso ajuda-lo a prefeitura pode me auxiliar?"*
* **Comportamento da IA:**  
  Priorizou corretamente a emergência médica com acionamento imediato do **SAMU 192**. No entanto, na seção posterior de apoio social, indicou especificamente o **CRAS Jardim Primavera** com endereço e telefone.
* **Avaliação / Observação:**  
  *"A resposta foi boa, porém, poderia indicar o link para buscar o CRAS mais próximo e não o de Jardim Primavera, pq não disse que o ocorrido foi em Primavera."*
* **Diagnóstico da Causa Raiz:**  
  Especificidade Alucinada (*Hallucinated Specificity* — presunção indevida de dados não informados) na camada de recuperação de unidades. Ao buscar serviços de assistência social pós-estabilização médica, a query relacional em `secretaria_unidades` ordenou por ID padrão e retornou o CRAS Jardim Primavera (ID 1). Como o munícipe não forneceu bairro, a IA presumiu aquela unidade física em vez de tratar a ausência de localidade.
* **Solução Técnica (Seguindo a mesma lógica geoespacial do Caso 01):**  
  1. **Priorização Médica Incondicional:** Manter como primeiro passo o alerta de emergência médica com acionamento imediato do **SAMU 192** (ou Bombeiros 193).  
  2. **Mapeamento e Geocodificação do Endereço da Ocorrência (Lógica do Caso 01):** Conectar o resolvedor de endereços ao índice cartográfico de Duque de Caxias para obter a latitude e longitude do local onde o morador de rua foi encontrado (rua, praça, bairro ou ponto de referência).  
  3. **Cálculo de Proximidade (Top-K Geográfico / Haversine):** Executar cálculo espacial de distância contra os equipamentos de Assistência Social cadastrados na base oficial (`data/knowledge/bancoduqueia/dados_mestres/equipamentos.json`), filtrando por `categoria == "Assistência Social"` e priorizando o **Centro POP** (unidade especializada em população em situação de rua) e o **CRAS/CREAS mais próximo** daquelas coordenadas exatas.  
  4. **Triagem de Esclarecimento Contextual (Agente Coletor para Endereço Ausente):** Caso o munícipe não informe a localização exata no primeiro turno, o gerador de resposta é expressamente proibido de arbitrar um CRAS genérico. O sistema aciona o comportamento de Agente Coletor: *"Para indicarmos o CRAS ou a equipe de abordagem social mais próxima do local, por favor me informe em qual rua ou bairro a pessoa se encontra."*

---

### Caso 05 — Como Regularizo meu Imóvel e Dou Entrada no meu RGI
* **Pergunta do Munícipe:**  
  *"Gostaria de saber como regularizo meu imóvel com RGI!"*
* **Comportamento da IA:**  
  Informou que procedimentos para início de RGI não constavam na base interna, oferecendo em contrapartida o serviço correlato de "Resolução de Processos em Pendência" (Código de Obras).
* **Avaliação / Observação:**  
  *"A capacidade de fornecer outra resposta com proximidade conceitual, achei legal! Mas devemos verificar se não temos alguma informação sobre RGI para fornecer. Embora o município não consiga regularizar todos os casos, será que não tem um caminho melhor para orientar? Verificar nos sites oficiais e documentos do Urbanismo."*
* **Diagnóstico da Causa Raiz:**  
  O RGI (Registro Geral de Imóveis) é ato registral de competência privativa dos Cartórios de Registro de Imóveis (1º e 2º Ofícios da Comarca de Duque de Caxias), e não um serviço emitido diretamente no balcão da Prefeitura. No entanto, a Prefeitura é responsável por emitir os atos autorizativos prévios (Habite-se, Desmembramento, Certidão de Dados Cadastrais/IPTU e REURB - Regularização Fundiária pela SMUH). Como a base de dados não continha um fragmento de texto oficial (fragmento de texto (chunk)) ligando a sigla "RGI" aos pré-requisitos municipais da SMUH, o sistema deu resposta de contingência defensiva (contingência (fallback)).
* **Solução Técnica (Baseada no Guia Oficial da SMUH — "Como Regularizar o Registro do Imóvel?"):**  
  1. **Criação de Regra Canônica com a Triagem de Cenários Reais:**  
     - **Cenário 1 — O imóvel já possui matrícula no Cartório?** O cidadão identifica o Cartório de RGI competente pela localização (1º ou 2º Ofício). Na Secretaria Municipal de Urbanismo e Habitação (SMUH), abre *processo de logradouro/informações* para obter a certidão com o endereço oficial completo (logradouro atual, lote, quadra, loteamento, bairro e distrito) para atualização cadastral no RGI.  
     - **Cenário 2 — Possui escritura de compra e venda ou outro título de propriedade?** O caminho é apresentar o título diretamente ao Cartório de Registro de Imóveis para formalização e registro perante a matrícula do imóvel.  
     - **Cenário 3 — Tem apenas a posse e busca a propriedade (Usucapião)?**  
       * *Extrajudicial:* Contratação de advogado + protocolo no Cartório de RGI + pesquisa prévia nos arquivos da SMUH/Prefeitura sobre desapropriação, modificação de traçado ou regularização anterior.  
       * *Judicial:* Advogado particular ou Defensoria Pública do Estado + Poder Judiciário. A SMUH elabora a planta do imóvel e memorial descritivo **gratuitamente** quando solicitado via ofício formal da Defensoria Pública.  
     - **Regularização de Benfeitorias e Edificações (Construída ou a Construir):**  
       * *Benfeitoria já construída:* Pesquisa de processo na SMUH, contratação de profissional habilitado (arquiteto/engenheiro) para levantamento arquitetônico, abertura de protocolo de legalização na SMUH, quitação de taxas municipais, emissão da certidão de legalização/Habite-se e posterior averbação no Cartório de RGI.  
       * *Benfeitoria a construir:* Consulta prévia de projeto junto ao Urbanismo, aprovação do projeto, emissão do alvará de obras, vistoria final de conclusão com emissão do Habite-se pela SMUH e averbação no RGI.  
     - **Programa REURB (Regularização Fundiária Urbana — Lei Complementar nº 08/2021):** Para núcleos urbanos informais consolidados (REURB-S Social e REURB-E Específica), tramitados diretamente pela SMUH para concessão de títulos de legitimação fundiária.  
  2. **Canais e Endereço Oficial da SMUH para Atendimento Presencial:**  
     - **Secretaria Municipal de Urbanismo e Habitação (SMUH):** Alameda Bartolomeu Gusmão, nº 85 – Jardim Primavera, Duque de Caxias - RJ (CEP: 25215-320).  
     - **Telefones de Atendimento:** (21) 2773-0202 / (21) 2776-0388 / (21) 2783-6066.  
     - **Horário:** Segunda a sexta-feira, das 09h às 17h.  
     - **E-mail:** `semuh@duquedecaxias.rj.gov.br`.

---

### Caso 06 — Estabelecimento que Vende Carne Fede Muito
* **Pergunta do Munícipe:**  
  *"Tem um estabelecimnto perto da minha rua que está fedendo muito. Eles vendem carne!"*
* **Comportamento da IA:**  
  Respondeu que a base oficial não detalha denúncia específica de mau cheiro de comércio, mas sugeriu registrar no Colab citando Vigilância Sanitária ou Meio Ambiente de forma genérica, sem disponibilizar links nem os nomes exatos das categorias.
* **Avaliação / Observação:**  
  *"Não possui o link para o Colab. A resposta também não ficou completa. Tínhamos que explicar que é a Vigilância Sanitária que realiza essa fiscalização e que pode ser aberta uma denúncia com esse tema e o assunto correto (explicar o assunto) no sistema de Ouvidoria de Duque de Caxias pelo Colab (informar o link do serviço de Ouvidoria do Portal Cidadão)."*
* **Diagnóstico da Causa Raiz:**  
  O classificador de triagem não encontrou a palavra-chave "açougue" (o usuário escreveu *"estabelecimnto... vendem carne"*) na Carta de Serviços, e a taxonomia do Colab não estava vinculada às regras de Vigilância Sanitária de alimentos. O handler de contingência (fallback) não injetou o link parametrizado do Colab.
* **Solução Técnica:**  
  1. **Sinônimos Semânticos na Ontologia:** Mapear expressamente as expressões reais do cidadão: *"estabelecimento fedendo"*, *"comércio fedendo"*, *"vende carne fedendo"*, *"açougue fedendo"*, *"peixaria fedendo"*, *"carne estragada"*, *"mau cheiro de comércio"* diretamente para a **Subsecretaria de Vigilância Sanitária (SMS)** e fiscalização de alimentos.  
  2. **Direcionamento no Colab:** Instruir o munícipe com precisão:  
     - **Canal:** Aplicativo Colab ou Portal Cidadão — Ouvidoria Geral;  
     - **Tema / Categoria:** Vigilância Sanitária;  
     - **Assunto:** Fiscalização de Comércio de Alimentos / Condições Higiênico-Sanitárias;  
     - **Link:** Inserir o link oficial da Ouvidoria no Portal Cidadão.  
  3. **Orientações do POP:** Recomendar ao cidadão anexar fotos e indicar o nome de fachada e endereço exato com ponto de referência.

---

### Caso 07 — Barulho em Casa de Festa Noturna (Loop de Multi-turno)
* **Pergunta do Munícipe (Turno 1):**  
  *Relato inicial de barulho excessivo.*  
* **Resposta da IA (Turno 1):**  
  Pediu esclarecimento: *"Poderia me informar se o local do evento é um espaço público ou se há algum servidor envolvido...?"*  
* **Pergunta do Munícipe (Turno 2):**  
  *"É uma casa de festas, tem uma pessoa que é um dono. Pode entrar quem pagar"*  
* **Resposta da IA (Turno 2):**  
  Repetiu exatamente o mesmo padrão de exigência: *"Caso esse ocorrido envolva algum órgão, servidor ou serviço da Prefeitura... poderia informar em qual unidade ou secretaria esse fato aconteceu?"*
* **Avaliação / Observação:**  
  *"Ela pede complemento de informações, eu envio a ela, porém não consegue assimilar e me retorna a mesma exigência de complementação. Neste caso eu já passei todas as informações de primeira, era pra ela me responder corretamente quem é o órgão que trata e me orientando a registrar uma denúncia na polícia e que não é competência da prefeitura, pois é o correto em casa de festas noturnas."*
* **Diagnóstico da Causa Raiz:**  
  1. **Amnésia de Slot no Grafo:** O `COLLECTOR_HANDLER` e o nó `node_triage` classificaram a segunda mensagem como `POSSIVEL_DENUNCIA` isolada, ignorando que o turno anterior já era uma solicitação de esclarecimento em andamento e insistindo na mesma pergunta redundante.  
  2. **Viés de "Servidor Público":** O handler estava enviesado para investigar se a irregularidade envolvia servidor municipal, falhando ao reconhecer que se tratava de um estabelecimento comercial privado (casa de festas noturna).  
  3. **Ausência da Regra de Segurança Pública vs Fiscalização Integrada:** Falta de regra canônica orientando que perturbação do sossego e ilícitos em flagrante competem à Polícia Militar (190), enquanto a fiscalização municipal de poluição sonora do estabelecimento deve ser dividida estritamente entre Meio Ambiente (SMMA), Urbanismo (SMUU) e Superintendência de Operações (SUOP).
* **Solução Técnica:**  
  1. **Perturbação do Sossego e Ilícitos Penais (190 - Polícia Militar):**  
     Informar imediatamente que casos de perturbação do sossego alheio, som alto, desordem ou ilícitos penais em casas noturnas e eventos em andamento são matéria de **Segurança Pública**, devendo ser acionada a **Polícia Militar pelo 190**. A Prefeitura não possui atribuição de intervenção penal ou contenção armada em flagrante.  
  2. **Matriz de Fiscalização Integrada de Poluição Sonora (Meio Ambiente, SMUU e SUOP):**  
     Para a denúncia administrativa e fiscalização das irregularidades da casa noturna/comércio via Ouvidoria / Colab, a atuação conjunta dos órgãos municipais é:  
     - **Secretaria Municipal de Meio Ambiente (SMMA):** Fiscalização técnica de poluição sonora com decibelímetro, verificação dos limites legais de ruído (conforme Decreto nº 7.620/2020) e autuação/multa por infração ambiental. *(Canal Colab: Meio Ambiente → Assunto: Fiscalização legal de poluição sonora)*.  
     - **Secretaria Municipal de Urbanismo (SMUU / Posturas):** Fiscalização do Alvará de Localização e Funcionamento, conformidade do zoneamento urbano, exigência de projeto de isolamento acústico obrigatório e interdição física do estabelecimento por descumprimento do Código de Obras e Posturas.  
     - **Superintendência de Operações / Ordem Pública (SUOP):** Ações ostensivas de fiscalização e ordenamento urbano em bares, festas e casas noturnas, coibição do uso indevido de vias públicas/calçadas e apreensão de aparelhagem de som em conjunto com a Guarda Municipal.  
  3. **Consolidação de Memória de Turno:** Travar o estado do coletor para que, ao receber o segundo turno (*"É uma casa de festas, tem uma pessoa que é um dono..."*), o assistente encerre imediatamente perguntas repetitivas e entregue a resposta definitiva.

---

### Caso 08 — Regularização de Situação para Profissionais Liberais
* **Pergunta do Munícipe:**  
  *"Sou profissional liberal e quero regularizar meu estabelecimento. Quero gerar o alvará e o certificado de vigilância sanitária. Como faço?"*
* **Comportamento da IA:**  
  Ignorou completamente o pedido de "certificado de vigilância sanitária", informou equivocadamente que não havia dados sobre alvará para profissional liberal e, em seguida, recuperou dados gerais da Fazenda (SMF). Não realizou busca externa na internet.
* **Avaliação / Observação:**  
  *"Resposta bem ruim. Ignorou o da Vigilância Sanitária, depois informou que não temos isso disponíveis na nossa base oficial. Depois foi lá e achou a informação do alvará da Fazenda e como solicitar. Me parece que ela não está fazendo buscas nas internet para o que não tem na nossa base. Ela precisa buscar a internet quando não encontrar e retornar com a fonte em sites oficiais. Outra coisa, tem informação sobre certificado de vigilância sanitária na nossa carta de serviços se não me engano."*
* **Diagnóstico da Causa Raiz:**  
  1. **Diluição Semântica de Múltiplas Entidades:** O prompt do munícipe uniu dois serviços distintos: Alvará (SMF) e Certificado de Vigilância Sanitária (SMS). A busca vetorial unificada focou apenas nos termos de maior frequência lexical ("alvará"), descartando os fragmentos de texto (fragmentos de dados (chunks)) da Vigilância Sanitária.  
  2. **Busca Web Desativada:** O módulo de contingência (fallback) não disparou a busca web institucional porque o mecanismo de busca (retriever) encontrou fragmentos de dados (chunks) parciais da SMF com score acima do threshold de contingência (fallback) total.
* **Solução Técnica:**  
  1. **Splitter de Múltiplos Serviços (Decompositor de Múltiplas Consultas (Multi-Query Decomposer)):** Detectar conjunções coordenativas ("e", "além de", "também") e quebrar a consulta em duas sub-buscas: Sub-busca A: *Alvará para profissional liberal*; Sub-busca B: *Licenciamento/Certificado de vigilância sanitária municipal*.  
  2. **Estruturação de Resposta em 2 Blocos:**  
     - **Bloco 1 (Fazenda - SMF):** Inscrição Municipal / ISS Profissional Liberal e emissão de Alvará via Portal do Contribuinte.  
     - **Bloco 2 (Saúde - Vigilância Sanitária):** Licença Sanitária para estabelecimentos de saúde, estética ou serviços regulados.  
  3. **Busca Web Ativa:** Disparar varredura em sites oficiais (web scraping) no domínio `duquedecaxias.rj.gov.br` sempre que uma das sub-queries não atingir 80% de precisão nos fragmentos internos de dados (fragmentos de dados (chunks)).

---

### Caso 09 — Retirada de Animal Silvestre (Gambá no Quintal)
* **Pergunta do Munícipe:**  
  *"Tem um gambá preso no meu quintal. Gostaria de solicitar resgate como faço?"*
* **Comportamento da IA:**  
  Disse que a base oficial não continha detalhes sobre resgate de gambá, sugeriu genericamente o Colab e preencheu campos formais vazios com *"Documentos: Não especificado"*, *"Prazo: Não especificado"*, *"Custo: Não especificado"*. Não forneceu link do Colab.
* **Avaliação / Observação:**  
  *"Resposta não foi correta. A orientação não tem link do Colab. Disse que não temos isso na base oficial, mas o Meio Ambiente se não me engano, tem esta atribuição."*
* **Diagnóstico da Causa Raiz:**  
  1. O termo zoológico específico "gambá" não constava no vocabulário do fragmento de texto (chunk) da Carta de Serviços (que continha termos mais gerais como "fauna silvestre" e "proteção animal").  
  2. O template do gerador de respostas possui campos automáticos vazios (campos de preenchimento (placeholders)) que, na ausência de metadados, imprimem strings mecânicas como *"Não especificado na base de dados fornecida"*.
* **Solução Técnica:**  
  1. **Expansão de Ontologia de Fauna:** Incluir termos populares de fauna urbana: `gambá`, `sariguê`, `cobra`, `morcego`, `coruja`, `gavião` mapeados para **Secretaria Municipal de Meio Ambiente e Proteção Animal (SMMA) / Guarda Ambiental**.  
  2. **Fluxo de Emergência vs Manejo:**  
     - Animal agressivo ou risco iminente à vida: Acionar o **Corpo de Bombeiros (193)** ou Defesa Civil.  
     - Resgate / Soltura de animal silvestre sem risco imediato: Solicitar à **Guarda Ambiental / SMMA** ou registrar no **Colab** (Tema: Meio Ambiente, Assunto: Resgate de Animais Silvestres), acompanhado do link direto.  
  3. **Sanitização de Templates:** Eliminar linhas de texto que contenham *"Não especificado"*, omitindo campos vazios para não degradar a estética da mensagem.

---

### Caso 10 — Múltiplas Perguntas num Único Prompt + Interface do Chat
* **Pergunta do Munícipe:**  
  *"Tenho um ninho de marimbondos na minha rua, está colocando em risco a todos. Além disso, tmbém gostaria de retirar entulho da minha porta. Fora isso também gostaria de fazer uma pode de uma árvore que tem no meu quinta. E no final, marcar uma consulta para mim no cardiologista."*
* **Comportamento da IA:**  
  Agrupou os 3 primeiros assuntos (marimbondo, entulho, poda) em um bloco confuso, afirmando genericamente que nenhum deles estava detalhado na base, e respondeu apenas o procedimento de consulta cardiológica.
* **Avaliação / Observação:**  
  *"A primeira resposta ela juntou assuntos que são de temas diferentes e disse erradamente que não tem nada base. Em mesmo que não tenha na base, não busca na internet em fontes confiáveis? Respondeu corretamente sobre a consulta. Parece que a capacidade de responder múltiplas perguntas no mesmo prompt, não está bom. Além disso a organização da respostas de múltiplas questões precisa ficr melhor organizada. OBS: NÃO FUNCIONA SHIFT+ENTER NO CHAT DA IA. DEVERIA."*
* **Diagnóstico da Causa Raiz:**  
  1. O sistema tentou gerar um único vetor semântico de busca (vetor semântico (embedding)) para uma mensagem com 4 tópicos conflitantes (Defesa Civil, Limpeza Urbana, Meio Ambiente e Saúde), ocorrendo saturação do espaço vetorial.  
  2. No frontend (`public/js/chat.js`), o manipulador do evento `keydown` envia a mensagem ao detectar a tecla `Enter`, sem validar se a tecla modificadora `e.shiftKey` estava pressionada.
* **Solução Técnica:**  
  1. **Módulo Decompositor de Múltiplas Perguntas (Prompt Decomposer):** Antes da etapa de busca e recuperação (busca de dados (retrieval)), submeter mensagens com múltiplos conectivos a uma etapa local de decomposição:  
     - Item 1: Ninho de marimbondo em rua pública -> **Defesa Civil (199) / Bombeiros (193)**;  
     - Item 2: Retirada de entulho na calçada -> **Secretaria de Obras e Serviços Públicos (Colab - Remoção de Entulho)**;  
     - Item 3: Poda de árvore em quintal particular -> **Secretaria de Meio Ambiente (Avaliação Técnica)**;  
     - Item 4: Consulta com cardiologista -> **Atenção Básica (UBS/USF) -> SISREG**.  
  2. **Correção de Frontend (Shift + Enter):** Adicionar no código do chat:  
     ```javascript
     if (e.key === 'Enter' && !e.shiftKey) {
       e.preventDefault();
       sendMessage();
     }
     ```

---

### Caso 11 — Falta de Água na Rua (Concessionárias)
* **Pergunta do Munícipe:**  
  *"Quero abrir uma demanda de falta de água na minha rua. Como posso fazer?"*
* **Comportamento da IA:**  
  Disse que não encontrou informações na base e sugeriu procurar a **CEDAE**.
* **Avaliação / Observação:**  
  *"Resposta errada. Temos agora contato com a Águas do Rio, então essas demandas podem ser abertas pelo Colab com tema da Águas do Rio em Ouvidoria, ou então procurar os canais próprios da Água do Rio (a IA pode buscar na internet em fontes oficiais e responder corretamente). Também temos da Light e da Enel, então é bom ajustar estes contextos também."*
* **Diagnóstico da Causa Raiz:**  
  A base de conhecimento interna continha dados desatualizados anteriores à concessão do saneamento básico na Baixada Fluminense, citando a estatal antiga (CEDAE). O sistema não continha o cadastro da concessionária atual (**Águas do Rio**) nem da integração que a Ouvidoria Geral realiza pelo Colab.
* **Solução Técnica:**  
  1. **Atualização Cadastral de Concessionárias:**  
     - **Água e Esgoto:** **Águas do Rio** (Telefone/WhatsApp: 0800 195 0 195).  
     - **Energia Elétrica:** **Light** (0800 021 0196) para os distritos atendidos ou **Enel** se aplicável.  
  2. **Duplo Canal de Resolução:**  
     - **Canal Direto da Concessionária:** Para religamento emergencial e vazamentos na rede pública.  
     - **Canal da Ouvidoria Geral no Colab:** Se a concessionária não resolver ou houver descumprimento reiterado, o munícipe pode abrir uma manifestação no Colab no tema **"Ouvidoria - Concessionárias de Serviços Públicos"** para intermediação e fiscalização do município.

---

### Caso 12 — Poda de Árvore em Local Particular
* **Pergunta do Munícipe:**  
  *Solicitação de avaliação para poda/corte de árvore em quintal com risco de queda.*
* **Comportamento da IA:**  
  Acertou o órgão (SMMA) e a interação com a rede elétrica (Light), mas no final recomendou entrar em contato previamente com a secretaria para perguntar quais documentos levar.
* **Avaliação / Observação:**  
  *"Resposta correta, porém, não precisa recomendar entrar em contato com a secretaria para perguntar os documentos, uma vez que o cidadão já irá comparecer presencialmente para solicitar a poda."*
* **Diagnóstico da Causa Raiz:**  
  O gerador de respostas aplica uma heurística de preenchimento que orienta o munícipe a "ligar para checar documentos" sempre que a tabela oficial não lista uma relação exaustiva de certidões.
* **Solução Técnica:**  
  Ajustar a diretriz do Instrução Mestra do Sistema (System Prompt): Se a orientação principal for o comparecimento presencial na sede da Secretaria, orientar diretamente o kit básico documental padrão do cidadão (**Documento de identidade com foto, CPF e comprovante de residência ou posse do imóvel**) e eliminar frases de contato preliminar redundante.

---

### Caso 13 — Emergência em Ortopedia e Referência no Município
* **Pergunta do Munícipe:**  
  *"Quebrei o pé e moro em Jardim Primavera, Duque de Caxias. Gostaria de saber qual é o hospital de referência em ortopedia mais próximo onde posso procurar atendimento."*
* **Comportamento da IA:**  
  Afirmou que não havia detalhes sobre hospitais específicos de emergência ortopédica e discorreu longamente sobre o programa ambulatorial eletivo *"Chegaram os Especialistas"*.
* **Avaliação / Observação:**  
  *"A resposta foi incorreta. Não podemos abordar somente sobre hospital de referência numa emergência médica. Precisamos recomendar a ida para o hospital de trauma mais próximo, que no nosso caso a referência é o Adão Pereira Nunes. Abordar sobre o programa Chegaram os Especialistas está errado."*
* **Diagnóstico da Causa Raiz:**  
  Erro gravíssimo de classificação de contexto médico. A palavra "ortopedia" encontrou correspondência com a especialidade médica do programa eletivo *"Chegaram os Especialistas"*. O sistema falhou ao reconhecer o gatilho de trauma agudo (*"Quebrei o pé"*) e não acionou o protocolo de emergência hospitalar de urgência.
* **Solução Técnica:**  
  1. **Barreira de Segurança de Entrada para Trauma e Emergência (Barreira de Segurança de Entrada (Input Guardrail)):** Detectar expressões de trauma ortopédico imediato: `quebrei`, `fratura`, `osso quebrado`, `torção grave`, `trauma`.  
  2. **Bloqueio do SISREG Eletivo:** Nesses casos, proibir sumariamente menções a programas de agendamento ambulatorial (*"Chegaram os Especialistas"* ou regulação ambulatorial).  
  3. **Direcionamento Hospitalar de Referência:**  
     - **Hospital Municipal Dr. Moacyr Rodrigues do Carmo (HMMRC)**;  
     - **Hospital Estadual/Municipal Adão Pereira Nunes (Saracuruna)** — referência regional de trauma e cirurgia ortopédica;  
     - **UPHs e UPAs:** Como portas de primeiro socorro para imobilização provisória e encaminhamento via ambulância.

---

### Caso 14 — Reparo de Canteiro Danificado
* **Pergunta do Munícipe:**  
  *Como solicitar o conserto de um canteiro danificado na calçada da rua.*
* **Comportamento da IA:**  
  Citou genericamente Meio Ambiente ou Serviços Públicos no Colab, sem links e sem precisão sobre a secretaria responsável.
* **Avaliação / Observação:**  
  *"Resposta errada. Deveria recomendar o comparecimento à Secretaria de Obras e Agricultura ou abrir uma reclamação no Colab com o tema de Obras e assunto correto. Colocar o link do Portal Cidadão."*
* **Diagnóstico da Causa Raiz:**  
  A palavra "canteiro" não encontrou correspondência na tabela de serviços estruturados da SMOA, gerando uma pontuação fraca no RAG e uma resposta aproximada sem links funcionais.
* **Solução Técnica:**  
  1. **Mapeamento de Sinônimos de Vias e Logradouros:** Vincular `canteiro`, `calçada pública`, `meio-fio`, `guia`, `praça pública` à **Secretaria Municipal de Obras e Agricultura (SMOA)**.  
  2. **Taxonomia no Colab:** Indicar a categoria exata: **Obras e Infraestrutura -> Reparo de Vias / Canteiros Públicos**, fornecendo o link direto do Portal Cidadão.

---

### Caso 15 — Alvará de Funcionamento para Templo Religioso
* **Pergunta do Munícipe:**  
  *Templo religioso sem alvará: a Prefeitura pode interditar sumariamente? Quais licenças são necessárias e quais etapas administrativas existem?*
* **Comportamento da IA:**  
  Respondeu de forma evasiva: *"As informações oficiais disponíveis em nossa base de dados não detalham especificamente... não é possível afirmar..."*.
* **Avaliação / Observação:**  
  *"Resposta errada. Alvará precisa ser dado pela Fazenda e isso tem nas nossas regras. Existe o Portal do Contribuinte. Precisamos verificar onde no Portal do Contribuinte se consegue o alvará e quais as devidas instruções. Ela não respondeu todas as questões perguntadas. Verificar se tem algum site oficial ou fonte confiável que tenha essas informações."*
* **Diagnóstico da Causa Raiz:**  
  Consulta complexa e jurídica com múltiplos questionamentos. A IA não encontrou um fragmento de texto oficial (fragmento de texto (chunk)) com o termo exato "templo religioso" e assumiu postura de recusa completa em vez de decompor as premissas urbanísticas e tributárias gerais.
* **Solução Técnica:**  
  1. **Regra de Alvará para Templos e Imunidade:**  
     - Templos possuem **imunidade tributária** quanto a impostos sobre patrimônio e renda (Art. 150, VI, 'b' da CF), mas **estão sujeitos ao poder de polícia administrativo** da Prefeitura (Alvará de Localização e Funcionamento, Habite-se da SMUH e Certificado do CBMERJ).  
  2. **Procedimento de Alvará:** Solicitação via **Portal do Contribuinte (SMF)**, com envio do Estatuto Social, CNPJ, Ata de Eleição da Diretoria e laudo do Corpo de Bombeiros.  
  3. **Processo Administrativo de Fiscalização:** A Prefeitura não determina interdição sumária sem motivo grave de segurança: primeiro ocorre a **Notificação Preliminar / Auto de Infração**, concede-se prazo legal para defesa e regularização, e somente em caso de descumprimento ou risco iminente à integridade física dos fiéis ocorre a interdição.

---

### Caso 16 — Recurso e Defesa para Multas
* **Pergunta do Munícipe:**  
  *"Recebi uma multa que considero indevida, mas não sei qual órgão municipal a aplicou. Como posso identificar o órgão responsável, consultar o processo administrativo e apresentar defesa ou recurso dentro do prazo?"*
* **Comportamento da IA:**  
  Bloqueou a consulta emitindo a mensagem do Guardrail: *"Como assistente virtual informativo, não realizo pareceres jurídicos, defesas, recursos ou interpretações de leis... Bloqueio por Assunto Jurídico (BLOCKED LEGAL)"*.
* **Avaliação / Observação:**  
  *"Resposta errada. Tem diferentes demandas na mesma questão. O órgão responsável no município por tratar isso é a JARI na Segurança Pública. Para consultar o processo administrativo precisa entrar em contato com o órgão e verificar qual caminho correto."*
* **Diagnóstico da Causa Raiz:**  
  **Falso Positivo Severo no Barreira de Proteção Jurídica (Guardrail) (`LEGAL_TRIGGERS`).** O sistema de segurança interceptou a combinação das palavras "defesa", "recurso" e "multa" e interpretou que o usuário estava pedindo para a IA escrever uma petição de recurso judicial contra o município, quando na realidade tratava-se de uma simples dúvida sobre o rito administrativo e o órgão competente.
* **Solução Técnica:**  
  1. **Refinamento do Barreira de Proteção Jurídica (Guardrail):** O bloqueio deve atuar apenas se o usuário solicitar redação de petição (ex: *"Escreva uma petição de defesa"*, *"redija um recurso para anular minha multa"*). Dúvidas sobre *onde protocolar* ou *qual o prazo* devem ser liberadas normalmente.  
  2. **Roteamento para a JARI:**  
     - **Órgão Responsável:** **JARI (Junta Administrativa de Recursos de Infrações)**, vinculada à Secretaria Municipal de Segurança Pública e Transportes;  
     - **Consulta de Processo:** Setor de Protocolo Geral da Prefeitura ou sede da Secretaria de Transportes;  
     - **Procedimento:** Apresentação do formulário de recurso no prazo de 30 dias contados da notificação, anexando cópia da notificação, CNH, CRLV do veículo e provas documentais.

---

### Caso 17 — Diferença entre Pedido de Informação (e-SIC) e Manifestações (Ouvidoria)
* **Pergunta do Munícipe:**  
  *Quero saber quantos médicos estão lotados no posto e reclamar que não tem atendimento. Faço solicitação única ou separada?*
* **Comportamento da IA:**  
  Explicou teoricamente a diferença conceitual, mas indicou telefones gerais da Secretaria de Saúde sem fornecer o link do e-SIC nem o link da Ouvidoria do Colab.
* **Avaliação / Observação:**  
  *"Resposta não foi legal. Precisava diferenciar o pedido de informação de manifestações e mandar os links separados do e-SIC e do serviço de Ouvidoria do Colab para o cidadão cadastrar as demandas. Não orientou direito e não forneceu os links corretos."*
* **Diagnóstico da Causa Raiz:**  
  A IA acertou a lógica jurídica da Lei de Acesso à Informação (Lei 12.527) versus Lei da Ouvidoria (Lei 13.460), mas o template de resposta não possuía a injeção programática dos dois hiperlinks oficiais correspondentes.
* **Solução Técnica:**  
  1. **Estruturação Prática em 2 Canais Distintos:**  
     - **Canal 1: Pedido de Informação Pública (e-SIC / LAI):** Para consultar dados estatísticos e quadro de servidores lotados -> Fornecer o link do **e-SIC da Prefeitura de Duque de Caxias** (`duquedecaxias.rj.gov.br/e-sic`).  
     - **Canal 2: Reclamação / Ouvidoria:** Para relatar a ausência de médicos no plantão do dia -> Fornecer o link do **Colab (Módulo Ouvidoria)**, tipo *Reclamação*.  
  2. **Instrução Resolutiva:** Explicar expressamente que **não devem ser feitas no mesmo protocolo**, pois tramitam em sistemas e com prazos legais diferentes (20 dias para o e-SIC e 30 dias para a Ouvidoria).

---

### Caso 18 — Um Amigo Quer Emagrecer
* **Pergunta do Munícipe:**  
  *"um amigo meu quer emagrecer, qual secretaria ele procura?"*
* **Comportamento da IA:**  
  Disse que a base oficial não continha detalhes sobre emagrecimento, citou Procuradoria Geral e cursos da FUNDEC (alucinação por proximidade lexical nula) e, ao final, sugeriu procurar a Secretaria de Saúde.
* **Avaliação / Observação:**  
  *"Resposta errada. Existe informação nos sites oficiais sobre emagrecimento. Inclusive na carta de serviços da Saúde tem sobre nutrição e outras questões que podem ajudar a orientar o cidadão qual unidade ele pode procurar. Parece que ela não está conseguindo concatenar os dados disponíveis e usar como fonte de conhecimento da forma correta."*
* **Diagnóstico da Causa Raiz:**  
  A gíria/termo popular "emagrecer" não encontrou correspondência direta (match) nos serviços formais de saúde (catalogados como "Consulta em Nutrição", "Acompanhamento de Doenças Crônicas" ou "Hiperdia"). Com score nulo, o RAG preencheu os campos de contexto (slots) do prompt com os fragmentos de texto residuais (fragmentos de dados (chunks)) de maior peso estrutural da base (PGM e FUNDEC).
* **Solução Técnica:**  
  1. **Sinônimos Clínicos:** Mapear `emagrecer`, `perder peso`, `dieta`, `obesidade`, `nutricionista` para a rede de **Atenção Primária da Secretaria Municipal de Saúde (SMS)**.  
  2. **Porta de Entrada no SUS:** O munícipe não vai direto a um serviço especializado de emagrecimento; ele deve comparecer à sua **UBS ou USF (Clínica da Família)** de referência para uma consulta com o Clínico Geral, que fará a avaliação e o encaminhamento para o serviço de **Nutrição** ou programas de saúde preventiva.  
  3. **Trava Anti-Alucinação:** Se os fragmentos de dados (chunks) recuperados não tiverem relação semântica com saúde, suprimi-los imediatamente da resposta.

---

### Caso 19 — Falta de Iluminação Pública na Rua (Zeladoria vs Ouvidoria)
* **Pergunta do Munícipe:**  
  *Relato de lâmpada queimada na rua gerando escuridão e medo de assaltos em idosos.*
* **Comportamento da IA:**  
  Citou a SMTSP e a PPP de Iluminação, mas direcionou para abertura como demanda de Ouvidoria em vez de serviço primário de Zeladoria.
* **Avaliação / Observação:**  
  *"Resposta incorreta. Ela deu recomendação para abrir pela Ouvidoria, uma demanda que é para ser solicitada em Zeladoria. É importante que a IA consiga diferenciar essas situações, pois ela tem acesso a essas informações. Precisa colocar o link certo para abertura na Zeladoria e informar a categoria correta."*
* **Diagnóstico da Causa Raiz:**  
  Como a mensagem mencionava "assaltos", "violência" e "medo", o nó de triagem considerou o aspecto de segurança pública e direcionou o atendimento para a Ouvidoria Geral, em vez de isolar o fato gerador que era a **troca de lâmpada queimada (Zeladoria Urbana)**.
* **Solução Técnica:**  
  1. **Isolamento do Fato Gerador Primário:** Se a causa-raiz for poste apagado ou lâmpada queimada, a rota prioritária é sempre **Zeladoria Urbana**.  
  2. **Indicação Exata no Colab:**  
     - **Módulo / Aba:** Zeladoria Urbana;  
     - **Categoria:** Iluminação Pública;  
     - **Assunto:** Lâmpada Queimada / Manutenção de Iluminação LED;  
     - **Link:** Inserir o link direto do Colab para iluminação.  
  3. **Quando usar a Ouvidoria:** Esclarecer que a Ouvidoria Geral só deve ser acionada caso o pedido de zeladoria já tenha sido aberto e o prazo legal de atendimento tenha expirado.

---

### Caso 20 — Demora na Marcação de Consulta (Ajuste de Tom Institucional)
* **Pergunta do Munícipe:**  
  *Reclamação de demora extrema para marcação de especialista para a mãe.*
* **Comportamento da IA:**  
  Orientou detalhadamente sobre o SISREG, mas no fechamento incluiu a seguinte frase:  
  *"Recomendamos que, ao ir à UBS, você se certifique de que o encaminhamento do clínico geral foi devidamente inserido no sistema de regulação e pergunte sobre o status do pedido para o especialista, em vez de apenas ser informada sobre a falta de vagas. Isso garante que sua mãe esteja na fila de espera oficial."*
* **Avaliação / Observação:**  
  *"Resposta correta, porém, precisa ajustar essa mensagem final. O trecho sublinhado em vermelho pode sair. Pode ser que isso instigue o cidadão a criar problemas na regulação."*
* **Diagnóstico da Causa Raiz:**  
  O LLM tentou adotar um tom de suporte empático ("defesa enfática dos interesses do cidadão (advocacy)"), mas acabou sugerindo uma postura combativa e de desconfiança contra a recepção do posto de saúde, criando risco de atrito interpessoal nas unidades municipais.
* **Solução Técnica:**  
  1. **Ajuste de Tom no Instrução Mestra do Sistema (System Prompt):** Estabelecer uma regra mandatória de neutralidade institucional e cooperação com as equipes de atendimento público.  
  2. **Substituição da Frase de Fechamento:** Substituir o trecho por:  
     *"Ao comparecer à unidade, solicite o número do comprovante de inserção do pedido no SISREG. Com esse número em mãos, você poderá acompanhar o andamento da regulação nos canais oficiais de saúde do município com total transparência."*

---

### Caso 21 — Denúncia de Conduta Irregular de Funcionário
* **Pergunta do Munícipe:**  
  *"Quero denunciar um funcionário fantasma, ele nunca aparece na unidade pra trabalhar, em horário de expediente... Não tenho registro, mas posso informar o nome e a unidade onde ele deveria trabalhar."*
* **Comportamento da IA:**  
  Apresentou uma resposta desconexa, inferindo sem qualquer menção prévia que o caso envolvia a Secretaria de Gestão, Inclusão e Mulher (SMGIM) ou Secretaria de Saúde, citando programas como "Atividade Educativa" e fornecendo contatos incorretos.
* **Avaliação / Observação:**  
  *"Resposta sem sentido. Não foi citado o órgão e ela inferiu sem fundamentação que estava falando sobre a Secretaria de Gestão Inclusão e Mulher e Secretaria de Saúde. Deu endereço das secretarias de forma incorreta também. A resposta certa seria indicar abrir demanda pelo canal de Ouvidoria no Colab (fornecendo o link do Portal Cidadão do serviço de Ouvidoria), no tipo denúncia."*
* **Diagnóstico da Causa Raiz:**  
  Como a base de dados não continha um fragmento de texto oficial (fragmento de texto (chunk)) denominado *"funcionário fantasma"*, o mecanismo de busca (retriever) vetorial fez busca de alta aproximação por termos administrativos gerais e recuperou fragmentos aleatórios da SMGIM e SMS. O gerador de respostas tentou forçar uma amarração lógica inexistente em vez de direcionar para o canal geral de integridade.
* **Solução Técnica:**  
  1. **Regra de Denúncia de Conduta de Servidor:** Qualquer relato envolvendo funcionário fantasma, prevaricação, assédio, ausência de plantão ou irregularidade administrativa de servidores públicos deve ser encaminhado obrigatoriamente para a **Ouvidoria Geral do Município / Controladoria Geral (CGM)**.  
  2. **Canal do Colab:** Enviar o link direto do serviço de Ouvidoria no Portal Cidadão, orientando a selecionar o tipo **Denúncia**.  
  3. **Segurança Jurídica:** Ressaltar a garantia de sigilo de identidade do denunciante conforme a Lei Federal nº 13.460/2017 e orientar o munícipe a fornecer o maior número possível de dados (nome completo, lotação e fatos observados).

---

### Caso 22 — Assistência por Casa Destruída por Chuva
* **Pergunta do Munícipe:**  
  *Solicitação de auxílio emergencial para famílias com casas destruídas ou danificadas pela chuva.*
* **Comportamento da IA:**  
  Indicou a Secretaria de Assistência Social (SMASDH), mas apontou o comparecimento físico na sede central administrativa da secretaria na Av. Brigadeiro Lima e Silva, no Jardim 25 de Agosto.
* **Avaliação / Observação:**  
  *"Resposta mediana. Poderia sugerir verificar na listagem dos CRAS, identificar o mais próximo da região dela e comparecer para solicitar ajuda."*
* **Diagnóstico da Causa Raiz:**  
  O banco de dados relacional associa o serviço "Auxílio em Calamidades" diretamente à sede da SMASDH, sem desdobrar que o atendimento operacional territorial à população atingida é feito pela **rede descentralizada de CRAS** e pelos postos da Defesa Civil nos bairros.
* **Solução Técnica:**  
  1. **Descentralização do Atendimento Social:** Em situações de perda de moradia por chuva ou enchente, instruir que a solicitação de Aluguel Social, Cesta Básica Emergencial e acolhimento provisório é feita no **CRAS de referência territorial do bairro**.  
  2. **Lista Completa dos CRAS:** Fornecer o link ou a lista estruturada das unidades de CRAS dos 4 distritos para que o cidadão localize o mais perto de sua residência.  
  3. **Emergência Imediata:** Se o local ainda estiver sob risco de novos deslizamentos ou desabamentos, reforçar o acionamento imediato da **Defesa Civil pelo 199**.

---

### Caso 23 — Diferenças entre Secretaria de Obras e Secretaria de Urbanismo
* **Pergunta do Munícipe:**  
  *"Qual a diferença entre a secretaria de obras e a secretaria de urbanismo? Liste exemplos de serviços de cada uma delas para exemplificar a diferença de escopo"*
* **Comportamento da IA:**  
  Resposta perfeita e pedagógica. Diferenciou a SMOA (infraestrutura urbana pública: drenagem, asfalto, tapa-buraco, quebra-mola) da SMUH (regulação e licenciamento privado: alvarás de construção, habite-se, REURB, fiscalização de posturas e acústica).
* **Avaliação / Observação:**  
  *"Resposta está boa."*
* **Diagnóstico da Causa Raiz:**  
  Correspondência integral (match completo) com a regra de ontologia municipal `regra_canon_smoa_vs_smuh` cadastrada na governança do sistema.
* **Solução Técnica:**  
  Manter e adotar este formato comparativo como modelo para outras secretarias de fronteira de competência próxima (ex: Meio Ambiente vs Serviços Públicos).

---

## 🛠️ Parte 2: Plano de Engenharia das 12 Diretrizes Gerais de Melhoria

Abaixo estão as especificações arquiteturais e operacionais para atender integralmente aos **12 Pontos Gerais de Melhoria** demandados pela auditoria:

```mermaid
graph TD
    A[Mensagem do Munícipe] --> B{Separador de Múltiplas Intenções (Multi-Intent Splitter)?}
    B -->|Sim - Múltiplas Perguntas| C[Sub-Query 1 + Sub-Query 2 + ...]
    B -->|Não - Pergunta Única| D[Fluxo de Triagem]
    C --> D
    D --> E[Classificador Canônico / Ontológico]
    E -->|Zeladoria Urbana| F[Colab Zeladoria + Link Direto]
    E -->|Ouvidoria / Denúncia| G[Colab Ouvidoria + Link Portal Cidadão]
    E -->|e-SIC / LAI| H[Portal da Transparência / e-SIC]
    E -->|Concessionária| I[Águas do Rio / Light + Ouvidoria]
    E -->|Equipamento Próximo| J[Motor Geoespacial Classificação dos Mais Próximos (Top-K) Maps]
    E -->|Sem Chunk Interno| K[Busca Web em Sites Oficiais PMDC]
```

### 1. Melhorar a busca nas bases de conhecimento
* **Problema:** Respostas automáticas de que "não há informação" sem exaurir os documentos catalogados.  
* **Solução:**  
  - Implementar **expansão de sinônimos via ontologia** antes da etapa de busca e recuperação (busca de dados (retrieval)) (ex: mapear gírias e termos populares como "emagrecer", "ninho de marimbondo", "açougue fedendo" para seus equivalentes formais).  
  - Reduzir o corte do limiar de similaridade híbrida para 0.50 antes de disparar o resposta de contingência negativa (contingência (fallback)), ativando a busca FTS5 relaxada com operadores `OR` caso a busca booleana estrita `AND` retorne vazio.

### 2. Buscar fontes oficiais externas quando necessário
* **Problema:** Quando a base interna não contém o termo, a IA encerra o atendimento sem consultar o domínio oficial da Prefeitura.  
* **Solução:**  
  - Ativar o conector web oficial integrado (`utils/web_search.py`) filtrando estritamente domínios municipais e governamentais: `site:duquedecaxias.rj.gov.br OR site:saude.duquedecaxias.rj.gov.br`.  
  - Citar a URL da fonte oficial no rodapé da resposta sob o formato `[Fonte Oficial: portal.duquedecaxias.rj.gov.br]`.

### 3. Melhorar a classificação das demandas (Taxonomia Rigorosa)
* **Problema:** Mistura recorrente entre Ouvidoria, Zeladoria, e-SIC e serviços rotineiros.  
* **Solução:**  
  - **Zeladoria Urbana:** Serviços físicos iniciais de manutenção de vias, podas de árvores em rua, troca de lâmpadas de postes e desobstrução de bueiros.  
  - **Ouvidoria Geral:** Reclamações de serviços não executados após o prazo, denúncias de servidores, elogios e sugestões de governança.  
  - **e-SIC (LAI):** Pedidos de acesso a dados estatísticos, contratos, editais e documentos administrativos.  
  - **Serviços Administrativos:** Emissão de certidões, ITBI, IPTU e alvarás no balcão da Fazenda/Urbanismo.  
  - **Competências Externas:** Polícia Militar (190), Bombeiros (193), concessionárias e órgãos federais.

### 4. Direcionar corretamente ao órgão responsável
* **Problema:** Inferências arbitrárias atribuindo demandas a secretarias não citadas (ex: atribuir funcionário fantasma à Secretaria da Mulher).  
* **Solução:**  
  - Implementar uma trava de segurança no Prompt de Geração: *"Se a consulta não especificar a secretaria ou se o serviço não for exclusivo de uma pasta, nunca atribua a responsabilidade a uma secretaria setorial arbitrária. Em caso de dúvidas funcionais gerais, direcione à Ouvidoria Geral ou Secretaria Municipal de Governo."*

### 5. Informar o canal correto para resolução com Links Parametrizados
* **Problema:** Citar o aplicativo Colab sem disponibilizar o link de download/acesso e sem orientar o tema/assunto a ser selecionado.  
* **Solução:**  
  - Criar um **Dicionário Canônico de Links Oficiais**:  
    - **Colab Geral:** `https://duquedecaxias.colab.re/`  
    - **Portal Cidadão Ouvidoria:** `https://portal.duquedecaxias.rj.gov.br/ouvidoria`  
    - **Portal do Contribuinte (Fazenda):** `https://portalcontribuinte.duquedecaxias.rj.gov.br/`  
    - **e-SIC Municipal:** `https://duquedecaxias.rj.gov.br/e-sic`  
    - **Saúde (Unidades):** `https://saude.duquedecaxias.rj.gov.br/unidades-de-saude.php`  
  - Na resposta, indicar sempre a trilha de navegação:  
    `👉 Abra o aplicativo Colab > Selecione o Tema [X] > Escolha o Assunto [Y] > [Link do Serviço]`

### 6. Melhorar a compreensão do contexto da conversa (Gestão de Multi-turno)
* **Problema:** A IA repete perguntas já respondidas pelo munícipe ou esquece dados informados no turno anterior (conforme ocorrido no Caso 07).  
* **Solução:**  
  - Injetar no estado do grafo (`AgentState`) uma memória estruturada de dados contextuais preenchidos (campos de contexto (slots)) (`campos de contexto (slots): {bairro, logradouro, categoria, tipo_denuncia}`).  
  - O classificador deve avaliar a mensagem do munícipe em conjunto com a última pergunta feita pelo sistema, impedindo que o fluxo seja reiniciado do zero.

### 7. Melhorar o tratamento de múltiplas perguntas num único prompt
* **Problema:** Se o cidadão faz 3 ou 4 pedidos juntos, a IA responde um e ignora os demais.  
* **Solução:**  
  - Implementar o componente **Analisador de Múltiplas Intenções (Multi-Intent Parser)**:  
    1. Identifica delimitadores sintáticos (*"além disso"*, *"também gostaria"*, *"e por último"*, numerações);  
    2. Divide a entrada em `N` sub-perguntas;  
    3. Executa o RAG individualmente para cada uma;  
    4. Concatena as respostas em seções numeradas (1, 2, 3...) mantendo total independência temática.

### 8. Melhorar a concatenação de informações de diferentes bases
* **Problema:** Respostas fragmentadas quando parte da informação está na Fazenda e parte na Saúde (conforme Caso 08).  
* **Solução:**  
  - No módulo de fusão (RRF), permitir que candidatos de diferentes categorias administrativas convivam no contexto enviado ao modelo de linguagem, orientando o modelo a estruturar a resposta em tópicos departamentais separados.

### 9. Tornar as respostas mais resolutivas (O que, onde e como fazer)
* **Problema:** Apenas dizer quem é a secretaria sem fornecer o plano de ação prático para o munícipe.  
* **Solução:**  
  - Padronizar toda resposta resolutiva com o roteiro de 4 pilares:  
    1. **O que é / Órgão Responsável** (em negrito);  
    2. **Onde Solicitar** (endereço físico ou link direto);  
    3. **Documentos Obrigatórios** (kit de identificação e comprovantes);  
    4. **Prazos e Custos** (gratuidade ou valor da taxa).

### 10. Evitar informações desnecessárias ou inadequadas
* **Problema:** Frases redundantes (*"não especificado no contexto"*, *"ligue antes para saber os documentos"*) ou conselhos combativos que instiguem o munícipe a confrontar servidores na regulação do posto.  
* **Solução:**  
  - Adicionar filtro de pós-processamento de texto (Barreira de Segurança de Saída (Output Guardrail)) para remover strings mecânicas de metadados nulos e instruções de atrito com a administração pública.

### 11. Melhorar a orientação por localização (Motor Geoespacial)
* **Problema:** Indicar equipamentos sem considerar a proximidade física do cidadão.  
* **Solução:**  
  - Conectar os 443 equipamentos públicos catalogados no arquivo `equipamentos.json` (que já possuem latitude e longitude conferidas) a uma rotina de ordenação por distância euclidiana/cálculo geográfico de distância (Haversine), retornando as unidades mais próximas com indicação de bairro e rota no mapa.

### 12. Melhorar a interface do chat e estética visual das respostas
* **Problema:** Falta de suporte a `Shift + Enter` para quebra de parágrafo no chat e ausência de uma identidade visual padronizada com uso de emoticons institucionais.  
* **Solução:**  
  - **Frontend:** Atualizar o manipulador de eventos do teclado no arquivo de script do chat web:  
    ```javascript
    textarea.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        enviarMensagem();
      }
    });
    ```  
  - **Padrão Estético de Resposta do DUQUE IA:**  
    Adotar um gabarito visual uniforme com hierarquia limpa, títulos em caixa alta suave, tópicos com marcadores e emoticons temáticos oficiais:  
    - 🏛️ **Órgão Responsável**  
    - 📍 **Onde Solicitar / Unidade Mais Próxima**  
    - 📋 **Documentos Necessários**  
    - ⏱️ **Prazo e Custo**  
    - 📲 **Canais Digitais e Links Oficiais**

---

## 📋 Conclusão e Próximos Passos

Este diagnóstico demonstra que o núcleo do **DUQUE IA** já opera com alta precisão factual quando as regras estão canonicamente mapeadas (como demonstrado nos Casos 02, 03 e 23). As oportunidades de melhoria concentram-se no refinamento do **roteamento múltiplos turnos de conversa (multi-turno)**, na **decomposição de prompts múltiplos**, no **ajuste fino dos barreiras de segurança jurídica (barreiras de segurança (guardrails))** e na **integração do cálculo de proximidade geográfica dos 443 equipamentos cadastrados**.

Todas as recomendações deste documento foram formuladas de forma puramente consultiva e analítica, preservando integralmente o código e os arquivos existentes no projeto até que sejam aprovadas para a fase de implementação.
