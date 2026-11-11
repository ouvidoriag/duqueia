import sqlite3
import json

conn = sqlite3.connect("data/db/vector.db")

check = conn.execute("SELECT count(*) FROM chunks WHERE id = 'autoridade_prefeito_netinho_reis'").fetchone()[0]
if check == 0:
    chunk_id = "autoridade_prefeito_netinho_reis"
    tipo = "AUTORIDADE"
    titulo = "Prefeito de Duque de Caxias: Jonathas Monteiro Porto Neto (Netinho Reis)"
    conteudo = (
        "# Prefeito de Duque de Caxias\n\n"
        "## Jonathas Monteiro Porto Neto (Netinho Reis)\n"
        "Netinho Reis (Jonathas Monteiro Porto Neto) é o Prefeito de Duque de Caxias eleito para a gestão 2025-2028.\n"
        "É empresário do setor de sustentabilidade e empreendedor desde os 18 anos. Vindo de uma família com tradição política no município, assumiu a prefeitura com foco em modernização, tecnologia, causas sociais, saúde e educação.\n\n"
        "### Perfil e Metas:\n"
        "- Liderança Inovadora: Foco em tecnologia, saúde, educação e inclusão social.\n"
        "- Gestão Humanizada: Atuação estratégica priorizando o atendimento digno e humanizado ao munícipe.\n"
        "- Sustentabilidade: Desenvolvimento econômico sustentável aliado à preservação e inovação urbana.\n"
        "- Transparência: Compromisso com uma governança participativa e transparente.\n\n"
        "Sede / Gabinete do Prefeito: Alameda Esmeralda, 206 - Jardim Primavera, Duque de Caxias - RJ, CEP 25215-260."
    )
    meta = json.dumps({
        "tipo_label": "Autoridade Pública",
        "cargo": "Prefeito de Duque de Caxias",
        "nome": "Jonathas Monteiro Porto Neto (Netinho Reis)",
        "apelidos": ["Netinho Reis", "Netinho", "Jonathas Monteiro"],
        "fonte_oficial": "data/knowledge/CRIADO/prefeito.md"
    }, ensure_ascii=False)

    conn.execute(
        "INSERT INTO chunks (id, tipo, titulo, conteudo, metadata_json) VALUES (?, ?, ?, ?, ?)",
        (chunk_id, tipo, titulo, conteudo, meta)
    )
    conn.execute(
        "INSERT INTO chunks_fts (id, titulo, conteudo, tipo) VALUES (?, ?, ?, ?)",
        (chunk_id, titulo, conteudo, tipo)
    )
    conn.commit()
    print("Chunk do Prefeito Netinho Reis inserido com sucesso em chunks e chunks_fts!")
else:
    print("Chunk do Prefeito já existe em chunks.")

conn.close()

