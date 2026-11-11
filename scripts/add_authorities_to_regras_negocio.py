import sqlite3
import json

conn = sqlite3.connect('data/db/main.db')
cur = conn.cursor()

# 1. Corrige o vazamento de tag "prefeito" na creche da SME
cur.execute("UPDATE regras_negocio SET tags = replace(tags, 'rua prefeito bernardo tavora', 'rua bernardo tavora') WHERE id = 'regra_canon_vaga_creche_matricula_escolar_sme'")

# 2. Insere a Regra Canônica do Prefeito Netinho Reis
cur.execute("""
INSERT OR REPLACE INTO regras_negocio (id, tipo_label, tema, assunto, conteudo, tags, prioridade, boost_weight)
VALUES (
    'regra_canon_autoridade_prefeito_netinho_reis',
    'AUTORIDADE MUNICIPAL',
    'Governo Municipal e Poder Executivo',
    'Prefeito de Duque de Caxias — Jonathas Monteiro Porto Neto (Netinho Reis)',
    'Jonathas Monteiro Porto Neto (Netinho Reis) é o Prefeito de Duque de Caxias eleito para a gestão 2025-2028. Empresário do setor de sustentabilidade e empreendedor desde os 18 anos, assumiu a liderança do Poder Executivo municipal com foco em modernização, tecnologia, inclusão social e fortalecimento dos serviços públicos.',
    '["prefeito", "prefeito de duque de caxias", "netinho reis", "jonathas monteiro porto neto", "quem é o prefeito", "poder executivo municipal"]',
    'MÁXIMA',
    5.0
)
""")

# 3. Insere a Regra Canônica da Vice-Prefeita Aline do Aureo
cur.execute("""
INSERT OR REPLACE INTO regras_negocio (id, tipo_label, tema, assunto, conteudo, tags, prioridade, boost_weight)
VALUES (
    'regra_canon_autoridade_vice_prefeita_aline_do_aureo',
    'AUTORIDADE MUNICIPAL',
    'Governo Municipal e Poder Executivo',
    'Vice-Prefeita de Duque de Caxias — Aline Ribeiro da Silva (Aline do Aureo)',
    'Aline Ribeiro da Silva (Aline do Aureo) é a Vice-Prefeita de Duque de Caxias eleita para a gestão 2025-2028. Atua ativamente no fortalecimento das políticas públicas, inclusão social e articulação governamental.',
    '["vice-prefeita", "vice prefeita", "aline do aureo", "aline ribeiro da silva", "quem é a vice-prefeita"]',
    'MÁXIMA',
    5.0
)
""")

conn.commit()
print("Regras canônicas de autoridades inseridas com sucesso em regras_negocio!")
conn.close()
