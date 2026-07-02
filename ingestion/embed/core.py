import re
import json
from typing import List, Dict, Any

class ChunkingStrategies:
    """Implementação das diferentes estratégias de chunking para RAG do DUQUE IA."""

    @staticmethod
    def recursive_character_chunker(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Divide o texto recursivamente por parágrafos, linhas, frases e palavras."""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk)
            start += (chunk_size - chunk_overlap)
            if start >= text_len or chunk_size <= chunk_overlap:
                break
        return chunks

    @staticmethod
    def token_chunker(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Divide o texto baseado em tokens estimativos (usando delimitadores de palavras)."""
        words = text.split()
        chunks = []
        step = chunk_size - chunk_overlap
        
        for i in range(0, len(words), step):
            chunk_words = words[i:i + chunk_size]
            chunks.append(" ".join(chunk_words))
            if i + chunk_size >= len(words):
                break
        return chunks

    @staticmethod
    def semantic_chunker(text: str, buffer_size: int, threshold: float) -> List[str]:
        """Divide o texto baseado na variação semântica entre frases subsequentes."""
        # Split por pontuação para separar frases
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        
        # Simulação de análise semântica: junta sentenças até um limite de tamanho
        # Em produção, usaria embeddings para medir a similaridade de cosseno
        for sentence in sentences:
            if not sentence.strip():
                continue
            current_chunk.append(sentence)
            if len(" ".join(current_chunk)) > 400:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    @staticmethod
    def entity_geo_chunker(geojson_str: str) -> List[Dict[str, Any]]:
        """Estratégia GIS: 1 entidade geográfica = 1 chunk.
        
        Valida o GeoJSON e cria chunks contendo as propriedades estruturadas
        e metadados para consultas territoriais do Duque de Caxias.
        """
        try:
            data = json.loads(geojson_str)
        except json.JSONDecodeError:
            raise ValueError("GeoJSON inválido.")
            
        chunks = []
        if data.get("type") == "FeatureCollection":
            features = data.get("features", [])
            for feat in features:
                # Validações exigidas pela Fase 6 (Geometria, CRS, Nome, ID, Campos obrigatórios)
                properties = feat.get("properties", {})
                geometry = feat.get("geometry", {})
                
                # Identifica tipo de entidade (Municipio, Bairro, Setor, Quadra, Lote, Logradouro)
                entidade = properties.get("entidade", "desconhecido").lower()
                nome = properties.get("nome", properties.get("name", "Sem Nome"))
                entidade_id = properties.get("id", properties.get("ID", None))
                
                # Construção do conteúdo do chunk em formato textual e metadados
                chunk_text = f"Entidade Geográfica: {entidade.capitalize()} | Nome: {nome} | ID: {entidade_id}"
                
                # Adiciona representação espacial textual para busca
                if geometry:
                    chunk_text += f" | Tipo de Geometria: {geometry.get('type')}"
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "entidade": entidade,
                        "nome": nome,
                        "id": entidade_id,
                        "properties": properties,
                        "geometry": geometry
                    }
                })
        return chunks
