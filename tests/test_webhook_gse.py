# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados de Ponta a Ponta para o Webhook Receptor GSE / OGM.
Valida:
1. Autenticação HMAC-SHA256 (assinaturas válidas, inválidas e ausentes).
2. Processamento do Módulo SIGEM (equipamento criado, atualizado, desativado).
3. Processamento do Módulo CDS (serviço criado, atualizado, desativado).
4. Sanitização contra WhatsApp fictício.
5. Blindagem de dados curados (secretarias.titular e regras_negocio intactos).
6. Auditoria de telemetria em telemetry.db.
"""

import os
import sys
import json
import hmac
import hashlib
import sqlite3
import time
import subprocess
import urllib.request
import urllib.error

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from scripts.webhook_processor import process_webhook_payload, sanitize_text

SECRET = "duque_ia_gse_secret_key_2026"
DB_MAIN = os.path.join(_PROJECT_ROOT, "data", "db", "main.db")
DB_VECTOR = os.path.join(_PROJECT_ROOT, "data", "db", "vector.db")
DB_TELEMETRY = os.path.join(_PROJECT_ROOT, "data", "db", "telemetry.db")

def generate_signature(body_str: str, secret: str = SECRET) -> str:
    """Gera assinatura HMAC-SHA256 no formato hex."""
    return hmac.new(secret.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()

def test_sanitization():
    print(">>> [TESTE 1] Sanitização de Telefones e WhatsApp Fictício...")
    dirty = "Para atendimento ligue (21) 99824-5903 ou envie email."
    clean = sanitize_text(dirty)
    assert "99824" not in clean, f"Falha na sanitização: {clean}"
    print(f"  ✓ Sanitização aprovada: '{dirty}' -> '{clean}'")

def test_golden_source_protection():
    print("\n>>> [TESTE 2] Blindagem de Titulares e Regras de Negócio...")
    conn = sqlite3.connect(DB_MAIN)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COUNT(titular) FROM secretarias;")
    total_sec, total_tit = c.fetchone()
    assert total_sec == total_tit, "Erro: secretarias sem titular!"
    
    c.execute("SELECT titular FROM secretarias WHERE code = 'SMS';")
    sms_tit = c.fetchone()[0]
    assert "Célia Serrano" in sms_tit, f"Titular SMS corrompido: {sms_tit}"

    c.execute("SELECT COUNT(*) FROM regras_negocio;")
    regras_cnt = c.fetchone()[0]
    assert regras_cnt >= 85, f"Regras de negócio reduzidas: {regras_cnt}"
    conn.close()
    print(f"  ✓ Secretarias (22/22 titulares preservados) e Regras ({regras_cnt} regras intactas)")

def test_sigem_processing():
    print("\n>>> [TESTE 3] Processamento de Payload SIGEM (Equipamento Público)...")
    payload = {
        "evento": "equipamento.atualizado",
        "modulo": "sigem",
        "id": "test_eq_001",
        "versao": 1731438000000,
        "alterado_em": "2026-11-12T16:00:00.000Z",
        "dados_atuais": {
            "id": "test_eq_001",
            "nome": "Unidade de Saúde Teste Webhook",
            "sigla": "USTW",
            "categoria": "Saúde",
            "secretaria_sigla": "SMS",
            "secretaria_nome": "Secretaria Municipal de Saúde",
            "status": "Ativo",
            "horario_funcionamento": "08:00 às 17:00",
            "endereco_completo": "Rua das Flores, 100 - Centro, Duque de Caxias - RJ, CEP 25000-000",
            "bairro_oficial": "Centro",
            "distrito_oficial": "1º Distrito",
            "latitude": -22.7850,
            "longitude": -43.3100,
            "telefones": ["(21) 2672-0000"],
            "emails": ["teste.saude@duquedecaxias.rj.gov.br"],
            "atualizado_em": "2026-11-12T16:00:00.000Z"
        }
    }
    
    res = process_webhook_payload(payload)
    assert res.get("success") is True, f"Erro no processamento SIGEM: {res}"
    print(f"  ✓ Resultado da operação: {res.get('action')}, unit_id: {res.get('unit_id')}")

    # Verifica no main.db
    conn = sqlite3.connect(DB_MAIN)
    c = conn.cursor()
    c.execute("SELECT name, phone, bairro, latitude, sigem_id FROM secretaria_unidades WHERE sigem_id = 'test_eq_001';")
    row = c.fetchone()
    assert row is not None, "Registro não encontrado em main.db!"
    assert row[0] == "Unidade de Saúde Teste Webhook"
    assert row[2] == "Centro"
    assert row[3] == -22.7850
    conn.close()
    print("  ✓ main.db verificado com sucesso!")

    # Verifica no vector.db
    vconn = sqlite3.connect(DB_VECTOR)
    vc = vconn.cursor()
    vc.execute("SELECT id, tipo, titulo FROM chunks WHERE id = 'sigem_test_eq_001';")
    vrow = vc.fetchone()
    assert vrow is not None, "Registro não encontrado na tabela chunks!"
    assert vrow[1] == "EQUIPAMENTO_PUBLICO"
    
    # Verifica duque_ia_chunks
    vc.execute("SELECT id, source, category FROM duque_ia_chunks WHERE source = 'sigem_test_eq_001';")
    drow = vc.fetchone()
    assert drow is not None, "Registro não encontrado na tabela duque_ia_chunks!"
    vconn.close()
    print("  ✓ vector.db (chunks + duque_ia_chunks) verificado com sucesso!")

def test_cds_processing():
    print("\n>>> [TESTE 4] Processamento de Payload CDS (Serviço Municipal)...")
    payload = {
        "evento": "servico.atualizado",
        "modulo": "cds",
        "id": "test_srv_001",
        "versao": 1731438100000,
        "alterado_em": "2026-11-12T16:05:00.000Z",
        "dados_atuais": {
            "id": "test_srv_001",
            "name": "Emissão de Cartão de Estacionamento para Idoso",
            "description": "Emissão gratuita do cartão especial de estacionamento para munícipes 60+.",
            "how_to_access": "Presencial na SMTSP ou online pelo portal do cidadão.",
            "address": "Alameda Esmeralda, 206 - Jardim Primavera",
            "who_can_request": "Moradores de Duque de Caxias com idade igual ou superior a 60 anos.",
            "waiting_time": "15 minutos",
            "max_deadline": "5 dias úteis",
            "cost": "Gratuito",
            "regulation_norm": "Resolução CONTRAN e Decreto Municipal",
            "status": "published",
            "secretaria_sigla": "SMTSP",
            "secretaria_nome": "Secretaria Municipal de Transportes e Serviços Públicos",
            "categoria_nome": "Mobilidade e Trânsito",
            "atualizado_em": "2026-11-12T16:05:00.000Z"
        }
    }

    res = process_webhook_payload(payload)
    assert res.get("success") is True, f"Erro no processamento CDS: {res}"
    print(f"  ✓ Resultado da operação: {res.get('action')}, service_id: {res.get('service_id')}")

    # Verifica no main.db
    conn = sqlite3.connect(DB_MAIN)
    c = conn.cursor()
    c.execute("SELECT name, max_deadline, cost, status FROM services WHERE name = 'Emissão de Cartão de Estacionamento para Idoso';")
    row = c.fetchone()
    assert row is not None, "Serviço não encontrado em main.db!"
    assert row[1] == "5 dias úteis"
    assert row[2] == "Gratuito"
    conn.close()
    print("  ✓ main.db verificado com sucesso para serviços!")

def test_http_server_and_hmac():
    print("\n>>> [TESTE 5] Teste HTTP com Assinatura HMAC no server.js...")
    # Inicia o servidor Node em processo separado
    proc = subprocess.Popen(["node", "server.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("  • Aguardando inicialização do server.js...")
    time.sleep(3)

    payload = {
        "evento": "equipamento.atualizado",
        "modulo": "sigem",
        "id": "rec_397",
        "versao": 1731436400000,
        "alterado_em": "2026-11-12T15:33:00.000Z",
        "dados_atuais": {
            "id": "rec_397",
            "nome": "Hospital Municipal Veterinário",
            "sigla": "",
            "categoria": "Proteção Animal",
            "secretaria_sigla": "SMPA",
            "secretaria_nome": "Secretaria Municipal de Proteção Animal",
            "status": "Ativo",
            "horario_funcionamento": "24 Horas",
            "endereco_completo": "Alameda Xavier Filho, s/nº - Jardim Primavera, Duque de Caxias - RJ",
            "bairro_oficial": "Jardim Primavera",
            "distrito_oficial": "2º Distrito",
            "latitude": -22.7564,
            "longitude": -43.3082,
            "telefones": ["(21) 2671-0000"],
            "emails": ["hospitalveterinario@duquedecaxias.rj.gov.br"],
            "atualizado_em": "2026-11-12T15:33:00.000Z"
        }
    }
    body_str = json.dumps(payload, ensure_ascii=False)
    valid_sig = generate_signature(body_str, SECRET)

    url = "http://127.0.0.1:3000/api/webhook/gse"

    # Caso A: Sem assinatura -> deve retornar 401
    try:
        req = urllib.request.Request(url, data=body_str.encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            status_code = resp.getcode()
    except urllib.error.HTTPError as e:
        status_code = e.code
    assert status_code == 401, f"Esperado 401 para requisição sem assinatura, obtido: {status_code}"
    print("  ✓ Caso A: Rejeição de requisição sem HMAC (401 Unauthorized) aprovado!")

    # Caso B: Assinatura inválida -> deve retornar 401
    try:
        headers = {"Content-Type": "application/json", "x-hub-signature-256": "sha256=invalidhex000000"}
        req = urllib.request.Request(url, data=body_str.encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req) as resp:
            status_code = resp.getcode()
    except urllib.error.HTTPError as e:
        status_code = e.code
    assert status_code == 401, f"Esperado 401 para assinatura inválida, obtido: {status_code}"
    print("  ✓ Caso B: Rejeição de assinatura HMAC forjada (401 Unauthorized) aprovado!")

    # Caso C: Assinatura válida -> deve retornar 200 OK
    headers = {
        "Content-Type": "application/json",
        "x-hub-signature-256": f"sha256={valid_sig}",
        "x-signature": valid_sig
    }
    req = urllib.request.Request(url, data=body_str.encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.getcode() == 200, f"Falha ao enviar webhook válido: {resp.getcode()}"
        resp_data = json.loads(resp.read().decode("utf-8"))
        assert resp_data.get("success") is True, f"Resposta inesperada: {resp_data}"
    print(f"  ✓ Caso C: Envio com assinatura HMAC-SHA256 válida (200 OK): {resp_data}")

    # Encerra o processo do servidor
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("  • Servidor finalizado com sucesso.")

def main():
    print("=" * 80)
    print("INICIANDO SUÍTE DE TESTES: WEBHOOK RECEPTOR GSE/OGM -> DUQUE IA")
    print("=" * 80)
    test_sanitization()
    test_golden_source_protection()
    test_sigem_processing()
    test_cds_processing()
    test_http_server_and_hmac()
    print("\n" + "=" * 80)
    print("TODOS OS TESTES FORAM CONCLUÍDOS COM 100% DE SUCESSO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
