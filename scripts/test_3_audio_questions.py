# -*- coding: utf-8 -*-
"""
test_3_audio_questions.py — DUQUE IA
======================================
Executa o teste oficial de resposta em áudio com 3 perguntas reais do cidadão:
1. Castração de cães / Proteção Animal
2. Zeladoria Urbana / Tapa-Buraco em Imbariê
3. Contatos da Ouvidoria Geral (WhatsApp / Telefone / Sede)

Gera os áudios nativos em WAV (24kHz Studio Quality) via Gemini TTS,
salva na pasta public/audio/ e docs/audio_demonstracao/,
e cria uma página HTML interativa para reprodução imediata.
"""

import os
import sys
import json
import time
import shutil

# Configurar stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from voice.voice_router import VoiceRouter

DEMO_AUDIO_DIR = os.path.join(ROOT_DIR, "docs", "audio_demonstracao")
PUBLIC_AUDIO_DIR = os.path.join(ROOT_DIR, "public", "audio")
PLAYER_HTML = os.path.join(ROOT_DIR, "docs", "player_audio_respostas.html")
PLAYER_ROOT_HTML = os.path.join(ROOT_DIR, "player_audio_respostas.html")

os.makedirs(DEMO_AUDIO_DIR, exist_ok=True)
os.makedirs(PUBLIC_AUDIO_DIR, exist_ok=True)


def main():
    print("=" * 70)
    print("DUQUE IA — TESTE DE RESPOSTA EM ÁUDIO (3 PERGUNTAS)")
    print("Motor TTS: Gemini Interactions API (gemini-3.1-flash-tts-preview)")
    print("Formato: Áudio Nativo PCM 24.000 Hz / RIFF WAV")
    print("=" * 70)

    router = VoiceRouter()

    test_cases = [
        {
            "id": "AUDIO_01",
            "categoria": "Proteção Animal & Zoonoses",
            "pergunta": "Como faço para castrar meu cachorro de graça na prefeitura?",
            "persona": "saude",  # Voz Vindemiatrix
            "descricao": "Consulta sobre castração gratuita, documentos e agendamento presencial no Jardim Primavera."
        },
        {
            "id": "AUDIO_02",
            "categoria": "Zeladoria Urbana & Vias Públicas",
            "pergunta": "Tem um buraco enorme na minha rua em Imbariê, como peço para tapar?",
            "persona": "duque_ia",  # Voz Charon
            "descricao": "Solicitação de operação tapa-buraco e orientação de registro no aplicativo Colab com fotos."
        },
        {
            "id": "AUDIO_03",
            "categoria": "Ouvidoria Geral & Cidadania",
            "pergunta": "Qual é o WhatsApp e o telefone da Ouvidoria de Duque de Caxias?",
            "persona": "ouvidoria",  # Voz Charon
            "descricao": "Canais oficiais de contato (Telefone fixo, WhatsApp, Colab e endereço na Alameda Esmeralda)."
        }
    ]

    results = []

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[{idx}/3] Testando Pergunta {tc['id']}: '{tc['pergunta']}'")
        t0 = time.time()

        res_json = router.process_input(
            input_value=tc["pergunta"],
            conversation_id=f"voice_test_{tc['id'].lower()}",
            generate_audio=True,
            output_audio_dir=PUBLIC_AUDIO_DIR
        )

        elapsed = time.time() - t0

        try:
            data = json.loads(res_json)
        except Exception:
            data = {"answer": res_json}

        answer_text = data.get("answer", "")
        audio_rel_url = data.get("response_audio_url", "")
        audio_filename = os.path.basename(audio_rel_url) if audio_rel_url else ""
        source_audio_path = os.path.join(ROOT_DIR, "public", audio_rel_url.lstrip("/")) if audio_rel_url else ""
        
        dest_filename = f"{tc['id'].lower()}_{audio_filename}" if audio_filename else ""
        dest_audio_path = os.path.join(DEMO_AUDIO_DIR, dest_filename) if dest_filename else ""

        file_size_bytes = 0
        file_size_kb = 0.0
        audio_exists = False

        if source_audio_path and os.path.exists(source_audio_path):
            file_size_bytes = os.path.getsize(source_audio_path)
            file_size_kb = round(file_size_bytes / 1024, 1)
            audio_exists = True
            # Copia para docs/audio_demonstracao/ com nome identificável
            shutil.copyfile(source_audio_path, dest_audio_path)
            print(f"  -> [OK] Áudio gerado com sucesso!")
            print(f"  -> Arquivo: {dest_audio_path} ({file_size_kb} KB)")
        else:
            print(f"  -> [ERRO] Falha na geração do áudio: {data.get('response_audio_error')}")

        result_item = {
            "id": tc["id"],
            "categoria": tc["categoria"],
            "pergunta": tc["pergunta"],
            "descricao": tc["descricao"],
            "persona": tc["persona"],
            "answer_text": answer_text,
            "audio_filename": dest_filename,
            "audio_path_public": source_audio_path,
            "audio_path_demo": dest_audio_path,
            "file_size_kb": file_size_kb,
            "elapsed_seconds": round(elapsed, 2),
            "status": "OK" if audio_exists else "ERROR"
        }
        results.append(result_item)

    # 4. Gera Página HTML Interativa com reprodutor de áudio integrado
    build_player_html(results)

    # 5. Salva JSON com o relatório
    json_out = os.path.join(DEMO_AUDIO_DIR, "relatorio_teste_audio_3_perguntas.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("TESTE DE ÁUDIO CONCLUÍDO COM SUCESSO!")
    print(f"Relatório JSON: {json_out}")
    print(f"Player HTML interativo: {PLAYER_ROOT_HTML}")
    print("=" * 70)


def build_player_html(results):
    items_html = []
    for r in results:
        audio_rel = f"docs/audio_demonstracao/{r['audio_filename']}"
        items_html.append(f"""
        <div class="audio-card">
          <div class="card-header">
            <span class="badge-id">#{r['id']}</span>
            <span class="category-name">{r['categoria']}</span>
            <span class="badge-time">Tempo: {r['elapsed_seconds']}s</span>
            <span class="badge-size">{r['file_size_kb']} KB (WAV 24kHz)</span>
          </div>

          <div class="question-row">
            <span class="q-icon">💬</span>
            <strong>Pergunta:</strong> "{r['pergunta']}"
          </div>

          <div class="player-wrapper">
            <div class="player-title">🔊 Ouça a Resposta em Áudio Sintetizada pelo Gemini TTS:</div>
            <audio controls preload="auto" class="audio-element">
              <source src="{audio_rel}" type="audio/wav">
              <source src="public/audio/{r['audio_filename'].replace(r['id'].lower() + '_', '')}" type="audio/wav">
              Seu navegador não suporta reprodução de áudio HTML5.
            </audio>
          </div>

          <div class="answer-wrapper">
            <div class="ans-title">📄 Conteúdo Oficial Transcrito:</div>
            <div class="ans-body">{r['answer_text'].replace(chr(10), '<br>')}</div>
          </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>DUQUE IA — Demonstração de Respostas em Áudio (TTS Nativo)</title>
  <style>
    body {{
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      margin: 0;
      padding: 24px;
      line-height: 1.5;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
    }}
    .header {{
      text-align: center;
      padding-bottom: 24px;
      border-bottom: 1px solid #334155;
      margin-bottom: 30px;
    }}
    .header h1 {{
      margin: 0 0 8px 0;
      color: #38bdf8;
      font-size: 26px;
      letter-spacing: -0.5px;
    }}
    .header p {{
      margin: 0;
      color: #94a3b8;
      font-size: 14px;
    }}
    .audio-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }}
    .card-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 14px;
      border-bottom: 1px solid #334155;
      padding-bottom: 10px;
    }}
    .badge-id {{
      background: #0284c7;
      color: #fff;
      font-weight: 800;
      font-size: 12px;
      padding: 3px 8px;
      border-radius: 6px;
    }}
    .category-name {{
      font-weight: 700;
      color: #e2e8f0;
      font-size: 15px;
    }}
    .badge-time, .badge-size {{
      background: #334155;
      color: #cbd5e1;
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 4px;
      margin-left: auto;
    }}
    .badge-size {{
      margin-left: 6px;
      background: #065f46;
      color: #a7f3d0;
    }}
    .question-row {{
      background: #0f172a;
      border-left: 4px solid #38bdf8;
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      font-size: 15px;
      color: #f1f5f9;
      margin-bottom: 16px;
    }}
    .player-wrapper {{
      background: #090d16;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 16px;
    }}
    .player-title {{
      font-size: 12px;
      color: #38bdf8;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }}
    audio {{
      width: 100%;
      height: 40px;
      outline: none;
    }}
    .answer-wrapper {{
      background: #182234;
      border-radius: 8px;
      padding: 14px;
      font-size: 13px;
      color: #cbd5e1;
    }}
    .ans-title {{
      font-weight: 700;
      color: #94a3b8;
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .ans-body {{
      max-height: 180px;
      overflow-y: auto;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Prefeitura Municipal de Duque de Caxias — DUQUE IA</h1>
      <p>Demonstração Prática de Respostas em Áudio (Voz Sintetizada Nativa Gemini Studio 24.000 Hz)</p>
    </div>
    {"".join(items_html)}
  </div>
</body>
</html>
"""
    with open(PLAYER_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(PLAYER_ROOT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    main()

