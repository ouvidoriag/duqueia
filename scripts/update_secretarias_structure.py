"""
Script de atualização incremental da estrutura administrativa das Secretarias.
Ajustes realizados conforme reforma administrativa municipal:
1. SMCTEL separada em:
   - SMCT: Secretaria Municipal de Cultura e Turismo
   - SMEL: Secretaria Municipal de Esporte e Lazer
2. SMG: Secretaria Municipal de Governo (removida menção à Ouvidoria Geral)
3. SMCSRPTER: Secretaria Municipal de Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral
"""

import sqlite3
import json
import os

def update_main_db():
    db_path = 'data/db/main.db'
    if not os.path.exists(db_path):
        print(f"[main.db] Arquivo nao encontrado: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Atualizar ID 72 (SMG)
    c.execute(
        "UPDATE secretarias SET name = ?, code = ? WHERE id = 72",
        ('Secretaria Municipal de Governo', 'SMG')
    )

    # 2. Atualizar ID 78 (SMCT)
    c.execute(
        "UPDATE secretarias SET name = ?, code = ? WHERE id = 78",
        ('Secretaria Municipal de Cultura e Turismo', 'SMCT')
    )

    # 3. Inserir ou atualizar SMEL (ID 85)
    row_smel = c.execute("SELECT id FROM secretarias WHERE code = ?", ('SMEL',)).fetchone()
    if not row_smel:
        c.execute(
            """INSERT INTO secretarias (id, name, code, address, phone, email, working_hours)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                85,
                'Secretaria Municipal de Esporte e Lazer',
                'SMEL',
                'Rua Garibaldi, s/n (Vila Olímpica) - Jardim Vinte e Cinco de Agosto, Duque de Caxias - RJ, 25075-080',
                '(21) 2652-7428',
                'smel@duquedecaxias.rj.gov.br',
                'Segunda a Sexta, das 08h às 17h'
            )
        )
        print("[main.db] Inserida secretaria SMEL com ID 85")
    else:
        c.execute(
            """UPDATE secretarias SET name = ?, address = ?, phone = ?, email = ?, working_hours = ?
               WHERE id = ?""",
            (
                'Secretaria Municipal de Esporte e Lazer',
                'Rua Garibaldi, s/n (Vila Olímpica) - Jardim Vinte e Cinco de Agosto, Duque de Caxias - RJ, 25075-080',
                '(21) 2652-7428',
                'smel@duquedecaxias.rj.gov.br',
                'Segunda a Sexta, das 08h às 17h',
                row_smel[0]
            )
        )
        print(f"[main.db] Atualizada secretaria SMEL (ID {row_smel[0]})")

    # 4. Inserir ou atualizar SMCSRPTER (ID 86)
    row_smcs = c.execute("SELECT id FROM secretarias WHERE code = ?", ('SMCSRPTER',)).fetchone()
    if not row_smcs:
        c.execute(
            """INSERT INTO secretarias (id, name, code, address, phone, email, working_hours)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                86,
                'Secretaria Municipal de Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral',
                'SMCSRPTER',
                'Alameda Dona Mariana, 91 - 25 de Agosto, Duque de Caxias - RJ, 25075-010',
                '(21) 2652-3835 / WhatsApp: (21) 99824-5903',
                'ouvidoria@duquedecaxias.rj.gov.br',
                'Segunda a Sexta, das 08h às 17h'
            )
        )
        print("[main.db] Inserida secretaria SMCSRPTER com ID 86")
    else:
        c.execute(
            """UPDATE secretarias SET name = ?, address = ?, phone = ?, email = ?, working_hours = ?
               WHERE id = ?""",
            (
                'Secretaria Municipal de Comunicação Social, Relações Públicas, Trabalho, Emprego e Renda e Ouvidoria Geral',
                'Alameda Dona Mariana, 91 - 25 de Agosto, Duque de Caxias - RJ, 25075-010',
                '(21) 2652-3835 / WhatsApp: (21) 99824-5903',
                'ouvidoria@duquedecaxias.rj.gov.br',
                'Segunda a Sexta, das 08h às 17h',
                row_smcs[0]
            )
        )
        print(f"[main.db] Atualizada secretaria SMCSRPTER (ID {row_smcs[0]})")

    conn.commit()
    print("[main.db] Alteracoes salvas com sucesso.")
    
    rows = c.execute("SELECT id, name, code, phone FROM secretarias WHERE id IN (72, 78, 85, 86)").fetchall()
    for r in rows:
        print(f"  -> ID {r[0]}: {r[1]} ({r[2]}) | Tel: {r[3]}")

    conn.close()

if __name__ == "__main__":
    update_main_db()

