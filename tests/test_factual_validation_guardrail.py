"""
tests/test_factual_validation_guardrail.py
=========================================
Bateria de testes unitários e de integração para validação factual estrita (Pilar 1).
Verifica se o Output Guardrail bloqueia alucinações de telefones, e-mails, ofensas
e vazamentos de CPF sem prejudicar respostas legítimas fundamentadas no contexto oficial.
"""

import os
import sys

# Garante o path do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.guardrails import (
    check_output_guardrail,
    extract_candidate_phones,
    is_phone_grounded
)
from config.settings import OUVIDORIA_CONTACTS


def test_extract_candidate_phones():
    """Valida a extração correta de telefones e a exclusão de anos/mandatos."""
    text = (
        "O mandato 2025-2028 foi iniciado. Entre 1990-1994 ocorreram reformas. "
        "Telefone oficial: (21) 2652-3835. WhatsApp: (21) 99824-5903. "
        "Fixo local: 3656-6697. Falso: (21) 3456-7890. Celular falso: 98765-4321."
    )
    phones = extract_candidate_phones(text)
    
    # 2025-2028 e 1990-1994 NÃO devem ser extraídos como telefones
    assert "2025-2028" not in phones
    assert "1990-1994" not in phones
    
    # Telefones reais e falsos devem ser capturados para verificação
    assert any("2652-3835" in p for p in phones)
    assert any("99824-5903" in p for p in phones)
    assert any("3656-6697" in p for p in phones)
    assert any("3456-7890" in p for p in phones)
    assert any("98765-4321" in p for p in phones)


def test_phone_grounding_official_contacts():
    """Valida que telefones oficiais e códigos de emergência são sempre aprovados."""
    context = "Horário de atendimento das 8h às 17h."
    
    # Telefones da Ouvidoria Geral
    assert is_phone_grounded(OUVIDORIA_CONTACTS["telefone"], context) is True
    assert is_phone_grounded(OUVIDORIA_CONTACTS["whatsapp"], context) is True
    assert is_phone_grounded("2652-3835", context) is True
    assert is_phone_grounded("99824-5903", context) is True
    
    # Códigos de emergência
    assert is_phone_grounded("190", context) is True
    assert is_phone_grounded("192", context) is True
    assert is_phone_grounded("193", context) is True
    assert is_phone_grounded("199", context) is True
    assert is_phone_grounded("2253-1177", context) is True  # Disque Denúncia


def test_phone_grounding_from_context():
    """Valida que telefones presentes no contexto recuperado são aprovados."""
    context = "O posto de saúde funciona de 8h às 17h. Telefone para agendamento: (21) 2672-1234."
    assert is_phone_grounded("(21) 2672-1234", context) is True
    assert is_phone_grounded("2672-1234", context) is True


def test_phone_grounding_rejects_hallucinations():
    """Valida que números de telefone alucinados pelo modelo são rejeitados."""
    context = "Para emissão de IPTU, compareça à Secretaria de Fazenda."
    
    fake_landline = "(21) 2699-9999"
    fake_cellphone = "98888-7777"
    fake_general = "(21) 3333-4444"
    
    assert is_phone_grounded(fake_landline, context) is False
    assert is_phone_grounded(fake_cellphone, context) is False
    assert is_phone_grounded(fake_general, context) is False


def test_output_guardrail_blocks_hallucinated_phone():
    """Valida que o guardrail de saída bloqueia respostas com telefones inventados."""
    context = "A vacina contra gripe está disponível em todas as UBS de segunda a sexta."
    
    good_answer = (
        "A vacinação ocorre nas Unidades Básicas de Saúde (UBS). "
        "Para mais detalhes, contate a **Ouvidoria Geral**: (21) 2652-3835."
    )
    assert check_output_guardrail("onde vacinar", good_answer, None, context=context) is True
    
    bad_answer = (
        "A vacinação ocorre nas UBS. "
        "Ligue para o posto pelo telefone (21) 3777-8899 e tire suas dúvidas."
    )
    assert check_output_guardrail("onde vacinar", bad_answer, None, context=context) is False


def test_output_guardrail_blocks_hallucinated_email():
    """Valida que o guardrail de saída bloqueia respostas com e-mails fictícios."""
    context = "O IPTU pode ser pago nos bancos credenciados."
    
    bad_answer = (
        "Para solicitar o boleto do IPTU, envie um e-mail para cobranca.iptu.caxias@gmail.com."
    )
    assert check_output_guardrail("segunda via iptu", bad_answer, None, context=context) is False
    
    good_answer = (
        "Para mais informações sobre o IPTU, contate a **Ouvidoria Geral** pelo e-mail "
        "ouvidoria@duquedecaxias.rj.gov.br."
    )
    assert check_output_guardrail("segunda via iptu", good_answer, None, context=context) is True


def test_output_guardrail_blocks_cpf_leak():
    """Valida que vazamento acidental de CPF na resposta é interceptado."""
    bad_answer = "O protocolo do cidadão com CPF 123.456.789-00 está em análise."
    assert check_output_guardrail("consulta protocolo", bad_answer, None) is False


def test_output_guardrail_blocks_profanity():
    """Valida que ofensas geradas ou repetidas pelo modelo são interceptadas sem bypass."""
    # Teste mesmo com a palavra 'prefeitura' presente na frase (anteriormente causava bypass falso)
    bad_answer = "A prefeitura de Duque de Caxias informa que você é um burro e idiota."
    assert check_output_guardrail("teste", bad_answer, None) is False


if __name__ == "__main__":
    print("\n=======================================================")
    print("   TESTES DE VALIDAÇÃO FACTUAL E GROUNDING (PILAR 1)   ")
    print("=======================================================")
    test_extract_candidate_phones()
    print("✓ test_extract_candidate_phones: PASS")
    test_phone_grounding_official_contacts()
    print("✓ test_phone_grounding_official_contacts: PASS")
    test_phone_grounding_from_context()
    print("✓ test_phone_grounding_from_context: PASS")
    test_phone_grounding_rejects_hallucinations()
    print("✓ test_phone_grounding_rejects_hallucinations: PASS")
    test_output_guardrail_blocks_hallucinated_phone()
    print("✓ test_output_guardrail_blocks_hallucinated_phone: PASS")
    test_output_guardrail_blocks_hallucinated_email()
    print("✓ test_output_guardrail_blocks_hallucinated_email: PASS")
    test_output_guardrail_blocks_cpf_leak()
    print("✓ test_output_guardrail_blocks_cpf_leak: PASS")
    test_output_guardrail_blocks_profanity()
    print("✓ test_output_guardrail_blocks_profanity: PASS")
    print("=======================================================")
    print("TODOS OS 8 TESTES DE VALIDAÇÃO FACTUAL APROVADOS! 🎯")
    print("=======================================================\n")
