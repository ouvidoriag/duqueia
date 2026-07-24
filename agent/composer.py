"""
composer.py — Response Composer & Answer Policy Engine (DUQUE IA)
===================================================================
Camada de orquestração de resposta responsável por decidir quais partes dos
chunks e metadados estruturados realmente devem ser exibidos ao cidadão,
evitando despejo bruto de documentos ou anexos de atendimento presencial
quando o munícipe consulta um serviço digital (Colab/Portal).
"""

import re
import unicodedata

class AnswerPolicyEngine:
    @staticmethod
    def is_procedural_request(query: str) -> bool:
        """Identifica se a intenção da pergunta é 'como solicitar/fazer' um serviço digital de zeladoria."""
        q_norm = "".join(c for c in unicodedata.normalize('NFKD', query.lower()) if not unicodedata.combining(c))
        procedural_keywords = [
            "como solicitar", "como pedir", "como faco", "como faço", "como registrar",
            "tapa-buraco", "tapa buraco", "pavimentacao", "pavimentação", "asfalto",
            "lampada", "lâmpada", "poste", "entulho", "limpeza", "lote baldio", "terreno",
            "matricula", "matrícula", "creche", "iptu"
        ]
        return any(kw in q_norm for kw in procedural_keywords)

    @staticmethod
    def is_location_request(query: str) -> bool:
        """Identifica se a intenção da pergunta é estritamente consultar endereço, localização ou telefone."""
        q_norm = "".join(c for c in unicodedata.normalize('NFKD', query.lower()) if not unicodedata.combining(c))
        location_keywords = [
            "onde fica", "qual o endereco", "qual o endereço", "endereco da", "endereço da",
            "localizacao", "localização", "telefone da", "horario de funcionamento"
        ]
        return any(kw in q_norm for kw in location_keywords)


class ResponseComposer:
    @staticmethod
    def compose(query: str, raw_answer: str, intent: str = None) -> str:
        """
        Orquestra a resposta final eliminando contradições de canais e anexos brutos
        de Cartas de Serviço presenciais para chamados prioritariamente digitais.
        """
        if not raw_answer:
            return raw_answer

        is_procedural = AnswerPolicyEngine.is_procedural_request(query)
        is_location = AnswerPolicyEngine.is_location_request(query)

        composed = raw_answer

        # 1. Oculta incondicionalmente blocos soltos de 'Informações adicionais' concatenados
        composed = re.sub(
            r"(?i)\n*Informações adicionais sobre.*?(?:📍|👣|Passo a Passo).*?(?=\n\n|\Z)",
            "",
            composed,
            flags=re.DOTALL
        )
        
        # 2. Oculta linhas literais de "Passo 1: Presencialmente na secretaria" descontextualizadas
        composed = re.sub(r"(?i)Passo 1:\s*Presencialmente.*?\n?", "", composed)
        composed = re.sub(r"(?i)📍\s*Endereço de Atendimento:.*?\n?", "", composed)

        # 3. Higienização final de nulos e espaços extras
        composed = re.sub(r'\n\s*\n\s*\n', '\n\n', composed).strip()
        return composed
