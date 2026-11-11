import sqlite3
import json

conn = sqlite3.connect("data/db/vector.db")

check = conn.execute("SELECT count(*) FROM chunks WHERE id = 'autoridade_vice_prefeita_aline_do_aureo'").fetchone()[0]
if check == 0:
    chunk_id = "autoridade_vice_prefeita_aline_do_aureo"
    tipo = "AUTORIDADE"
    titulo = "Vice-Prefeita de Duque de Caxias: Aline Ferreira Batista Ribeiro (Aline do Aureo)"
    conteudo = (
        "# Vice-Prefeita de Duque de Caxias\n\n"
        "## Aline Ferreira Batista Ribeiro (Aline do Aureo)\n"
        "Aline Ferreira Batista Ribeiro, conhecida publicamente como **Aline do Aureo**, é a **Vice-Prefeita de Duque de Caxias** eleita para o mandato **2025–2028**, compondo a chapa executiva ao lado do prefeito Jonathas Monteiro Porto Neto (Netinho Reis).\n\n"
        "### Principais Informações e Trajetória:\n"
        "- **Nome Completo:** Aline Ferreira Batista Ribeiro\n"
        "- **Nome Público / Político:** Aline do Aureo\n"
        "- **Cargo:** Vice-Prefeita de Duque de Caxias (mandato 2025–2028)\n"
        "- **Formação Acadêmica:** Formada em **Serviço Social** pela Universidade do Grande Rio (Unigranrio), com especialização e pós-graduação em **Gestão Pública** pela Pontifícia Universidade Católica (PUC).\n"
        "- **Carreira e Atuação Pública:** Atuou a partir de 2017 como subsecretária e secretária municipal de Assistência Social e Direitos Humanos (SMASDH) de Duque de Caxias, com amplo histórico em gestão social, projetos de acolhimento e fortalecimento das políticas públicas municipais.\n\n"
        "### Gabinete e Contatos Oficiais:\n"
        "- **Local:** Gabinete da Vice-Prefeita (Sede da Prefeitura Municipal)\n"
        "- **Endereço:** Alameda Esmeralda, 206 - Jardim Primavera, Duque de Caxias - RJ, CEP 25.215-260 (2º Distrito)\n"
        "- **Telefone de Contato:** (21) 2772-7200\n"
        "- **E-mail Institucional:** viceprefeitaalinedoaureo@gmail.com\n"
        "- **Horário de Atendimento:** Segunda a sexta-feira, das 09h às 17h."
    )
    meta = json.dumps({
        "tipo_label": "Autoridade Pública",
        "cargo": "Vice-Prefeita de Duque de Caxias",
        "nome": "Aline Ferreira Batista Ribeiro (Aline do Aureo)",
        "apelidos": ["Aline do Aureo", "Aline do Áureo", "Aline Ferreira", "Aline Ferreira Batista Ribeiro"],
        "fonte_oficial": "Portal Oficial da Prefeitura de Duque de Caxias / ALERJ",
        "secretaria_sigla": "SMG",
        "bairro": "Jardim Primavera"
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
    print("Chunk da Vice-Prefeita Aline do Aureo inserido com sucesso em chunks e chunks_fts!")
else:
    print("Chunk da Vice-Prefeita já existe em chunks.")

# Também atualiza se o equipamento_01164 tiver menção antiga ou precisar de complemento
conn.close()
