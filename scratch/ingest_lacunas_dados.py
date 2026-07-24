"""
ingest_lacunas_dados.py — DUQUE IA
==================================
Indexação incremental enriquecida das 7 seções de conhecimento complementar em duque_ia_chunks (vector.db).
Limpa apenas registros anteriores de lacunas_dados_resolvidas.md e preserva 100% da base original.
"""

import os
import sys
import json
import sqlite3

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from config.settings import DATABASE_VECTOR
from agent.agent import DuqueIAAgent

KNOWLEDGE_FILE = os.path.join(_PROJECT_ROOT, "data", "knowledge", "CRIADO", "lacunas_dados_resolvidas.md")

KEYWORDS_BY_SECTION = {
    1: "poda arvore calcada praca arvore galho corte autorizacao meio ambiente zeladoria colab limpezas",
    2: "documentacao documentos matricula creche escola municipal certidao nascimento carteira vacinacao comprovante residencia rg cpf fotos 3x4 sus nis laudo medico inscricao escolar",
    3: "iptu carne 2 via emissao online portal financas tributos inscricao imobiliaria cota unica parcelamento fazenda imposto predial",
    4: "terreno abandonado lote baldio limpeza capina muramento fiscalizacao notificacao proprietario colab ouvidoria mato alto acumulo lixo",
    5: "divisao territorial distritos bairros primeiro distrito 1º distrito 2º distrito segundo distrito 3º distrito terceiro distrito 4º distrito quarto distrito campos eliseos jardim primavera imbarie xerem centro saracuruna santa cruz da serra pilar taquaraolavo bilac gramacho sarapui doutor laureano bar dos cavaleiros beira mar vila sao luis",
    6: "populacao estimada habitantes censo ibge area territorial baixada fluminense caxias demografia territorio",
    7: "cursos gratuitos fundec informatica ingles espanhol barbeiro cabeleireiro eletricista predial libras inscricao qualificacao profissional fundec.rj.gov.br"
}

def ingest_incremental():
    print("=" * 70)
    print("   INDEXAÇÃO INCREMENTAL ENRIQUECIDA DE LACUNAS DE DADOS NO VECTOR.DB")
    print("=" * 70)
    
    agent = DuqueIAAgent()
    gemini_client = agent.gemini_client
    
    if not os.path.exists(KNOWLEDGE_FILE):
        print(f"[Erro] Arquivo não encontrado: {KNOWLEDGE_FILE}", file=sys.stderr)
        return
        
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    sections = text.split("\n## ")
    
    # Limpa versões anteriores do lacunas_dados_resolvidas.md
    conn = sqlite3.connect(DATABASE_VECTOR)
    cur = conn.cursor()
    cur.execute("DELETE FROM duque_ia_chunks WHERE source = 'lacunas_dados_resolvidas.md'")
    conn.commit()
    conn.close()
    
    inserted_count = 0
    
    sec_num = 0
    for idx, sec in enumerate(sections):
        if not sec.strip() or sec.startswith("# Informações"):
            continue
        sec_num += 1
            
        lines = sec.strip().split("\n")
        raw_title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        
        full_chunk_text = f"{raw_title}\n\n{body}"
        
        title_clean = raw_title.replace("1. ", "").replace("2. ", "").replace("3. ", "").replace("4. ", "").replace("5. ", "").replace("6. ", "").replace("7. ", "")
        
        keywords = KEYWORDS_BY_SECTION.get(sec_num, title_clean.lower()) + f" {title_clean.lower()} {body.lower()}"
        
        # Gera embedding via Gemini
        try:
            emb = gemini_client.get_embedding(full_chunk_text, is_query=False)
        except Exception as e:
            print(f"[Embedding Warning] Usando fallback para chunk '{title_clean}': {e}", file=sys.stderr)
            import hashlib
            h = hashlib.sha256(full_chunk_text.encode('utf-8')).hexdigest()
            emb = [float(int(h[i:i+2], 16))/255.0 for i in range(0, len(h), 2)]
            emb = (emb * 24)[:768]
            
        emb_json = json.dumps(emb)
        meta_json = json.dumps({
            "source": "lacunas_dados_resolvidas.md",
            "category": "CONHECIMENTO_COMPLEMENTAR_OFICIAL",
            "title": title_clean
        }, ensure_ascii=False)
        
        # Inserção Incremental
        conn = sqlite3.connect(DATABASE_VECTOR)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "lacunas_dados_resolvidas.md",
                "CONHECIMENTO_COMPLEMENTAR_OFICIAL",
                full_chunk_text,
                emb_json,
                meta_json,
                keywords
            )
        )
        conn.commit()
        conn.close()
        inserted_count += 1
        print(f"  [+] Chunk {inserted_count}: '{title_clean}' indexado com sucesso com {len(keywords.split())} keywords.")

    print("=" * 70)
    print(f"[Sucesso] {inserted_count} chunks atualizados e enriquecidos com palavras-chave no vector.db.")
    print("=" * 70)

if __name__ == "__main__":
    ingest_incremental()
