import sqlite3

conn = sqlite3.connect("data/db/main.db")
cur = conn.cursor()
cur.execute("DROP VIEW IF EXISTS vw_ia_servicos;")
cur.execute("""
CREATE VIEW vw_ia_servicos AS
SELECT 
    s.id AS servico_id,
    sec.name AS secretaria_nome,
    sec.code AS secretaria_sigla,
    sec.code AS secretaria_codigo,
    sec.code AS secretaria_code,
    cat.name AS categoria_nome,
    cat.name AS categoria,
    s.name AS servico_nome,
    s.description AS descricao,
    s.how_to_access AS como_solicitar,
    s.how_to_access AS como_acessar,
    s.address AS endereco,
    s.who_can_request AS publico_alvo,
    s.who_can_request AS quem_pode_solicitar,
    s.max_deadline AS prazo_atendimento,
    s.max_deadline AS prazo_maximo,
    s.cost AS custo,
    s.waiting_time AS tempo_espera,
    s.regulation_norm AS norma_regulamentadora,
    s.regulation_norm AS norma_reguladora,
    (SELECT GROUP_CONCAT(phone, ', ') FROM service_phones WHERE service_id = s.id) AS telefones,
    (SELECT GROUP_CONCAT(email, ', ') FROM service_emails WHERE service_id = s.id) AS emails,
    (SELECT GROUP_CONCAT(link, ', ') FROM service_links WHERE service_id = s.id) AS links,
    (SELECT GROUP_CONCAT(document_name, '; ') FROM service_documents WHERE service_id = s.id) AS documentos,
    (SELECT GROUP_CONCAT(step_number || '. ' || description, '\n') FROM service_steps WHERE service_id = s.id) AS passo_a_passo
FROM services s
JOIN secretarias sec ON s.secretaria_id = sec.id
LEFT JOIN categories cat ON s.category_id = cat.id
WHERE s.status = 'published';
""")
conn.commit()
conn.close()
print("View vw_ia_servicos recriada com sucesso em main.db!")
