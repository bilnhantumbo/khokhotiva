import sqlite3

conn = sqlite3.connect('khokotiva.db')
c = conn.cursor()
c.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
conn.commit()
conn.close()
print("Base de dados atualizada para suportar imagens!")
