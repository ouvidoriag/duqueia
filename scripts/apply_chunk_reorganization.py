# -*- coding: utf-8 -*-
"""
Execução Segura da Etapa 2 (Reestruturação Semântica dos Chunks):
1. Substitui os 4 blocos monolíticos territoriais (geo_01571, geo_01572, geo_01573, geo_01574, geo_01575)
   por 47 Chunks Atômicos por Bairro Mestre Oficial (Regra GIS Fase 6: 1 Bairro = 1 Chunk).
2. Substitui o bloco monolítico da Transparência (transparencia_catalogo_59_apis, 6.566 chars)
   por 4 Sub-chunks Temáticos de APIs (~1.300 a 1.900 chars cada).
3. Sincroniza atomicamente em 'chunks', 'chunks_fts' (FTS5) e 'duque_ia_chunks'.
"""

import os
import sys
import json
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DB_VECTOR = os.path.join(BASE_DIR, "data", "db", "vector.db")

from scripts.restructure_geo_chunks import extract_bairros_from_db

# 4 Sub-chunks temáticos das 59 APIs da Transparência
ENDPOINT_INFO = """# 🌐 Portal da Transparência de Duque de Caxias / RJ — Catálogo Oficial de APIs
Endpoint Único: https://transparencia.duquedecaxias.rj.gov.br/sincronia/apidados.rule?sys=LAI
Método: POST | Formato: JSON
Exemplo de Envio: {"api": "<nome_da_api>", "ano": 2026}
"""

CHUNKS_APIS = {
    "transparencia_api_orcamento_receitas_despesas": {
        "titulo": "Portal da Transparência: APIs de Orçamento, Receitas e Despesas Públicas",
        "conteudo": f"""{ENDPOINT_INFO}
## APIs Oficiais: Orçamento, Receitas, Despesas e Gestão Fiscal
As seguintes APIs retornam dados fiscais e orçamentários do município de Duque de Caxias:
• api: 'despesas_liquidadas' (Cód 03) — Consulta de Todas as Despesas Liquidadas
• api: 'receita_prevista_arrecadada' (Cód 05) — Receita Prevista x Arrecadada (Todas as fontes)
• api: 'despesas_empenhadas' (Cód 19) — Consulta de Todas as Despesas Empenhadas (Empenhos)
• api: 'despesas_pagas' (Cód 20) — Consulta de Todas as Despesas Pagas
• api: 'quadro_detalhamento_despesas' (Cód 89) — Quadro de Detalhamento das Despesas (QDD)
• api: 'ordem_cronologica_liquidacao' (Cód 98) — Ordem Cronológica de Pagamentos e Liquidações
• api: 'repasse_concedido' (Cód 99) — Consulta de Repasses e Transferências Concedidas
• api: 'despesas_realizadas_recursos_multa_transito_sincronia' (Cód 104) — Despesas com Recursos de Multas
• api: 'execucao_orcamentaria_rreo_m2' (Cód 228) — Relatório Resumido da Execução Orçamentária (RREO)
• api: 'consulta_rgf_m2' (Cód 235) — Relatório de Gestão Fiscal (RGF)
• api: 'balanco_anual_simples_m1' (Cód 255) — Balanço Contábil Anual Simples
• api: 'ldo_simples_m2' (Cód 348) — Lei de Diretrizes Orçamentárias (LDO)
• api: 'consulta_ppa_m2' (Cód 350) — Plano Plurianual (PPA)
• api: 'consulta_loa_simples_m2' (Cód 352) — Lei Orçamentária Anual (LOA)
• api: 'divida_ativa_m3' (Cód 383) — Consulta à Dívida Ativa e Cobrança Tributária
• api: 'prestacao_contas_m2' (Cód 420) — Prestação de Contas Anual do Executivo
• api: 'transferencia_recurso_uniao' (Cód 477) — Repasses e Transferências da União
• api: 'emendas_parlamentares_m3' (Cód 388) — Execução de Emendas Parlamentares Municipais""",
        "tags": ["transparencia", "api orcamento", "despesas pagas", "receitas", "loa", "ldo", "ppa", "rgf", "rreo", "divida ativa", "empenho"]
    },
    "transparencia_api_servidores_folha_concursos": {
        "titulo": "Portal da Transparência: APIs de Servidores Públicos, Folha de Pagamento e Concursos",
        "conteudo": f"""{ENDPOINT_INFO}
## APIs Oficiais: Servidores Públicos, Folha Salarial, Cargos e Concursos
As seguintes APIs fornecem dados sobre o quadro funcional e remunerações da Prefeitura de Duque de Caxias:
• api: 'salarios_servidores_bruto_liquido' (Cód 97) — Consulta Nominal de Salários (Bruto e Líquido)
• api: 'salario_cargos_m1' (Cód 240) — Tabela Salarial por Cargo Público (Modelo 1)
• api: 'salario_cargos_servidores_m1' (Cód 242) — Vínculo de Servidores por Cargo e Lotação
• api: 'concursos_editais_m1' (Cód 244) — Editais de Concursos Públicos e Processos Seletivos (PSS)
• api: 'valores_diarias_m1' (Cód 247) — Tabela Oficial de Valores de Diárias de Viagem
• api: 'diarias_passagens' (Cód 04) — Consulta Individual de Diárias e Passagens Pagas
• api: 'jovem_aprendiz_m2' (Cód 301) — Contratações de Estagiários e Jovens Aprendizes
• api: 'tabela_remuneratoria_m2' (Cód 386) — Tabela do Plano de Cargos, Carreiras e Remunerações
• api: 'secretarias_m2' (Cód 318) — Organograma e Estrutura Administrativa das Secretarias""",
        "tags": ["transparencia", "salarios servidores", "folha de pagamento", "concursos", "editais pss", "diarias", "estagiarios", "cargos e salarios"]
    },
    "transparencia_api_obras_contratos_patrimonio": {
        "titulo": "Portal da Transparência: APIs de Obras Públicas, Contratos e Patrimônio Municipal",
        "conteudo": f"""{ENDPOINT_INFO}
## APIs Oficiais: Obras Públicas, Contratos Administrativos e Patrimônio
As seguintes APIs detalham investimentos em infraestrutura e gestão patrimonial de Duque de Caxias:
• api: 'obras_paralisadas_m1' (Cód 149) — Relatório e Motivação de Obras Públicas Paralisadas
• api: 'obra_andamento_m2' (Cód 389) — Acompanhamento de Obras Públicas em Andamento e Prazos
• api: 'consulta_terceirizada' (Cód 155) — Lista de Empresas Terceirizadas Prestadoras de Serviços
• api: 'patrimonio' (Cód 102) — Inventário de Bens Móveis e Imóveis do Município
• api: 'transferencia_convenio_federal_estadual' (Cód 320) — Convênios com Governo Federal e Estadual
• api: 'contratos_cadastro_transparencia_m2' (Cód 454) — Cadastro Geral de Contratos Administrativos
• api: 'fiscal_contrato_m2' (Cód 463) — Designação Oficial dos Fiscais de Cada Contrato
• api: 'contratos_covid19' (Cód 493) — Histórico de Contratos Especiais de Saúde
• api: 'gestao_saude_m2' (Cód 252) — Relatórios Oficiais de Gestão do Fundo Municipal de Saúde
• api: 'unidade_especializada_m2' (Cód 254) — Escalas e Dados de Unidades Especializadas de Saúde""",
        "tags": ["transparencia", "obras publicas", "obras em andamento", "contratos", "fiscais de contrato", "patrimonio", "convenios", "terceirizadas"]
    },
    "transparencia_api_licitacoes_fornecedores_lai": {
        "titulo": "Portal da Transparência: APIs de Licitações, Fornecedores Punidos e LAI",
        "conteudo": f"""{ENDPOINT_INFO}
## APIs Oficiais: Licitações, Fornecedores, Acesso à Informação (LAI) e Conselhos
As seguintes APIs controlam compras públicas, integridade e cidadania em Duque de Caxias:
• api: 'atos_editais_novo_m2' (Cód 366) — Editais de Licitação, Pregões e Concorrências
• api: 'chamamento_publico_m2' (Cód 340) — Chamamentos Públicos e Parcerias com OSCs/MROSC
• api: 'sancionados_m4' (Cód 248) — Cadastro de Fornecedores Punidos e Empresas Sancionadas
• api: 'conselho_dados_municipal' (Cód 56) — Atas e Composição dos Conselhos Municipais
• api: 'lancamento_documentos_m2' (Cód 402) — Documentos e Resoluções de Conselhos e Órgãos
• api: 'parecer_tce_m1' (Cód 256) — Pareceres Prévios do Tribunal de Contas do Estado (TCE-RJ)
• api: 'parecer_legislativo_m2' (Cód 399) — Pareceres e Atos do Poder Legislativo (Câmara Municipal)
• api: 'grau_sigilo_m2' (Cód 246) — Rol de Informações Classificadas em Grau de Sigilo (LAI)
• api: 'relatorios_estatisticos' (Cód 112) — Estatísticas de Pedidos de Acesso à Informação (e-SIC)
• api: 'perguntas_respostas' (Cód 310) — Banco Oficial de Perguntas Frequentes (FAQ Transparência)
• api: 'busca_avancada' (Cód 119) — Ferramenta de Busca Avançada no Portal da Transparência""",
        "tags": ["transparencia", "licitacoes", "editais", "fornecedores punidos", "chamamento publico", "lai", "e-sic", "tce", "conselhos municipais"]
    }
}

def apply_reorganization():
    print("=== INICIANDO REESTRUTURAÇÃO SEMÂNTICA DE CHUNKS GIGANTES ===")
    conn = sqlite3.connect(DB_VECTOR)
    cur = conn.cursor()

    # 1. Extração dos 47 Chunks Atômicos de Bairros
    print("[*] Extraindo 47 Bairros Mestres consolidados...")
    bairros_chunks = extract_bairros_from_db()

    # 2. Remoção dos antigos blocos gigantes territoriais
    old_geo_ids = ['geo_01571', 'geo_01572', 'geo_01573', 'geo_01574', 'geo_01575']
    for gid in old_geo_ids:
        cur.execute("DELETE FROM chunks WHERE id = ?", (gid,))
        cur.execute("DELETE FROM chunks_fts WHERE id = ?", (gid,))
        cur.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (gid,))
    print(f"[OK] Removidos 5 blocos monolíticos territoriais de 'chunks', 'chunks_fts' e 'duque_ia_chunks'.")

    # 3. Inserção dos 47 Chunks Atômicos de Bairros nas 3 tabelas
    bairros_inserted = 0
    for b in bairros_chunks:
        cid = b["id"]
        tipo = b["tipo"]
        tit = b["titulo"]
        cont = b["conteudo"]
        meta_str = json.dumps(b["metadata"], ensure_ascii=False)
        tags_str = json.dumps(b["metadata"]["tags"], ensure_ascii=False)

        # Inserção em chunks
        cur.execute("""
            INSERT OR REPLACE INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (cid, tipo, tit, cont, meta_str))

        # Inserção em chunks_fts
        cur.execute("DELETE FROM chunks_fts WHERE id = ?", (cid,))
        cur.execute("""
            INSERT INTO chunks_fts (id, titulo, conteudo, tipo)
            VALUES (?, ?, ?, ?)
        """, (cid, tit, cont, tipo))

        # Inserção em duque_ia_chunks
        cur.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (cid,))
        cur.execute("""
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, 'geografia_territorial', ?, NULL, ?, ?)
        """, (cid, cont, meta_str, tags_str))

        bairros_inserted += 1

    print(f"[OK] {bairros_inserted} Chunks Atômicos de Bairros indexados com sucesso nas 3 tabelas!")

    # 4. Substituição de transparencia_catalogo_59_apis por 4 Sub-chunks Temáticos
    print("[*] Reestruturando Catálogo das 59 APIs da Transparência em 4 Sub-chunks Temáticos...")
    cur.execute("DELETE FROM chunks WHERE id = 'transparencia_catalogo_59_apis'")
    cur.execute("DELETE FROM chunks_fts WHERE id = 'transparencia_catalogo_59_apis'")
    cur.execute("DELETE FROM duque_ia_chunks WHERE source = 'transparencia_catalogo_59_apis'")

    apis_inserted = 0
    for cid, data in CHUNKS_APIS.items():
        tipo = "TRANSPARENCIA"
        tit = data["titulo"]
        cont = data["conteudo"]
        meta = {
            "title": tit,
            "category": "transparencia",
            "tags": data["tags"],
            "boost_weight": 2.5,
            "parent_source": "catalogo_59_apis.md"
        }
        meta_str = json.dumps(meta, ensure_ascii=False)
        tags_str = json.dumps(data["tags"], ensure_ascii=False)

        # Inserção em chunks
        cur.execute("""
            INSERT OR REPLACE INTO chunks (id, tipo, titulo, conteudo, metadata_json, vetor_blob)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (cid, tipo, tit, cont, meta_str))

        # Inserção em chunks_fts
        cur.execute("DELETE FROM chunks_fts WHERE id = ?", (cid,))
        cur.execute("""
            INSERT INTO chunks_fts (id, titulo, conteudo, tipo)
            VALUES (?, ?, ?, ?)
        """, (cid, tit, cont, tipo))

        # Inserção em duque_ia_chunks
        cur.execute("DELETE FROM duque_ia_chunks WHERE source = ?", (cid,))
        cur.execute("""
            INSERT INTO duque_ia_chunks (source, category, content, embedding, metadata, keywords)
            VALUES (?, 'transparencia', ?, NULL, ?, ?)
        """, (cid, cont, meta_str, tags_str))

        apis_inserted += 1

    print(f"[OK] {apis_inserted} Sub-chunks da Transparência indexados com sucesso nas 3 tabelas!")

    conn.commit()

    # Contagens Finais
    cur.execute("SELECT count(*) FROM chunks")
    c_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM chunks_fts")
    f_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM duque_ia_chunks")
    d_count = cur.fetchone()[0]
    print(f"\n[OK] Contagem Final em vector.db: chunks={c_count}, chunks_fts={f_count}, duque_ia_chunks={d_count}")

    conn.close()
    print("=== REESTRUTURAÇÃO CONCLUÍDA COM SUCESSO ===")

if __name__ == "__main__":
    apply_reorganization()
