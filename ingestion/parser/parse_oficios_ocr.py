"""
==============================================================================
    DUQUE IA - OCR DE OFICIOS VIA GEMINI VISION (sem Tesseract)
==============================================================================
Extrai texto de PDFs escaneados usando a API multimodal do Gemini.
Envia cada pagina como imagem e pede ao modelo para transcrever.

Isso substitui Tesseract OCR local, usando IA na nuvem.

Uso:
  python ingestion/parser/parse_oficios_ocr.py                     # todos
  python ingestion/parser/parse_oficios_ocr.py --only 000113       # um so
  python ingestion/parser/parse_oficios_ocr.py --test              # 3 menores
==============================================================================
"""

import io
import os
import sys
import json
import sqlite3
import time
import base64

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

from utils.gemini_client import GeminiClient

# ---- Configuracao -----------------------------------------------------------
OFICIOS_DIR   = os.path.join(ROOT, "data", "knowledge", "OFICIOS")
DB_PATH       = os.path.join(ROOT, "data", "db", "duque_ia.db")
CATEGORY      = "oficio_oficial"
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100
DELAY_SEC     = 1.0     # pausa maior pra evitar rate limit (visao gasta mais cota)
BATCH_COMMIT  = 5
CRIADO_DIR    = os.path.join(ROOT, "data", "knowledge", "CRIADO", "OFICIOS")


def extrair_metadados_filename(filename: str) -> dict:
    """Extrai metadados do nome do arquivo de oficio."""
    name = os.path.splitext(filename)[0]
    partes = name.split(".")
    return {
        "numero"    : partes[0] if len(partes) > 0 else "",
        "orgao"     : partes[1] if len(partes) > 1 else "",
        "remetente" : partes[2] if len(partes) > 2 else "",
        "destinatario": partes[3] if len(partes) > 3 else "",
        "ano"       : "2026",
        "filename"  : filename
    }


def pdf_para_imagens_base64(pdf_path: str, max_pages: int = 10) -> list[str]:
    """
    Converte paginas do PDF em imagens PNG base64.
    Usa PyMuPDF (fitz) se disponivel, senao tenta pdf2image.
    """
    images_b64 = []

    # Tentativa 1: PyMuPDF (mais leve, sem poppler)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            images_b64.append(base64.b64encode(img_bytes).decode("utf-8"))
        doc.close()
        return images_b64
    except ImportError:
        pass

    # Tentativa 2: pdf2image (precisa de poppler)
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=max_pages)
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            images_b64.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
        return images_b64
    except Exception as e:
        print(f"  [pdf2image error] {e}")
        return []


def ocr_via_gemini(client: GeminiClient, image_b64: str, page_num: int) -> str:
    """Usa Gemini Vision para transcrever o texto de uma imagem de documento."""
    prompt_ocr = (
        "Transcreva todo o texto visivel neste documento oficial escaneado. "
        "Mantenha a formatacao original. Inclua numeros de protocolo, datas, "
        "nomes, cargos e todo conteudo legivel. Responda APENAS com o texto "
        "transcrito, sem comentarios adicionais."
    )

    image_bytes = base64.b64decode(image_b64)

    try:
        if hasattr(client, '_client') and client._client is not None:
            # Novo SDK (google.genai)
            from google.genai import types as genai_types
            contents = [
                genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part(
                            inline_data=genai_types.Blob(
                                mime_type="image/png",
                                data=image_bytes
                            )
                        ),
                        genai_types.Part(text=prompt_ocr)
                    ]
                )
            ]
            resp = client._client.models.generate_content(
                model=client.generation_model_name,
                contents=contents
            )
            return resp.text.strip() if resp.text else ""
        else:
            # SDK legado (google.generativeai)
            import google.generativeai as genai
            import PIL.Image

            # Converte bytes para PIL Image
            img = PIL.Image.open(io.BytesIO(image_bytes))
            model = genai.GenerativeModel(client.generation_model_name)
            resp = model.generate_content([prompt_ocr, img])
            return resp.text.strip() if resp.text else ""

    except Exception as e:
        print(f"  [OCR Gemini Error - pag {page_num}] {e}")
        return ""


def chunking_recursivo(text: str, chunk_size: int = CHUNK_SIZE,
                       overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide o texto em chunks com overlap."""
    if not text.strip():
        return []
    chunks = []
    start  = 0
    while start < len(text):
        end   = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append(chunk)
        start += chunk_size - overlap
        if start >= len(text):
            break
    return chunks


def processar_oficios(filter_num: str = None, test_mode: bool = False):
    """Processa PDFs de oficios usando OCR via Gemini Vision."""
    print("=" * 70)
    print("   DUQUE IA - INGESTAO: OFICIOS (OCR via Gemini Vision)")
    print("=" * 70)

    # Lista PDFs
    all_files = sorted([
        f for f in os.listdir(OFICIOS_DIR)
        if f.lower().endswith(".pdf")
    ])

    if filter_num:
        all_files = [f for f in all_files if filter_num in f]

    if test_mode:
        # Pega os 3 menores
        with_sizes = [(f, os.path.getsize(os.path.join(OFICIOS_DIR, f))) for f in all_files]
        with_sizes.sort(key=lambda x: x[1])
        all_files = [f for f, _ in with_sizes[:3]]
        print(f"\n  Modo teste: processando 3 menores PDFs")

    print(f"\n  Total de PDFs a processar: {len(all_files)}")

    if not all_files:
        print("  Nenhum PDF para processar.")
        return

    # Verifica se PyMuPDF esta instalado
    try:
        import fitz
        print(f"  Renderizador: PyMuPDF (fitz) v{fitz.version[0]}")
    except ImportError:
        print("  AVISO: PyMuPDF nao instalado. Tentando pdf2image (precisa poppler).")
        print("  Para melhor resultado, instale: python -m pip install PyMuPDF")

    # Conecta ao banco
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Inicializa Gemini
    client = GeminiClient()
    os.makedirs(CRIADO_DIR, exist_ok=True)

    total_chunks  = 0
    total_erros   = 0
    pdfs_ok       = 0
    pdfs_falha    = 0

    for i, pdf_name in enumerate(all_files, 1):
        pdf_path = os.path.join(OFICIOS_DIR, pdf_name)
        meta_raw = extrair_metadados_filename(pdf_name)
        source   = pdf_name

        file_size = os.path.getsize(pdf_path)
        print(f"\n  [{i:>2}/{len(all_files)}] {pdf_name} ({file_size / 1024:.0f} KB)")
        print(f"          Oficio: {meta_raw['numero']} | Dest: {meta_raw['destinatario']}")

        # 1. Converte PDF em imagens
        print(f"          Convertendo para imagens...")
        images = pdf_para_imagens_base64(pdf_path, max_pages=8)

        if not images:
            print(f"          [FALHA] Nao foi possivel converter o PDF em imagens.")
            pdfs_falha += 1
            continue

        print(f"          {len(images)} pagina(s) convertida(s)")

        # 2. OCR via Gemini Vision em cada pagina
        texto_completo = ""
        for pg, img_b64 in enumerate(images, 1):
            print(f"          OCR pagina {pg}/{len(images)}...", end=" ")
            txt = ocr_via_gemini(client, img_b64, pg)
            if txt:
                texto_completo += f"\n\n--- Pagina {pg} ---\n{txt}"
                print(f"{len(txt)} chars")
            else:
                print("sem texto")
            time.sleep(DELAY_SEC)

        if not texto_completo.strip():
            print(f"          [AVISO] OCR nao extraiu texto utilizavel.")
            pdfs_falha += 1
            continue

        print(f"          Texto total: {len(texto_completo)} chars")

        # 3. Remove chunks antigos
        cur.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (source,))

        # 4. Chunking
        chunks = chunking_recursivo(texto_completo)
        print(f"          Chunks gerados: {len(chunks)}")

        # 5. Insere cada chunk com embedding
        for j, chunk_text in enumerate(chunks):
            texto_embed = (
                f"Oficio {meta_raw['numero']} | Orgao: {meta_raw['orgao']} "
                f"| Destino: {meta_raw['destinatario']}\n\n{chunk_text}"
            )
            try:
                vetor = client.get_embedding(texto_embed[:3000], is_query=False)
                meta_json = json.dumps({
                    "title"       : f"Oficio {meta_raw['numero']} - {meta_raw['destinatario']}",
                    "numero"      : meta_raw['numero'],
                    "orgao"       : meta_raw['orgao'],
                    "destinatario": meta_raw['destinatario'],
                    "chunk_index" : j,
                    "source"      : source,
                    "ocr"         : True
                }, ensure_ascii=False)

                cur.execute("""
                    INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (source, CATEGORY, chunk_text, json.dumps(vetor), meta_json))

                total_chunks += 1
                time.sleep(DELAY_SEC * 0.5)

            except Exception as e:
                total_erros += 1
                print(f"          [ERRO chunk {j}] {e}")

        conn.commit()
        pdfs_ok += 1
        print(f"          OK: {len(chunks)} chunks gravados.")

        # Copia para CRIADO
        import shutil
        try:
            shutil.copy2(pdf_path, os.path.join(CRIADO_DIR, pdf_name))
        except Exception:
            pass

    conn.close()

    # Resultado
    print("\n" + "=" * 70)
    print(f"  CONCLUIDO!")
    print(f"  PDFs com texto extraido (OCR) : {pdfs_ok}")
    print(f"  PDFs sem texto / falha        : {pdfs_falha}")
    print(f"  Chunks inseridos no banco     : {total_chunks}")
    print(f"  Erros de embedding            : {total_erros}")
    print("=" * 70)


if __name__ == "__main__":
    filtro = None
    test   = False
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        filtro = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    if "--test" in sys.argv:
        test = True
    processar_oficios(filter_num=filtro, test_mode=test)
