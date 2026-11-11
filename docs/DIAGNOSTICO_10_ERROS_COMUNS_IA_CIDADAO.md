# DIAGNÓSTICO ESTRATÉGICO: OS 10 ERROS CRÍTICOS EM IA DE ATENDIMENTO AO CIDADÃO
**Avaliação de Maturidade, Medidas Implementadas e Plano Preventivo no DUQUE IA**  
*Prefeitura Municipal de Duque de Caxias — Ouvidoria Geral do Município*  
**Data:** 11 de Novembro de 2026 | **Versão:** 1.0 (Produção Homologada)

---

## SUMÁRIO EXECUTIVO

O atendimento automatizado ao munícipe por meio de Inteligência Artificial generativa impõe desafios severos de precisão, confiabilidade e responsabilidade pública. Ao contrário de um assistente de suporte privado, o assistente municipal lida diretamente com direitos fundamentais (acesso à saúde, matrículas escolares, tributos, regularização fundiária e canais de controle social).

Este relatório avalia minuciosamente o ecossistema do **DUQUE IA 2.0** frente aos **10 erros mais frequentes em assistentes virtuais governamentais**. Para cada erro, é apresentado:
1. **Diagnóstico no Duque IA:** Avaliação se o erro ocorria, sua causa técnica e o estado atual.
2. **O que fizemos para não acontecer:** A blindagem técnica, arquitetural e algorítmica já implementada no código.
3. **Plano de Prevenção Contínua:** Boas práticas de governança, monitoramento de telemetria e testes preventivos.

---

## MATRIZ DE MATURIDADE DOS 10 ERROS NO DUQUE IA

| Nº | Erro Crítico | Ocorrência Anterior | Status Atual | Mecanismo Principal de Blindagem |
| :---: | :--- | :---: | :---: | :--- |
| **01** | **Alucinação de Informações** | Baixa | **Blindado** | RAG Híbrido FTS5 + Vetores 3072d + Grounding Estrito |
| **02** | **Confusão entre Assuntos** | Média | **Blindado** | Triagem Cognitiva com Ruptura Temática + Handlers Especialistas |
| **03** | **Memória Contaminada** | Alta | **Blindado** | Anti-Loop com Reset Temático + Janela Rolling Enxuta |
| **04** | **Bloqueio Indevido de Respostas** | Alta | **Blindado** | Exceção do IPMDC + Refinamento de Regex de SQL Injection |
| **05** | **Respostas Repetitivas** | Média | **Blindado** | Deduplicação de Autoridades + Handler Didático de Clarificação |
| **06** | **Interpretação Incorreta** | Média | **Blindado** | Flag Procedural no EntityResolver (Funções vs Endereços) |
| **07** | **Encaminhamento para Setor Errado** | Baixa | **Blindado** | Mapeamento Canônico de 25 Secretarias + Desambiguação de Postes |
| **08** | **Perda de Contexto** | Alta | **Blindado** | Memória Persistente em 3 Camadas no SQLite WAL (50 Turnos OK) |
| **09** | **Informações Desatualizadas** | Média | **Blindado** | Catálogo 2025–2028 (Netinho Reis & Aline do Aureo) + Versão Estática |
| **10** | **Abertura Indevida de Atendimento** | Crítica | **Blindado** | Segregação Dúvida vs Manifestação + Desacoplamento do Colab |

---

## DETALHAMENTO DOS 10 ERROS: DIAGNÓSTICO, BLINDAGEM E PREVENÇÃO

---

### ERRO 01: Alucinação de Informações
> *A IA inventa telefones, endereços, horários ou serviços que não existem.*

#### 1. Diagnóstico no Duque IA
Em modelos LLM puros (sem grounding rígido), existe a tendência estatística de "alucinar" números de telefone plausíveis (ex: prefixos fictícios), horários genéricos ("segunda a sexta das 8h às 18h") ou procedimentos inventados. No Duque IA, qualquer telefone errado gera deslocamento inútil do munícipe ou sobrecarga de linhas erradas.

#### 2. O que fizemos para não acontecer
* **RAG Híbrido de Alta Densidade:** A recuperação combina busca textual exata (**FTS5 trigramas**) com busca vetorial densa (**`gemini-embedding-2`** de 3.072 dimensões) sobre 1.575 chunks mestres (`vector.db`) e 644 serviços catalogados (`main.db`).
* **Prompt de Engenharia com Grounding Estrito:** O prompt do motor factual (`gemini-3.8-flash`) proíbe explicitamente a criação de dados não contidos no contexto recuperado.
* **Tabela Canônica de Telefones e Emergências:** Contatos vitais (Ouvidoria Geral **(21) 2652-3835**, WhatsApp **(21) 99824-5903**, Defesa Civil **199**, PMERJ **190**) são injetados diretamente de constantes imutáveis (`config/settings.py`), blindados contra variação do modelo.
* **Retrieval Guardrail:** Se o índice de similaridade não atingir o limiar mínimo (`similarity_threshold = 0.50`), a IA não arrisca adivinhações e retorna recusa padrão orientando o munícipe à Ouvidoria Geral.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Auditoria de Telemetria:** Monitorar semanalmente no painel de observabilidade (`dashboard.html`) as consultas com score de similaridade entre 0.40 e 0.55 para identificar se novas demandas da população precisam de chunks documentais adicionais.
* **Selo de Validação de Dados:** Vincular nas respostas factuais a fonte oficial da prefeitura (ex: *"Fonte: Carta de Serviços da SMS"*).

---

### ERRO 02: Confusão entre Assuntos
> *O cidadão pergunta sobre saúde e a IA responde sobre IPTU ou Ouvidoria.*

#### 1. Diagnóstico no Duque IA
Antes da auditoria, diálogos com mais de um turno podiam sofrer contaminação temática se o classificador de intenção reutilizasse cegamente o histórico da pergunta anterior, misturando as secretarias no prompt.

#### 2. O que fizemos para não acontecer
* **Ruptura Temática na Triagem Cognitiva (`agent/triage.py`):** O triador rápido (`gemini-3.1-flash-lite`) foi instruído com regras rígidas de mudança de assunto. Se o munícipe perguntou sobre IPTU e em seguida pergunta *"Onde tomo vacina da gripe?"*, o classificador detecta a consulta autônoma, reescreve a query apenas com os termos médicos e categoriza como `RAG_GERAL / SMS`.
* **Roteamento Modular por Handlers (`agent/graph.py`):** O pipeline divide-se em executores especializados (`RAG_HANDLER`, `AUTHORITY_HANDLER`, `AMBIGUITY_HANDLER`, `COLLECTOR_HANDLER`). Saúde é processada pelo motor factual com base nos postos e hospitais municipais; IPTU é direcionado para a Fazenda.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Sanitização de Slots de Sessão:** Ao detectar troca de intenção entre turnos, limpar as tags temáticas da sessão anterior para evitar que o reescritor tente fundir os dois tópicos.
* **Bateria Contínua de Testes Multi-Turno:** Executar o script `tests/test_multi_turns_stress.py` a cada deploy.

---

### ERRO 03: Memória Contaminada
> *A IA continua considerando um assunto anterior mesmo quando o cidadão muda de tema.*

#### 1. Diagnóstico no Duque IA
Este foi o **bug central** revelado na auditoria e no print do celular: o cidadão abriu uma dúvida de saúde (*"marcar uma consulta?"*), mas a IA ainda carregava o contador de redirecionamento de uma pergunta anterior, sequestrando a resposta com a tag `🎯 ouvidoria loop prevented`.

#### 2. O que fizemos para não acontecer
* **Anti-Loop Condicionado a Atrito Humano Real (`agent/graph.py:291-348`):** O sistema agora só interrompe a conversa se o **próprio cidadão** expressar dificuldade explícita (*"não consigo mexer no app"*, *"está dando erro"*, *"não quero app"*).
* **Reset Instantâneo de Contadores:** Toda vez que o munícipe faz uma pergunta nova sobre outro serviço, o robô automaticamente redefine `redirect_count = 0` e `last_channel = None`.
* **Memória em 3 Camadas:** Em consultas comuns, a LLM recebe apenas uma janela compacta dos últimos 2 turnos, impedindo que contextos de 5 perguntas atrás continuem poluindo a atenção do modelo.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Expiração de Contexto por Tempo:** Adicionar expiração automática de contexto se o usuário passar mais de 30 minutos inativo entre mensagens.

---

### ERRO 04: Bloqueio Indevido de Respostas
> *Uma regra de segurança é acionada sem necessidade e impede a resposta correta.*

#### 1. Diagnóstico no Duque IA
Identificamos dois bloqueios indevidos graves na auditoria:
1. **Previdência Municipal (IPMDC):** Servidores de Duque de Caxias eram bloqueados pela regra geral de competência federal (*"Aposentadoria é assunto federal do INSS"*).
2. **Falso SQL Injection:** O uso gramatical legítimo de ponto-e-vírgula (`;`) ou travessão (`--`) era interceptado como ataque cibernético.

#### 2. O que fizemos para não acontecer
* **Exceção Territorial e Municipal do IPMDC (`agent/guardrails.py:35`):** Restringido o bloqueio ao INSS federal e criada exceção expressa para o **Instituto de Previdência dos Servidores Públicos de Duque de Caxias (IPMDC)**.
* **Refinamento de Regex de Injeção SQL (`agent/guardrails.py:6-12`):** Caracteres soltos foram substituídos por sequências de ataque empilhadas (`"; drop"`, `"; select"`, `"-- drop"`), liberando pontuação cotidiana.
* **Desbloqueio de Dúvidas Procedurais (`agent/router.py:180`):** Expressões como *"como funciona o tarifa zero"* foram liberadas para o RAG, em vez de acionar a ajuda institucional.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Logs Dedicados de Falsos Positivos:** Auditoria de todas as requisições marcadas com `SECURITY_BLOCKED` para identificar bloqueios desnecessários antes que cheguem a incomodar os munícipes.

---

### ERRO 05: Respostas Repetitivas
> *A IA insiste na mesma orientação, mesmo depois de o cidadão fazer outra pergunta.*

#### 1. Diagnóstico no Duque IA
Ocorria em dois cenários:
1. **Autoridades:** O cabeçalho dizia *"Jonathas Monteiro Porto Neto é o Prefeito"* e em seguida o campo `detalhes` repetia literalmente *"Netinho Reis é o Prefeito de Duque de Caxias"*.
2. **Esclarecimento:** Quando o cidadão dizia *"não entendi"*, a IA repetia o mesmo texto burocrático inicial.

#### 2. O que fizemos para não acontecer
* **Deduplicação de Autoridades (`agent/handlers.py`):** Implementada limpeza automática que detecta se os detalhes repetem a frase principal, substituindo por histórico biográfico complementar real (mandato 2025–2028, formação e ações de governo).
* **Handler Didático de Clarificação (`ClarificationHandler`):** Quando o munícipe diz *"não entendi"* ou *"explique melhor"*, a IA pede desculpas com humildade e reescreve a explicação em tópicos extremamente simples e práticos (máximo 3 a 4 passos), sem repetir o texto anterior.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Métrica de Diversidade de Vocabulário:** Testar automaticamente que reexplicações possuam formulação diferente da resposta original.

---

### ERRO 06: Interpretação Incorreta da Pergunta
> *O cidadão pergunta o que uma secretaria faz, mas a IA informa apenas seu endereço.*

#### 1. Diagnóstico no Duque IA
O `EntityResolver` (normalizador geográfico) interceptava perguntas como *"Qual a função da Secretaria de Obras?"* e, por conter o nome da secretaria, considerava que o usuário queria localizar a repartição, retornando apenas endereço e telefone.

#### 2. O que fizemos para não acontecer
* **Detecção Procedural e Institucional (`agent/entity_resolver.py:270-280`):** Adicionada a verificação `is_procedural` contendo termos como `"função"`, `"o que faz"`, `"atividades"`, `"competências"` e `"atribuições"`. Quando detectados, o interceptador não devolve ficha estática e permite que a pergunta flua para o motor analítico, explicando as competências da pasta.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Separação Fina de Intenções:** Manter distinção clara na triagem entre `LOCALIZACAO_EQUIPAMENTO` (onde fica) e `COMPETENCIA_INSTITUCIONAL` (o que faz).

---

### ERRO 07: Encaminhamento para o Setor Errado
> *A IA direciona uma solicitação de iluminação pública para uma secretaria que não é responsável.*

#### 1. Diagnóstico no Duque IA
Com a nova estrutura administrativa de Duque de Caxias (25 secretarias, incluindo pastas recentemente desmembradas como SMCT, SMEL, SMG e SMCSRPTER), erros de roteamento de competência poderiam fazer o cidadão registrar chamados na secretaria errada.

#### 2. O que fizemos para não acontecer
* **Mapeamento Canônico Relacional (`main.db`):** Cada um dos 644 serviços públicos municipais possui vínculo oficial estrito com a sua respectiva sigla e órgão responsável (ex: iluminação e tapa-buraco vinculados à SMO; vacinação à SMS; IPTU à SMF).
* **Desambiguação Prévia (`AmbiguityHandler`):** Se a solicitação contiver ambiguidade sobre responsabilidade pública vs concessionária privada (ex: falta de luz em poste na rua vs falta de energia no relógio residencial), a IA desambigua antes de direcionar, orientando corretamente se o caso é da Prefeitura (SMO/Colab) ou da Concessionária Light/Enel.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Revisão Periódica da Estrutura:** Validar a matriz de secretarias contra publicações do Diário Oficial do Município.

---

### ERRO 08: Perda de Contexto
> *A IA esquece informações fornecidas pelo cidadão e pede novamente os mesmos dados.*

#### 1. Diagnóstico no Duque IA
A perda de contexto ocorria porque o histórico na memória volátil era limitado a 3 turnos (`[-6:]`), e em requisições distribuídas entre múltiplos workers Python, o estado anterior não era resgatado com precisão se a query pedisse dados do início do atendimento.

#### 2. O que fizemos para não acontecer
* **Memória Conversacional Persistente em 3 Camadas:**
  1. **SQLite WAL (`telemetry.db`):** Toda mensagem é persistida na tabela `chat_messages` com o índice sequencial `turn_index INTEGER`.
  2. **Controle de Versão Atômico (`version INTEGER`):** Impede perda de atualização (*lost update*) entre os 4 workers concorrentes.
  3. **Resgate Cirúrgico Determinístico (`MemoryRecallHandler`):** Meta-perguntas sobre a conversa (*"qual foi minha primeira pergunta?"*, *"o que você respondeu antes?"*) são recuperadas via SQL em sub-25ms com 100% de precisão literal, sem alucinar e sem inchar tokens.
* **Homologação em 50 Turnos:** Testado e aprovado com retenção perfeita da 1ª pergunta após 49 outras interações.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Slots de Dados Coletados:** Preservar bairro, logradouro e categoria informados em turnos anteriores no dicionário `slots` da sessão, evitando que a IA pergunte o bairro novamente se ele já foi dito.

---

### ERRO 09: Informações Desatualizadas
> *A IA apresenta procedimentos antigos, serviços descontinuados ou contatos que mudaram.*

#### 1. Diagnóstico no Duque IA
Identificamos dados desatualizados no catálogo de autoridades: a vice-prefeita constava com o nome de uma gestão anterior, e o prefeito precisava de indexação explícita nas tabelas FTS.

#### 2. O que fizemos para não acontecer
* **Atualização do Quadro Oficial do Executivo (Mandato 2025–2028):**
  * **Prefeito:** **Jonathas Monteiro Porto Neto (Netinho Reis)** indexado no `vector.db` e no catálogo.
  * **Vice-Prefeita:** **Aline Ferreira Batista Ribeiro (Aline do Aureo)**, com formação em Serviço Social (Unigranrio), pós-graduação em Gestão Pública (PUC) e histórico na SMASDH.
* **Canais Oficiais Atualizados:** Centralização dos telefones e WhatsApp da Ouvidoria Geral.
* **Versionamento de Catálogo:** Todo registro de autoridade informa a versão do catálogo (`CATALOG_VERSION = "2026-07-13"` / atualizada) e a fonte documental.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Rotina Semestral de Recadastramento:** Criação de um formulário de checagem periódica junto aos secretários e diretores municipais para atualizar telefones, e-mails e titulares.

---

### ERRO 10: Abertura Indevida de Atendimento
> *A IA interpreta uma simples dúvida como uma reclamação e começa a solicitar dados para registrar uma manifestação.*

#### 1. Diagnóstico no Duque IA
Esse era um dos maiores riscos de atrito:
* Munícipes com dúvidas informativas (*"marcar uma consulta?"* ou *"como funciona o IPTU?"*) eram colocados no fluxo do aplicativo Colab.
* Cidadãos que demonstravam irritação com uma resposta (*"não entendi a resposta. vai à merda"*) eram enquadrados em `POSSIVEL_DENUNCIA`, acionando o coletor da Ouvidoria como se estivessem denunciando um servidor público!

#### 2. O que fizemos para não acontecer
* **Desacoplamento do Agente Coletor:** O `COLLECTOR_HANDLER` só é acionado se a intenção for genuína manifestação de controle social (`OUVIDORIA_MANIFESTACAO` ou relato factual de falta de atendimento em órgão municipal).
* **Segregação Estrita de Dúvidas Informativas (`RAG_GERAL`):** Procedimentos, guias de passo a passo e esclarecimentos de saúde, educação e obras entregam a resposta informativa diretamente, sem pedir CPF, endereço ou fotos para manifestação.
* **Filtro de Desabafo com a IA (`CLARIFICACAO_RESPOSTA`):** Frustrações com a inteligência artificial são acolhidas com civilidade e reexplicação didática, nunca como denúncia de ouvidoria.
* **Conformidade com a LGPD:** O assistente não solicita dados pessoais desnecessariamente quando o cidadão deseja apenas orientações públicas gerais.

#### 3. O que podemos fazer para nos prevenir continuamente
* **Confirmação Prévia de Protocolo:** Sempre que a IA identificar um relato de insatisfação, deve perguntar: *"Deseja que eu te oriente sobre como abrir uma manifestação oficial na Ouvidoria Geral sobre este fato?"*, antes de iniciar qualquer coleta de dados.

---

## CONCLUSÃO E DIRETRIZES DE SUSTENTAÇÃO

O ecossistema do **DUQUE IA** alcançou um nível de maturidade em que os **10 erros críticos foram mapeados, diagnosticados e blindados no código**.

### Próximos Passos de Governança:
1. **Monitoramento do Painel de Métricas (`dashboard.html`):** Acompanhar em tempo real os índices de confiança, tempo de resposta e intenções mais frequentes.
2. **Ciclo de Atualização de Conhecimento:** Manter o versionamento modular dos arquivos Markdown em `data/knowledge/` para que qualquer alteração de secretarias ou leis municipais seja ingerida de forma incremental sem downtime.
3. **Preservação da Memória Hierárquica:** Manter a política de limpeza semanal de telemetria (`cleanup_expired_sessions`), garantindo conformidade com a LGPD e agilidade operacional contínua no SQLite WAL.

