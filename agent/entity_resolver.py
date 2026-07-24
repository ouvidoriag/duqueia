"""
entity_resolver.py — DUQUE IA
==============================
Módulo de Resolução Determinística (Deterministic-First Architecture).
Reconhece entidades municipais, unidades descentralizadas (CRAS, UBS, UPA)
e serviços oficiais para consulta direta na Golden Source Layer (0ms, 100% de precisão).
"""

import os
import sys
import re
import sqlite3
import unicodedata
from config.settings import DATABASE_MAIN

def normalize_text(text: str) -> str:
    """Normaliza texto para minúsculas e sem acentos."""
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return re.sub(r'[^\w\s]', ' ', text).strip()

EQUIPMENT_PATTERNS = {
    "cras": r"\bcras\b|\bcentro\s+de\s+referencia\s+de\s+assistencia\s+social\b",
    "creas": r"\bcreas\b|\bcentro\s+de\s+referencia\s+especializado\b",
    "ubs": r"\bubs\b|\bunidade\s+basica\s+de\s+saude\b|\bposto\s+de\s+saude\b",
    "upa": r"\bupa\b|\bunidade\s+de\s+pronto\s+atendimento\b",
    "uph": r"\buph\b",
    "hospital": r"\bhospital\b",
    "escola": r"\bescola\b|\bcreche\b|\bcolegio\b",
    "secretaria": r"\bsecretaria\b|\bsemuh\b|\bsmo\b|\bsmu\b|\bsms\b|\bsme\b|\bsmf\b|\bseasdh\b|\bsmasdh\b",
    "fundec": r"\bfundec\b",
    "ipmdc": r"\bipmdc\b",
    "ouvidoria": r"\bouvidoria\b|\bouvidoria\s+geral\b",
    "prefeito": r"\bprefeito\b|\bprefeitura\b"
}

LOCALITY_PATTERNS = {
    "jardim primavera": r"\bjardim\s+primavera\b|\bprimavera\b",
    "xerem": r"\bxerem\b|\bxerém\b",
    "imbarie": r"\bimbarie\b|\bimbariê\b",
    "parque paulista": r"\bparque\s+paulista\b",
    "pilar": r"\bpilar\b",
    "saracuruna": r"\bsaracuruna\b",
    "campos eliseos": r"\bcampos\s+eliseos\b|\bcampos\s+elíseos\b",
    "pantanal": r"\bpantanal\b",
    "centenario": r"\bcentenario\b|\bcentenário\b",
    "beira mar": r"\bbeira\s+mar\b",
    "25 de agosto": r"\b25\s+de\s+agosto\b|\bjardim\s+25\s+de\s+agosto\b",
    "olavo bilac": r"\bolavo\s+bilac\b",
    "dr laureano": r"\bdr\s+laureano\b|\bdoutor\s+laureano\b"
}


class MunicipalEntityDetector:
    """Detecta equipamentos, serviços e localidades na pergunta do munícipe."""

    @staticmethod
    def detect(query: str) -> dict:
        q_norm = normalize_text(query)
        
        detected_equipments = []
        for eq_type, pat in EQUIPMENT_PATTERNS.items():
            if re.search(pat, q_norm):
                detected_equipments.append(eq_type)
                
        detected_localities = []
        for loc_name, pat in LOCALITY_PATTERNS.items():
            if re.search(pat, q_norm):
                detected_localities.append(loc_name)
                
        return {
            "equipments": detected_equipments,
            "localities": detected_localities,
            "has_exact_entity": len(detected_equipments) > 0 or len(detected_localities) > 0
        }


class GoldenSourceResolver:
    """Consulta diretamente a camada determinística de dados oficiais no SQLite."""

    def __init__(self, db_path: str = DATABASE_MAIN):
        self.db_path = db_path

    def resolve(self, query: str) -> dict | None:
        detection = MunicipalEntityDetector.detect(query)
        if not detection["has_exact_entity"]:
            return None

        q_norm = normalize_text(query)
        eqs = detection["equipments"]
        locs = detection["localities"]

        # Impedir interceptação de 'Prefeitura' ou 'Ouvidoria' se a pergunta for procedimental (como fazer/solicitar serviço)
        is_procedural = any(w in q_norm for w in ["como solicitar", "como pedir", "como faço", "como faco", "como registrar", "como emitir", "tapa-buraco", "tapa buraco", "limpeza", "entulho", "lixo", "poste", "lampada", "lâmpada", "matricula", "matrícula", "creche", "curso"])
        is_location_query = any(w in q_norm for w in ["onde fica", "qual o endereco", "qual o endereço", "localizacao", "localização", "endereco", "endereço", "telefone", "horario", "horário", "quem e o prefeito", "quem é o prefeito"])

        # 1. Tentar resolver Ouvidoria Geral (apenas se não for pergunta procedimental sobre outro serviço)
        if "ouvidoria" in eqs and not is_procedural:
            return {
                "answer": (
                    "Os contatos oficiais da **Ouvidoria Geral do Município de Duque de Caxias** são:\n\n"
                    "• **Telefone:** **(21) 2652-3835**\n"
                    "• **WhatsApp:** **(21) 99824-5903**\n"
                    "• **Endereço:** Alameda Esmeralda, 206 - Jardim Primavera (Sede da Prefeitura)\n"
                    "• **Funcionamento:** Segunda a sexta-feira, das 9h às 17h\n"
                    "• **Solicitações Web:** Aplicativo Colab ([duquedecaxias.colab.re](https://duquedecaxias.colab.re/))"
                ),
                "sources": ["Golden Source Layer (Ouvidoria Geral)"],
                "confidence": 1.0,
                "intent_detected": "golden_source_ouvidoria_resolved",
                "resolved_by": "GoldenSourceResolver"
            }

        if "prefeito" in eqs and (is_location_query or not is_procedural):
            return {
                "answer": (
                    "A Sede da **Prefeitura Municipal de Duque de Caxias** fica localizada na **Alameda Esmeralda, 206 - Jardim Primavera, Duque de Caxias - RJ**.\n\n"
                    "• **Horário de Atendimento:** Segunda a sexta-feira, das 9h às 17h\n"
                    "• **Atendimento Geral:** Telefone da Ouvidoria **(21) 2652-3835** ou WhatsApp **(21) 99824-5903**."
                ),
                "sources": ["Golden Source Layer (Prefeitura Municipal)"],
                "confidence": 1.0,
                "intent_detected": "golden_source_prefeitura_resolved",
                "resolved_by": "GoldenSourceResolver"
            }

        # 2. Tentar resolver unidades físicas específicas (ex: CRAS Jardim Primavera, UPA Saracuruna)
        if "cras" in eqs or "ubs" in eqs or "upa" in eqs or "escola" in eqs or "hospital" in eqs or locs:
            res_unit = self._resolve_unit(eqs, locs, q_norm)
            if res_unit:
                return res_unit

        # 2. Tentar resolver secretarias e órgãos (ex: Onde fica a Secretaria de Saúde)
        if "secretaria" in eqs or "fundec" in eqs or "ipmdc" in eqs:
            res_sec = self._resolve_secretaria(q_norm)
            if res_sec:
                return res_sec

        return None

    def _resolve_unit(self, eqs: list, locs: list, q_norm: str) -> dict | None:
        """Busca determinística na tabela secretaria_unidades."""
        if not os.path.exists(self.db_path):
            return None

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT u.name, u.address, u.phone, u.working_hours, s.name
                FROM secretaria_unidades u
                LEFT JOIN secretarias s ON u.secretaria_id = s.id
            """)
            rows = cur.fetchall()
        except Exception:
            conn.close()
            return None

        conn.close()

        for name, address, phone, hours, sec_name in rows:
            name_norm = normalize_text(name)
            addr_norm = normalize_text(address)

            # Match 1: Equipamento + Bairro combinados
            match_eq = any(e in name_norm for e in eqs) or ("cras" in q_norm and "cras" in name_norm)
            match_loc = any(l in name_norm or l in addr_norm for l in locs)

            if (match_eq and match_loc) or (match_eq and not locs and len(rows) == 1):
                ans = (
                    f"O endereço do **{name}** é **{address}**.\n\n"
                    f"• **Órgão Responsável:** {sec_name or 'Prefeitura de Duque de Caxias'}\n"
                )
                if phone and phone.lower() not in ("não cadastrado", "não disponível", "nan", "none", ""):
                    ans += f"• **Telefone:** **{phone}**\n"
                if hours and hours.lower() not in ("não cadastrado", "não disponível", "nan", "none", ""):
                    ans += f"• **Funcionamento:** {hours}\n"
                    
                ans += "\nSe precisar de mais alguma informação sobre este equipamento ou serviços do SUAS/Prefeitura, é só dizer! 😊"

                return {
                    "answer": ans,
                    "sources": [f"secretaria_unidades ({name})"],
                    "confidence": 1.0,
                    "intent_detected": "golden_source_unit_resolved",
                    "resolved_by": "GoldenSourceResolver"
                }

        return None

    def _resolve_secretaria(self, q_norm: str) -> dict | None:
        """Busca determinística na tabela secretarias."""
        if not os.path.exists(self.db_path):
            return None

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, code, address, phone, email, working_hours FROM secretarias")
            rows = cur.fetchall()
        except Exception:
            conn.close()
            return None

        conn.close()

        for sec_id, name, code, address, phone, email, hours in rows:
            name_norm = normalize_text(name)
            code_norm = normalize_text(code)

            # Extrai palavras significativas da secretaria (ex: saude, obras, fazenda, urbanismo)
            words_sec = [w for w in name_norm.split() if len(w) >= 4 and w not in ["secretaria", "municipal", "de", "direitos", "humanos"]]

            if (code_norm and re.search(rf"\b{re.escape(code_norm)}\b", q_norm)) or any(w in q_norm for w in words_sec):
                ans = (
                    f"O endereço da **{name} ({code})** é **{address or 'Alameda Esmeralda, 206 - Jardim Primavera (Sede da Prefeitura)'}**.\n\n"
                )
                if phone and phone.lower() not in ("não cadastrado", "none", ""):
                    ans += f"• **Telefone:** **{phone}**\n"
                if email and email.lower() not in ("não cadastrado", "none", ""):
                    ans += f"• **E-mail:** **{email}**\n"
                if hours and hours.lower() not in ("não cadastrado", "none", ""):
                    ans += f"• **Horário de Atendimento:** {hours}\n"
                else:
                    ans += f"• **Horário de Atendimento:** Segunda a sexta-feira, das 9h às 17h\n"

                ans += "\nPosso ajudar você com mais alguma informação, telefone ou serviços desta secretaria?"

                return {
                    "answer": ans,
                    "sources": [f"secretarias ({name})"],
                    "confidence": 1.0,
                    "intent_detected": "golden_source_secretaria_resolved",
                    "resolved_by": "GoldenSourceResolver"
                }

        return None
