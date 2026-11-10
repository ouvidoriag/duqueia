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

TEST_CASES = [
    {
        "id": "Caso 04",
        "query": "Encontrei um morador de rua desmaiado. Ele precisa de ajuda. Como posso ajuda-lo a prefeitura pode me auxiliar?",
        "history": [],
        "expected_keywords": ["192", "samu", "centro pop"]
    },
    {
        "id": "Caso 06",
        "query": "Tem um estabelecimnto perto da minha rua que está fedendo muito. Eles vendem carne!",
        "history": [],
        "expected_keywords": ["vigilância sanitária", "colab", "alimentos"]
    },
    {
        "id": "Caso 07",
        "query": "É uma casa de festas, tem uma pessoa que é um dono. Pode entrar quem pagar",
        "history": ["Relato de barulho excessivo vindo de uma festa com som alto"],
        "expected_keywords": ["190", "polícia militar", "meio ambiente"]
    },
    {
        "id": "Caso 11",
        "query": "Quero abrir uma demanda de falta de água na minha rua. Como posso fazer?",
        "history": [],
        "expected_keywords": ["águas do rio", "0800 195 0 195", "colab"]
    },
    {
        "id": "Caso 13",
        "query": "Quebrei o pé e moro em Jardim Primavera, Duque de Caxias. Gostaria de saber qual é o hospital de referência em ortopedia mais próximo onde posso procurar atendimento.",
        "history": [],
        "expected_keywords": ["adão pereira nunes", "saracuruna"]
    },
    {
        "id": "Caso 15",
        "query": "Templo religioso sem alvará: a Prefeitura pode interditar sumariamente? Quais licenças são necessárias e quais etapas administrativas existem?",
        "history": [],
        "expected_keywords": ["imunidade", "alvará", "bombeiros"]
    },
    {
        "id": "Caso 16",
        "query": "Recebi uma multa que considero indevida, mas não sei qual órgão municipal a aplicou. Como posso identificar o órgão responsável, consultar o processo administrativo e apresentar defesa ou recurso dentro do prazo?",
        "history": [],
        "expected_keywords": ["jari", "30 dias"]
    },
    {
        "id": "Caso 18",
        "query": "um amigo meu quer emagrecer, qual secretaria ele procura?",
        "history": [],
        "expected_keywords": ["saúde", "ubs", "nutri"]
    },
    {
        "id": "Caso 19",
        "query": "Tem uma lâmpada queimada na minha rua gerando escuridão e medo de assaltos.",
        "history": [],
        "expected_keywords": ["zeladoria", "iluminação pública"]
    },
    {
        "id": "Caso 21",
        "query": "Quero denunciar um funcionário fantasma, ele nunca aparece na unidade pra trabalhar, em horário de expediente... Não tenho registro, mas posso informar o nome e a unidade onde ele deveria trabalhar.",
        "history": [],
        "expected_keywords": ["ouvidoria", "denúncia", "sigilo"]
    }
]

print("=" * 70)
print("   TESTANDO OS CASOS DA AUDITORIA APÓS ATUALIZAÇÕES")
print("=" * 70)

for tc in TEST_CASES:
    cid = tc["id"]
    q = tc["query"]
    h = tc["history"]
    print(f"\n[{cid}] Pergunta: '{q[:60]}...'")
    try:
        conv_id = f"test_{cid.replace(' ', '_')}"
        res = agent.process_query(q, conversation_id=conv_id, history=h)
        ans = res.get("answer", "")
        print(f"   Intent: {res.get('intent_detected')} | Confiança: {res.get('confidence')}")
        print(f"   Resposta preview: {ans[:180].replace(chr(10), ' ')}...")
        
        # Validação de palavras esperadas
        ans_low = ans.lower()
        matches = [kw for kw in tc["expected_keywords"] if kw.lower() in ans_low]
        print(f"   Palavras-chave encontradas: {matches} / {tc['expected_keywords']}")
    except Exception as e:
        print(f"   ERRO: {e}")

print("\n[OK] Testes concluídos!")
