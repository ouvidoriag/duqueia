import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/db/main.db')
c = conn.cursor()

print("=" * 80)
print("1. BUSCA POR CRECHE / EDUCAÇÃO INFANTIL")
print("=" * 80)
c.execute("SELECT id, name, description, how_to_access, address FROM services WHERE name LIKE '%creche%' OR description LIKE '%creche%'")
for r in c.fetchall():
    print(f"ID {r[0]}: {r[1]}")
    print(f"  Desc: {r[2]}")
    print(f"  Acesso: {r[3]} | Endereço: {r[4]}\n")

print("=" * 80)
print("2. BUSCA POR TRANSFERÊNCIA ESCOLAR / ALUNOS")
print("=" * 80)
c.execute("SELECT id, name, description, how_to_access, address FROM services WHERE name LIKE '%transfer%' OR description LIKE '%transfer%'")
for r in c.fetchall():
    print(f"ID {r[0]}: {r[1]}")
    print(f"  Desc: {r[2]}")
    print(f"  Acesso: {r[3]} | Endereço: {r[4]}\n")

print("=" * 80)
print("3. BUSCA POR ISENÇÃO DE IPTU / APOSENTADO / TRIBUTOS")
print("=" * 80)
c.execute("SELECT id, name, description, how_to_access, address FROM services WHERE name LIKE '%isen%' OR name LIKE '%aposentad%' OR description LIKE '%isen%' OR description LIKE '%aposentad%'")
for r in c.fetchall():
    print(f"ID {r[0]}: {r[1]}")
    print(f"  Desc: {r[2]}")
    print(f"  Acesso: {r[3]} | Endereço: {r[4]}\n")

print("=" * 80)
print("4. BUSCA POR REGRAS DE NEGÓCIO (regras_negocio) PARA ESTES TEMAS")
print("=" * 80)
c.execute("SELECT id, tema, assunto, conteudo FROM regras_negocio WHERE assunto LIKE '%creche%' OR assunto LIKE '%matr%' OR assunto LIKE '%transfer%' OR assunto LIKE '%isen%' OR assunto LIKE '%iptu%' OR assunto LIKE '%autista%'")
for r in c.fetchall():
    print(f"ID: {r[0]} | Tema: {r[1]} | Assunto: {r[2]}")
    print(f"  Conteúdo: {r[3][:200]}...\n")
