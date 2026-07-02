import os
import argparse
import json
import sqlite3
import sys
from dotenv import load_dotenv

# Carrega as chaves de API do .env antes de qualquer inicialização
load_dotenv()

# Garante acesso à pasta utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils.gemini_client import GeminiClient
from config import load_config
from core import ChunkingStrategies

# Instancia o cliente globalmente para reúso de chaves
gemini_client = GeminiClient()

def generate_embedding(text: str) -> list:
    """Gera o vetor de embedding através do cliente unificado (com rotação de chaves)."""
    return gemini_client.get_embedding(text)

def extract_keywords_heuristics(text: str) -> list:
    """Extrai palavras-chave significativas do texto usando heurísticas locais simples."""
    stopwords = {
        "como", "onde", "quando", "quem", "qual", "quais", "para", "com", "uma", "um", 
        "mais", "sobre", "esta", "este", "seus", "suas", "pelo", "pela", "pelos", "pelas", 
        "seja", "eram", "seria", "teria", "esse", "essa", "isso", "aquilo", "tudo", "nada",
        "fazer", "posso", "quero", "saber", "entre", "algum", "deve", "devem", "esta",
        "está", "estão", "pelos", "pelas", "sem", "sob", "sobre", "por", "para", "com", 
        "dos", "das", "aos", "aas", "nas", "nos", "num", "numa", "sua", "seu", "pode", "podem",
        "prefeitura", "município", "municipal", "duque", "caxias"
    }
    import re
    words = re.findall(r'\b[a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]{3,15}\b', text.lower())
    filtered_words = [w for w in words if w not in stopwords]
    freq = {}
    for w in filtered_words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)
    return sorted_words[:12]

def save_to_sqlite(db_path: str, source: str, category: str, content: str, embedding: list, metadata: dict, keywords: list):
    """Insere o chunk de documento no banco SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        source,
        category,
        content,
        json.dumps(embedding),
        json.dumps(metadata, ensure_ascii=False),
        json.dumps(keywords, ensure_ascii=False)
    ))
    
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="DUQUE IA - Pipeline de Ingestão e Geração de Embeddings")
    parser.add_argument("--config", default="ingestion/embed/embed_config.yml", help="Caminho do arquivo de configuração")
    args = parser.parse_args()

    # 1. Carrega as configurações
    try:
        config = load_config(args.config)
        print(f"[Embed Main] Configurações carregadas com sucesso de: {args.config}")
    except Exception as e:
        print(f"[Embed Error] Erro ao carregar configurações: {e}")
        return

    parsed_dir = "parsed_pdf_files"
    db_path = os.path.join("agent", "duque_ia.db")

    if not os.path.exists(parsed_dir):
        print(f"[Embed Error] Pasta {parsed_dir} não encontrada. Execute 'make parse_pdfs' primeiro.")
        return

    # Coleta as fontes que serão reingeridas a partir do parsed_pdf_files/
    # para fazer um DELETE SELETIVO (preserva carta_servicos e oficio_oficial)
    sources_to_reingest = set()
    if os.path.exists(parsed_dir):
        for root, _, files in os.walk(parsed_dir):
            for f in files:
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as fp:
                            d = json.load(fp)
                        src = d.get("source", f)
                        sources_to_reingest.add(src)
                    except Exception:
                        pass

    # Remove apenas os chunks das fontes que serão reinseridas (não apaga carta_servicos/oficio_oficial)
    if os.path.exists(db_path) and sources_to_reingest:
        try:
            conn = sqlite3.connect(db_path)
            placeholders = ",".join("?" for _ in sources_to_reingest)
            conn.cursor().execute(f"DELETE FROM duque_ia_chunks WHERE source IN ({placeholders});",
                                  list(sources_to_reingest))
            conn.commit()
            conn.close()
            print(f"[Embed Main] Limpeza seletiva: {len(sources_to_reingest)} fontes removidas (carta_servicos e ofícios preservados).")
        except Exception as e:
            print(f"[Embed Warning] Não foi possível limpar seletivamente: {e}")

    # 2. Varre os arquivos JSON processados de forma recursiva
    count_chunks = 0
    for root, _, files in os.walk(parsed_dir):
        for f in files:
            if f.endswith(".json"):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                source = data.get("source", f)
                title = data.get("title", "")
                content = data.get("content", "")
                meta = data.get("metadata", {})
                category = meta.get("category", "general")
                
                print(f"[Embed Main] Chunking e indexando documento: {source} ({category})")
                
                # Executa a estratégia ativa recomendada (recursive_256_64 neste caso ou a geográfica)
                # Para simplificar e garantir a máxima qualidade, usaremos a recursive_500_100 para textos longos
                chunks = ChunkingStrategies.recursive_character_chunker(content, 500, 100)
                
                for idx, chunk_text in enumerate(chunks):
                    # Adiciona contexto do título no chunk para melhorar retrieval
                    contextualized_text = f"Documento: {title}\nConteúdo: {chunk_text}"
                    
                    # Gera vetor de embedding
                    emb = generate_embedding(contextualized_text)
                    
                    # Metadados do chunk
                    chunk_meta = {
                        "chunk_index": idx,
                        "title": title,
                        "original_metadata": meta
                    }
                    
                    # Extrai palavras-chave significativas do chunk e do título
                    kw_text = f"{title} {chunk_text}"
                    kws = extract_keywords_heuristics(kw_text)
                    
                    # Salva no banco local SQLite
                    save_to_sqlite(db_path, source, category, chunk_text, emb, chunk_meta, kws)
                    count_chunks += 1

    print(f"\n[Embed Main] Ingestão concluída com sucesso! Total de {count_chunks} chunks persistidos no banco de dados.")

if __name__ == "__main__":
    main()
