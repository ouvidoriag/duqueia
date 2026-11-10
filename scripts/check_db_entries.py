import sqlite3

conn = sqlite3.connect('data/db/main.db')
c = conn.cursor()

c.execute("SELECT name, address, phone FROM secretaria_unidades WHERE address LIKE '%Xer%m%' OR name LIKE '%Xer%m%'")
for r in c.fetchall():
    print(r[0], "|", r[1])

conn.close()
