import sqlite3

conn = sqlite3.connect('khokotiva.db')
c = conn.cursor()
c.execute("SELECT * FROM products WHERE id = (SELECT MAX(id) FROM products)")
latest_product = c.fetchone()
conn.close()

print("ÚLTIMO PRODUTO ADICIONADO:")
print(f"ID: {latest_product[0]}")
print(f"Nome: {latest_product[1]}")
print(f"URL da imagem: {latest_product[4]}")