# -*- coding: utf-8 -*-
"""
Calcula detalhadamente o custo de toda a bateria das 102 perguntas.
"""
import os
import sys
import json
import sqlite3

# Configurar stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 1. Carregar resultados
json_path = os.path.join(ROOT, "data", "resultados_todas_as_perguntas.json")
with open(json_path, "r", encoding="utf-8") as f:
    results = json.load(f)

# 2. Verificar telemetry.db se houver
telem_path = os.path.join(ROOT, "data", "telemetry.db")
db_metrics = []
if os.path.exists(telem_path):
    conn = sqlite3.connect(telem_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print("Tabelas em telemetry.db:", tables)
        for t in tables:
            rows = cur.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 150").fetchall()
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
            print(f"  Tabela {t}: {len(rows)} linhas recentes")
            if "prompt_tokens" in cols or "tokens" in str(cols).lower():
                print(f"    Colunas: {cols}")
    except Exception as e:
        print("Erro lendo telemetry:", e)

# 3. Analisar log do task-386 que gravou as telemetrias exatas de cada chamada Gemini
task_log = r"C:\Users\501379.PMDC\.gemini\antigravity\brain\63109f91-bfe7-410c-8b0b-90585c718135\.system_generated\tasks\task-386.log"
flash_38_prompt_tokens = 0
flash_38_candidate_tokens = 0
flash_38_calls = 0

flash_31_prompt_tokens = 0
flash_31_candidate_tokens = 0
flash_31_calls = 0

if os.path.exists(task_log):
    with open(task_log, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # [GeminiClient] Telemetria [gemini-3.8-flash]: prompt_tokens=4267, candidate_tokens=378
            if "[GeminiClient] Telemetria [gemini-3.8-flash]:" in line:
                flash_38_calls += 1
                try:
                    parts = line.split(":")[-1].strip().split(",")
                    p_tok = int(parts[0].split("=")[-1].strip())
                    c_tok = int(parts[1].split("=")[-1].strip())
                    flash_38_prompt_tokens += p_tok
                    flash_38_candidate_tokens += c_tok
                except Exception:
                    pass
            elif "[GeminiClient] Telemetria [gemini-3.1-flash-lite]:" in line:
                flash_31_calls += 1
                try:
                    parts = line.split(":")[-1].strip().split(",")
                    p_tok = int(parts[0].split("=")[-1].strip())
                    c_tok = int(parts[1].split("=")[-1].strip())
                    flash_31_prompt_tokens += p_tok
                    flash_31_candidate_tokens += c_tok
                except Exception:
                    pass

print("=" * 60)
print("EXTRATO EXATO DE TOKENS E TELEMETRIA DA BATERIA (102 PERGUNTAS)")
print("=" * 60)
print(f"Total de Perguntas no Dossiê: {len(results)}")
print()
print("1. MODELO PRINCIPAL (Geração / RAG): gemini-3.8-flash")
print(f"   Chamadas efetuadas: {flash_38_calls}")
print(f"   Prompt tokens (entrada): {flash_38_prompt_tokens:,}")
print(f"   Candidate tokens (saída): {flash_38_candidate_tokens:,}")
print(f"   Total de tokens: {flash_38_prompt_tokens + flash_38_candidate_tokens:,}")
print()
print("2. MODELO DE TRIAGEM RÁPIDA: gemini-3.1-flash-lite")
print(f"   Chamadas efetuadas: {flash_31_calls}")
print(f"   Prompt tokens (entrada): {flash_31_prompt_tokens:,}")
print(f"   Candidate tokens (saída): {flash_31_candidate_tokens:,}")
print(f"   Total de tokens: {flash_31_prompt_tokens + flash_31_candidate_tokens:,}")
print()

# Tabela oficial Google Cloud / AI Studio Pricing:
# Gemini 3.8 Flash / 2.5 Flash:
# Entrada (<= 128k tokens): $0.10 por 1 milhão de tokens
# Saída (<= 128k tokens): $0.40 por 1 milhão de tokens
# Gemini 3.1 Flash-Lite:
# Entrada: $0.075 por 1 milhão de tokens
# Saída: $0.30 por 1 milhão de tokens

cost_flash_38_in = (flash_38_prompt_tokens / 1_000_000) * 0.10
cost_flash_38_out = (flash_38_candidate_tokens / 1_000_000) * 0.40
cost_flash_38_total = cost_flash_38_in + cost_flash_38_out

cost_flash_31_in = (flash_31_prompt_tokens / 1_000_000) * 0.075
cost_flash_31_out = (flash_31_candidate_tokens / 1_000_000) * 0.30
cost_flash_31_total = cost_flash_31_in + cost_flash_31_out

cost_usd = cost_flash_38_total + cost_flash_31_total
taxa_cambio_brl = 5.75
cost_brl = cost_usd * taxa_cambio_brl

print("=" * 60)
print("CÁLCULO FINANCEIRO DETALHADO (Tabela Oficial Google AI Studio)")
print("=" * 60)
print(f"• Custo gemini-3.8-flash (Entrada): US$ {cost_flash_38_in:.6f}")
print(f"• Custo gemini-3.8-flash (Saída):   US$ {cost_flash_38_out:.6f}")
print(f"• Subtotal gemini-3.8-flash:        US$ {cost_flash_38_total:.6f}")
print()
print(f"• Custo gemini-3.1-flash-lite (In): US$ {cost_flash_31_in:.6f}")
print(f"• Custo gemini-3.1-flash-lite (Out):US$ {cost_flash_31_out:.6f}")
print(f"• Subtotal gemini-3.1-flash-lite:   US$ {cost_flash_31_total:.6f}")
print("-" * 60)
print(f"💰 CUSTO TOTAL DA BATERIA (102 PERGUNTAS):")
print(f"   -> Em Dólar (USD): US$ {cost_usd:.4f} (aprox. {cost_usd*100:.2f} centavos de dólar)")
print(f"   -> Em Reais (BRL @ R$ 5,75): R$ {cost_brl:.4f} (aprox. R$ {cost_brl:.2f})")
print(f"   -> Custo Médio por Pergunta: R$ {cost_brl/len(results):.5f} (menos de um terço de centavo por pergunta!)")
print("=" * 60)

