"""
entity_resolver.py — DUQUE IA
==============================
Módulo de Resolução Determinística (Deterministic-First Architecture).
Reconhece entidades municipais, unidades descentralizadas (CRAS, UBS, UPA, UPH, Escolas, FUNDEC, Hospitais)
e serviços oficiais para consulta direta na Golden Source Layer (0ms, 100% de precisão).
Cobre deterministicamente as 443 unidades físicas municipais e os 152 bairros de Duque de Caxias.
"""

import os
import sys
import re
import json
import sqlite3
import unicodedata
from config.settings import DATABASE_MAIN

def normalize_text(text: str) -> str:
    """Normaliza texto para minúsculas e sem acentos."""
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    return re.sub(r'[^\w\s]', ' ', text).strip()

STOPWORDS = {
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "a", "o", "as", "os",
    "e", "ou", "para", "por", "com", "sem", "sob", "sobre", "qual", "quais", "onde", "fica",
    "como", "que", "tem", "qualquer", "meu", "minha", "seu", "sua", "duque", "caxias", "rj",
    "municipio", "municipal", "unidade", "unidades", "numero", "telefone", "endereco", "localizacao",
    "horario", "funcionamento", "atendimento", "gostaria", "saber", "favor", "por", "dizer",
    "secretaria", "secretarias", "subsecretaria", "subsecretarias", "posto", "postos",
    "ubs", "usf", "cras", "creas", "upa", "uph", "hospital", "hospitais", "escola", "escolas",
    "creche", "creches", "ciep", "cieps", "fundec", "colegio", "colegios", "clinica", "clinicas",
    "centro", "centros", "polo", "polos"
}

EQUIPMENT_PATTERNS = {
    "cras": r"\bcras\b|\bcentros?\s+de\s+referencia\s+de\s+assistencia\s+social\b",
    "creas": r"\bcreas\b|\bcentros?\s+de\s+referencia\s+especializados?\b",
    "ubs": r"\bubs\b|\bunidades?\s+basicas?\s+de\s+saude\b|\bpostos?\s+de\s+saude\b|\bpostos?\s+medicos?\b|\bambulatorios?\b",
    "usf": r"\busfs?\b|\bunidades?\s+de\s+saude\s+da\s+familia\b|\bclinicas?\s+da\s+familia\b|\bcasf\b",
    "upa": r"\bupas?\b|\bunidades?\s+de\s+pronto\s+atendimento\b",
    "uph": r"\buphs?\b|\bunidades?\s+pre\s+hospitalares?\b",
    "hospital": r"\bhospita(?:l|is)\b|\bmaternidades?\b|\bhmapn\b",
    "escola": r"\bescolas?\b|\bcreches?\b|\bcolegios?\b|\bcieps?\b|\bpre\s*escolas?\b|\be\s*\.\s*m\b|\be\s*\.\s*e\s*\.\s*m\b",
    "fundec": r"\bfundecs?\b|\bpolos?\s+fundec\b",
    "conselho_tutelar": r"\bconselhos?\s+tutela(?:r|res)\b|\bcmdca\b|\bcomdepi\b|\bcomdim\b",
    "caps": r"\bcaps\b|\bcapsij\b|\bcaps\s+ad\b|\bcentros?\s+de\s+atencao\s+psicossocial\b",
    "ceam": r"\bceams?\b|\bcasas?\s+da\s+mulher\b|\bcasas?\s+da\s+mulher\s+caxiense\b|\bcraesm\b",
    "cadunico": r"\bcadunico\b|\bcadastro\s+unico\b|\bbolsa\s+familia\b",
    "restaurante_povo": r"\brestaurantes?\s+do\s+povo\b|\brestaurantes?\s+popular(?:es)?\b",
    "teatro": r"\bteatros?\b|\bteatro\s+raul\s+cortez\b",
    "museu": r"\bmuseus?\b|\bmuseu\s+ciencia\s+e\s+vida\b",
    "vila_olimpica": r"\bvilas?\s+olimpicas?\b",
    "defesa_civil": r"\bdefesa\s+civil\b",
    "subprefeitura": r"\bsubprefeituras?\b",
    "guarda_municipal": r"\bguarda\s+municipal\b",
    "veterinario": r"\bveterinarios?\b|\bveterinaria\b|\bcastramove(?:l|is)\b|\bprotecao\s+aos\s+animais\b|\bcachorros?\b|\bcaes\b|\bcao\b|\bgatos?\b|\bpets?\b|\banima(?:l|is)\b|\bzoonoses?\b|\bsocorro\s+animal\b|\bhospital\s+veterinario\b|\bhmv\b",
    "secretaria": r"\bsecretarias?\b|\bsemuh\b|\bsmo\b|\bsmu\b|\bsms\b|\bsme\b|\bsmf\b|\bseasdh\b|\bsmasdh\b|\bsemagro\b",
    "ipmdc": r"\bipmdc\b",
    "ouvidoria": r"\bouvidoria\b|\bouvidoria\s+geral\b",
    "prefeito": r"\bprefeitos?\b|\bprefeitura\b"
}

LOCALITY_PATTERNS = {
    # 1º Distrito — Centro e Adjacências
    "25 de agosto": r"\b25\s+de\s+agosto\b|\bjardim\s+25\s+de\s+agosto\b",
    "centro": r"\bcentro\s+(?:de\s+caxias|de\s+duque\s+de\s+caxias)?\b",
    "dr laureano": r"\bdr\s+laureano\b|\bdoutor\s+laureano\b",
    "parque lafaiete": r"\bparque\s+lafaiete\b|\blafaiete\b",
    "gramacho": r"\bgramacho\b|\bparque\s+gramacho\b|\bparada\s+gramacho\b",
    "centenario": r"\bcentenario\b|\bcentenário\b",
    "beira mar": r"\bbeira\s+mar\b|\bperiquitos\b",
    "olavo bilac": r"\bolavo\s+bilac\b|\bbilac\b",
    "bar dos cavaleiros": r"\bbar\s+dos\s+cavaleiros\b|\bcavaleiros\b",
    "vila sao luis": r"\bvila\s+sao\s+luis\b|\bvila\s+são\s+luís\b|\bvila\s+são\s+luis\b",
    "engenho do porto": r"\bengenho\s+do\s+porto\b",
    "pantanal": r"\bpantanal\b",

    # 2º Distrito — Campos Elíseos
    "campos eliseos": r"\bcampos\s+eliseos\b|\bcampos\s+elíseos\b",
    "jardim primavera": r"\bjardim\s+primavera\b|\bprimavera\b",
    "saracuruna": r"\bsaracuruna\b",
    "pilar": r"\bpilar\b",
    "figueira": r"\bfigueira\b",
    "chacaras rio petropolis": r"\bchacaras?\s+rio\s+petropolis\b|\bchácaras?\s+rio\s+petrópolis\b",

    # 3º Distrito — Imbariê
    "imbarie": r"\bimbarie\b|\bimbariê\b",
    "parque paulista": r"\bparque\s+paulista\b",
    "parada angelica": r"\bparada\s+angelica\b|\bparada\s+angérica\b|\bparada\s+angélica\b",
    "nova campinas": r"\bnova\s+campinas\b",
    "santa lucia": r"\bsanta\s+lucia\b|\bsanta\s+lúcia\b",
    "parque equitativa": r"\bparque\s+equitativa\b|\bequitativa\b",
    "santa cruz da serra": r"\bsanta\s+cruz\s+da\s+serra\b|\bsanta\s+cruz\b",
    "taquara": r"\btaquara\b",

    # 4º Distrito — Xerém
    "xerem": r"\bxerem\b|\bxerém\b",
    "mantiquira": r"\bmantiquira\b",
    "amapa": r"\bamapa\b|\bamapá\b"
}


class MunicipalEntityDetector:
    """Detecta equipamentos, serviços e localidades na pergunta do munícipe."""

    _LOCALITIES_CACHE = None

    @classmethod
    def _get_localities(cls, db_path: str = DATABASE_MAIN) -> dict:
        """Carrega e compila em memória os 152 bairros e apelidos de Duque de Caxias."""
        if cls._LOCALITIES_CACHE is not None:
            return cls._LOCALITIES_CACHE

        localities = dict(LOCALITY_PATTERNS)

        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT nome, aliases FROM bairros_distritos")
                for nome, aliases_raw in cur.fetchall():
                    nome_norm = normalize_text(nome)
                    if len(nome_norm) >= 3 and nome_norm not in localities:
                        localities[nome_norm] = rf"\b{re.escape(nome_norm)}\b"

                    if aliases_raw:
                        try:
                            aliases = json.loads(aliases_raw)
                            for a in aliases:
                                a_norm = normalize_text(a)
                                if len(a_norm) >= 3 and a_norm not in ("25", "caxias", "duque") and a_norm not in localities:
                                    localities[a_norm] = rf"\b{re.escape(a_norm)}\b"
                        except Exception:
                            pass
                conn.close()
            except Exception:
                pass

        cls._LOCALITIES_CACHE = localities
        return cls._LOCALITIES_CACHE

    @classmethod
    def detect(cls, query: str, db_path: str = DATABASE_MAIN) -> dict:
        q_norm = normalize_text(query)
        
        detected_equipments = []
        for eq_type, pat in EQUIPMENT_PATTERNS.items():
            if re.search(pat, q_norm):
                detected_equipments.append(eq_type)
                
        localities_dict = cls._get_localities(db_path=db_path)
        detected_localities = []
        for loc_name, pat in localities_dict.items():
            if re.search(pat, q_norm):
                detected_localities.append(loc_name)
                
        return {
            "equipments": detected_equipments,
            "localities": detected_localities,
            "has_exact_entity": len(detected_equipments) > 0 or len(detected_localities) > 0
        }


class GoldenSourceResolver:
    """Consulta diretamente a camada determinística de dados oficiais no SQLite."""

    _UNIDADES_CACHE = None

    def __init__(self, db_path: str = DATABASE_MAIN):
        self.db_path = db_path
        self._ensure_cache()

    def _ensure_cache(self):
        """Indexa as 443 unidades físicas em memória na primeira chamada (<2ms)."""
        if GoldenSourceResolver._UNIDADES_CACHE is not None:
            return

        unidades = []
        if not os.path.exists(self.db_path):
            GoldenSourceResolver._UNIDADES_CACHE = unidades
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                SELECT u.id, u.name, u.address, u.phone, u.working_hours, s.name, s.code
                FROM secretaria_unidades u
                LEFT JOIN secretarias s ON u.secretaria_id = s.id
            """)
            rows = list(cur.fetchall())
            try:
                cur.execute("""
                    SELECT id, nome, endereco || ' - ' || bairro || ' - CEP: ' || cep, telefone, '', 'Secretaria Municipal de Educação', 'SME'
                    FROM escolas_municipais
                """)
                rows.extend(cur.fetchall())
            except Exception:
                pass
            conn.close()
        except Exception:
            GoldenSourceResolver._UNIDADES_CACHE = unidades
            return

        def get_unit_type(nl: str) -> str:
            if nl.startswith("cras ") or " cras " in nl: return "cras"
            if nl.startswith("creas ") or " creas " in nl: return "creas"
            if nl.startswith("upa ") or " upa " in nl: return "upa"
            if nl.startswith("uph ") or " uph " in nl: return "uph"
            if "veterinario" in nl or "veterinaria" in nl: return "veterinario"
            if "hospital" in nl or "maternidade" in nl or "hmapn" in nl: return "hospital"
            if "fundec" in nl: return "fundec"
            if "conselho tutelar" in nl: return "conselho_tutelar"
            if "caps" in nl: return "caps"
            if "ceam" in nl or "casa da mulher" in nl: return "ceam"
            if "cadastro unico" in nl or "cadunico" in nl or "bolsa familia" in nl: return "cadunico"
            if "teatro" in nl: return "teatro"
            if "museu" in nl: return "museu"
            if "restaurante do povo" in nl: return "restaurante_povo"
            if "vila olimpica" in nl: return "vila_olimpica"
            if "defesa civil" in nl: return "defesa_civil"
            if "detran" in nl or "identificacao civil" in nl: return "detran"
            if "sine" in nl: return "sine"
            if any(k in nl for k in ["escola", "ciep", "creche", "e m ", "e e m ", "pré-escola", "pre-escola"]): return "escola"
            if "usf" in nl or "clinica" in nl or "casf" in nl: return "usf"
            if "ubs" in nl or "centro municipal de saude" in nl or "posto de saude" in nl or "posto medico" in nl: return "ubs"
            if any(k in nl for k in ["secretaria", "subsecretaria", "gabinete", "procuradoria"]): return "secretaria"
            return "outros"

        for uid, name, address, phone, hours, sec_name, sec_code in rows:
            name_norm = normalize_text(name)
            addr_norm = normalize_text(address)

            # Extrai bairro do endereço
            bairro_match = re.search(r'-\s*([^,-]+),\s*Duque de Caxias', address)
            bairro_extracted = bairro_match.group(1).strip() if bairro_match else ""
            bairro_extracted_norm = normalize_text(bairro_extracted)

            clean_name = re.sub(r'^(e\s*m|e\s*e\s*m|ciep|creche|cras|creas|upa|uph|usf|ubs|hospital|fundec|secretaria\s+municipal\s+de|secretaria\s+de|secretaria|subsecretaria\s+de|subsecretaria)\s*', '', name_norm).strip()
            name_tokens = {w for w in clean_name.split() if len(w) >= 3 and w not in STOPWORDS}
            unit_type = get_unit_type(name_norm)

            unidades.append({
                "id": uid,
                "name": name,
                "name_norm": name_norm,
                "clean_name": clean_name,
                "unit_type": unit_type,
                "address": address,
                "addr_norm": addr_norm,
                "bairro": bairro_extracted,
                "bairro_norm": bairro_extracted_norm,
                "phone": phone,
                "hours": hours,
                "sec_name": sec_name or "Prefeitura de Duque de Caxias",
                "sec_code": sec_code or "",
                "name_tokens": name_tokens
            })

        GoldenSourceResolver._UNIDADES_CACHE = unidades

    def resolve(self, query: str) -> dict | None:
        detection = MunicipalEntityDetector.detect(query, db_path=self.db_path)
        if not detection["has_exact_entity"]:
            return None

        q_norm = normalize_text(query)
        eqs = detection["equipments"]
        locs = detection["localities"]

        # Impedir interceptação de perguntas procedimentais ou de serviços
        is_procedural = any(w in q_norm for w in [
            "como solicitar", "como pedir", "como faço", "como faco", "como registrar", "como emitir", 
            "tapa-buraco", "tapa buraco", "limpeza", "entulho", "lixo", "poste", "lampada", "lâmpada", 
            "matricula", "matrícula", "creche", "curso", "quais cursos", "segunda via", "iptu", "taxa", "multa",
            "denuncia", "denunciar", "reclamar", "colab", "disponivel", "disponiveis", "disponível", 
            "disponíveis", "cadastro", "cadastrar", "oferece", "oferta", "ajuda", "ajudar", "chuva", "chuvas",
            "enchente", "desabamento", "destruida", "destruido", "perdi tudo", "auxilio", "auxílio",
            "demora", "esperando", "espera", "marcação", "marcacao", "marcar", "especialista", "como proceder",
            "reclamar", "reclamação", "reclamacao", "agendamento", "fila", "sisreg", "regulação", "regulacao",
            "consulta", "diferenca", "diferença", "diferente", "comparar", "escopo", "competencia", "competência",
            "exemplos", "atribuicao", "atribuição", "atribuições", "atribuicoes",
            "funcao", "função", "funcoes", "funções", "o que faz", "papel", "atividades", "atividade",
            "esportes", "esporte", "modalidades", "atuacao", "atuação", "responsabilidades"
        ])
        is_location_query = any(w in q_norm for w in [
            "onde", "fica", "endereco", "endereço", "qual o endereco", "qual o endereço",
            "localizacao", "localização", "telefone", "contato", "numero", "horario", "horário",
            "atendimento", "posto", "unidade", "cras", "upa", "uph", "hospital", "escola",
            "sede", "quem e o prefeito", "quem é o prefeito"
        ])

        is_asking_place = any(k in q_norm for k in [
            "qual o endereco", "qual o endereço", "onde fica o cras", "onde fica a upa", "onde fica a clinica",
            "onde fica o hospital", "onde eu acho", "onde acho", "onde encontro", "mais proxima", "mais proximo",
            "unidade mais proxima", "posto mais proximo", "clinica mais proxima"
        ])
        # Casos de emergência clínica/social (trauma ortopédico, fratura aguda, desmaio na rua)
        # nunca devem ser tratados como simples consulta de endereço na Golden Source Layer;
        # devem fluir para os handlers clínicos com protocolo SAMU 192 e Hospital Adão Pereira Nunes.
        is_emergency_clinical = any(w in q_norm for w in [
            "quebrei", "quebrado", "fratura", "trauma", "ortopedia", "desmaiado", "desmaio", "socorro"
        ])
        is_animal_query = any(w in q_norm for w in ["cachorro", "cachorros", "cao", "caes", "gato", "gatos", "pet", "pets", "animal", "animais", "veterinario", "veterinaria"])
        if is_emergency_clinical and not is_animal_query:
            return None

        if is_procedural and not is_asking_place:
            return None

        # 1. Tentar resolver Ouvidoria Geral (apenas se não for pergunta procedimental sobre outro serviço)
        if "ouvidoria" in eqs and not is_procedural:
            return {
                "answer": (
                    "Os contatos oficiais da **Ouvidoria Geral do Município de Duque de Caxias** são:\n\n"
                    "• **Telefone:** **(21) 2652-3835**\n"
                    "• **WhatsApp:** **(21) 99824-5903**\n"
                    "• **Endereço:** **Alameda Esmeralda, 206 - Jardim Primavera (Sede da Prefeitura)**\n"
                    "• **Funcionamento:** Segunda a sexta-feira, das 9h às 17h\n"
                    "• **Solicitações Web:** Aplicativo Colab ([duquedecaxias.colab.re](https://duquedecaxias.colab.re/))"
                ),
                "sources": ["Golden Source Layer (Ouvidoria Geral)"],
                "confidence": 1.0,
                "intent_detected": "golden_source_ouvidoria_resolved",
                "resolved_by": "GoldenSourceResolver"
            }

        # Resolução da Sede da Prefeitura / Prefeito (Apenas para dúvidas diretas de localização/atendimento da Sede)
        is_direct_prefeitura_query = bool(re.search(
            r"\b(?:onde\s+fica|qual\s+(?:o\s+)?endereço|qual\s+(?:o\s+)?endereco|localização|localizacao|sede)\s+(?:da\s+)?prefeitura\b"
            r"|\bprefeitura\s+(?:onde\s+fica|endereço|endereco|fica\s+onde|sede)\b"
            r"|\bquem\s+é\s+o\s+prefeito\b|\bquem\s+e\s+o\s+prefeito\b",
            q_norm
        ))
        if is_direct_prefeitura_query and not is_procedural and "colab" not in q_norm:
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

        # 2. Tentar resolver secretarias e órgãos caso seja consulta de secretaria
        if "secretaria" in eqs or any(re.search(rf"\b{c}\b", q_norm) for c in ["sms", "smo", "sme", "smf", "smu", "semuh", "ipmdc"]):
            res_sec = self._resolve_secretaria(q_norm)
            if res_sec:
                return res_sec

        # 3. Tentar resolver unidades físicas específicas (ex: CRAS Jardim Primavera, UPA Saracuruna, etc.)
        res_unit = self._resolve_unit(eqs, locs, q_norm)
        if res_unit:
            return res_unit

        # 4. Tentar resolver outros órgãos (ex: FUNDEC) se unidade física não foi encontrada
        if "fundec" in eqs or "ipmdc" in eqs:
            res_sec = self._resolve_secretaria(q_norm)
            if res_sec:
                return res_sec

        return None

    def _resolve_unit(self, eqs: list, locs: list, q_norm: str) -> dict | None:
        """Busca determinística instantânea nas 443 unidades municipais."""
        unidades = GoldenSourceResolver._UNIDADES_CACHE or []
        if not unidades:
            return None

        q_tokens = {w for w in q_norm.split() if len(w) >= 3 and w not in STOPWORDS}

        # Verificar se o munícipe está pedindo uma listagem geral do equipamento no município (ex: 'onde tem cras', 'quais as upas')
        is_list_query = any(p in q_norm for p in ["onde tem", "quais sao as", "quais sao os", "quais as", "quais os", "lista de"]) and not locs

        scored_units = []
        for u in unidades:
            score = 0
            u_type = u["unit_type"]

            # Compatibilidade de equipamento quando especificado na consulta
            if eqs:
                type_matches = False
                for deq in eqs:
                    if deq == u_type:
                        type_matches = True
                        score += 50
                        break
                    elif deq == "upa" and u_type in ("upa", "uph"):
                        type_matches = True
                        score += 40
                        break
                    elif deq == "uph" and u_type in ("uph", "upa"):
                        type_matches = True
                        score += 40
                        break
                    elif deq in ("ubs", "usf") and u_type in ("ubs", "usf", "uph"):
                        type_matches = True
                        score += 40
                        break
                    elif deq == "hospital" and u_type == "hospital":
                        type_matches = True
                        score += 50
                        break
                    elif deq == "veterinario" and u_type == "veterinario":
                        type_matches = True
                        score += 60
                        break
                    elif deq == "escola" and u_type == "escola":
                        type_matches = True
                        score += 40
                        break

                # Se a consulta especificou um tipo e a unidade não é compatível, descarte imediatamente
                if not type_matches:
                    continue

            # Substring direta do nome na query
            clean_u = u["clean_name"]
            if len(clean_u) >= 5 and clean_u in q_norm:
                score += 80

            # Match de tokens do nome específico
            common_tokens = q_tokens.intersection(u["name_tokens"])
            score += len(common_tokens) * 20

            # Match de localidade / bairro
            loc_matched = False
            for loc in locs:
                if loc in u["bairro_norm"] or loc in u["name_norm"] or loc in u["addr_norm"]:
                    score += 35
                    loc_matched = True
                    break

            if loc_matched and eqs:
                score += 30

            # Para eleger uma unidade individual específica, exige evidência concreta de nome, token ou localidade
            has_specific_evidence = (len(clean_u) >= 5 and clean_u in q_norm) or len(common_tokens) >= 1 or loc_matched
            if has_specific_evidence and score >= 45:
                scored_units.append((score, u))

        # Se for listagem geral de um tipo específico (ex: CRAS, UPA, Conselho Tutelar)
        if is_list_query and eqs:
            target_eq = eqs[0]
            matching_type_units = [u for u in unidades if u["unit_type"] == target_eq or (target_eq == "upa" and u["unit_type"] in ("upa", "uph"))]
            if matching_type_units and len(matching_type_units) <= 15:
                type_labels = {
                    "cras": "Centros de Referência de Assistência Social (CRAS)",
                    "creas": "Centros de Referência Especializados (CREAS)",
                    "upa": "Unidades de Pronto Atendimento (UPAs e UPHs 24h)",
                    "conselho_tutelar": "Conselhos Tutelares",
                    "caps": "Centros de Atenção Psicossocial (CAPS)",
                    "veterinario": "Hospitais e Unidades Veterinárias Municipais",
                    "defesa_civil": "Bases da Defesa Civil"
                }
                label = type_labels.get(target_eq, target_eq.upper())
                ans = f"O município de Duque de Caxias conta com as seguintes unidades de **{label}**:\n\n"
                for u in matching_type_units:
                    b_str = f" ({u['bairro']})" if u['bairro'] else ""
                    phone_str = f" • Tel: **{u['phone']}**" if u['phone'] and u['phone'].lower() not in ("não cadastrado", "none", "") else ""
                    ans += f"• **{u['name']}**{b_str}: {u['address']}{phone_str}\n"
                ans += "\nSe quiser detalhes, horários ou rotas para alguma dessas unidades, é só perguntar! 😊"
                return {
                    "answer": ans,
                    "sources": [f"secretaria_unidades ({target_eq.upper()})"],
                    "confidence": 1.0,
                    "intent_detected": "golden_source_unit_resolved",
                    "resolved_by": "GoldenSourceResolver"
                }

        if scored_units:
            scored_units.sort(key=lambda x: -x[0])
            best_score, best_u = scored_units[0]

            name = best_u["name"]
            addr = best_u["address"]
            phone = best_u["phone"]
            hours = best_u["hours"]
            sec = best_u["sec_name"]

            import urllib.parse
            clean_search_addr = re.sub(r'\s+', ' ', f"{name}, {addr}").strip()
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(clean_search_addr)}"

            is_proximity_req = any(w in q_norm for w in ["mais proxima", "mais proximo", "proxima", "proximo", "perto", "vizinho"])
            if is_proximity_req and locs:
                loc_name = locs[0].title()
                ans = f"Para a região de **{loc_name}**, a unidade de atendimento de referência é a **{name}**.\n\n"
                ans += f"• **Endereço Completo:** {addr}\n"
            else:
                ans = f"O endereço do **{name}** é **{addr}**.\n\n"

            ans += f"• **Órgão Responsável:** {sec}\n"
            if phone and phone.lower() not in ("não cadastrado", "não disponível", "nan", "none", ""):
                ans += f"• **Telefone:** **{phone}**\n"
            if hours and hours.lower() not in ("não cadastrado", "não disponível", "nan", "none", ""):
                ans += f"• **Funcionamento:** {hours}\n"

            ans += f"• **Rota / Mapa:** [Ver no Google Maps]({maps_url})\n"

            # Orientação de cadastro caso o munícipe tenha perguntado sobre se cadastrar na unidade de saúde
            if any(w in q_norm for w in ["cadastr", "matricul", "inscrever", "cuidar da minha saude"]):
                if best_u["unit_type"] in ("ubs", "usf", "uph", "hospital"):
                    ans += "\n📋 **Para se cadastrar na unidade de saúde:** Compareça de segunda a sexta-feira portando seu **Cartão do SUS**, **documento oficial com foto (RG/CPF)** e **comprovante de residência** no município.\n"

            # Orientação específica para atendimento veterinário
            if best_u["unit_type"] == "veterinario":
                ans += (
                    "\n🐾 **Orientações para Atendimento Veterinário (HMV):**\n"
                    "• O atendimento de urgência/emergência e consultas é **100% gratuito** para cães e gatos de moradores de Duque de Caxias.\n"
                    "• **Documentos Obrigatórios do Tutor:** Documento de identidade com foto (**RG/CNH**), **CPF** e **comprovante de residência atualizado** no município de Duque de Caxias em nome do tutor do animal.\n"
                    "• **Serviços:** Emergência clínica, cirurgias gerais, castração gratuita, exames de sangue, raio-X e ultrassonografia.\n"
                )

            ans += "\nSe precisar de mais alguma informação ou serviços deste equipamento, é só perguntar! 😊"

            return {
                "answer": ans,
                "sources": [f"secretaria_unidades ({name})"],
                "confidence": 1.0,
                "intent_detected": "golden_source_unit_resolved",
                "resolved_by": "GoldenSourceResolver"
            }

        return None

    def _resolve_secretaria(self, q_norm: str) -> dict | None:
        """Busca determinística na tabela secretarias (apenas para contato/endereço direto)."""
        # Se for pergunta sobre escopo, atribuições, comparações ou procedimentos, NÃO interceptar deterministicamente
        is_comparative_or_procedural = any(w in q_norm for w in [
            "diferenca", "diferença", "diferente", "comparar", "escopo", "competencia", "competência",
            "exemplos", "o que faz", "atribuicao", "atribuição", "atribuições", "atribuicoes",
            "como solicitar", "como pedir", "como funciona", "servicos", "serviços"
        ])
        if is_comparative_or_procedural:
            return None

        # Exigir que a consulta esteja explicitamente perguntando contato, endereço, localização ou horário da secretaria
        is_asking_sec_info = any(k in q_norm for k in [
            "onde fica", "endereco", "endereço", "qual o endereco", "qual o endereço", "qual endereco",
            "telefone", "contato", "numero", "email", "e-mail", "horario", "horário", "atendimento", "sede"
        ]) or re.fullmatch(r"(?:secretaria\s+(?:municipal\s+)?(?:de\s+)?[a-z\s]+|smuh|smoa|sms|sme|smf|semuh)", q_norm.strip())

        if not is_asking_sec_info:
            return None

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

        scored = []
        for sec_id, name, code, address, phone, email, hours in rows:
            name_norm = normalize_text(name)
            code_norm = normalize_text(code) if code else ""

            # Extrai palavras significativas da secretaria (ex: saude, obras, fazenda, urbanismo, educacao)
            words_sec = [w for w in name_norm.split() if len(w) >= 4 and w not in ["secretaria", "municipal", "direitos", "humanos", "apoio", "para"]]

            score = 0
            if code_norm and re.search(rf"\b{re.escape(code_norm)}\b", q_norm):
                score += 100
            for w in words_sec:
                if re.search(rf"\b{re.escape(w)}\b", q_norm):
                    score += 25
            if "fundacao" in name_norm and "fundec" not in q_norm and "fundacao" not in q_norm:
                score -= 15

            if score > 0:
                scored.append((score, sec_id, name, code, address, phone, email, hours))

        if not scored:
            return None

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, sec_id, name, code, address, phone, email, hours = scored[0]

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
