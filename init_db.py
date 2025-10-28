import sqlite3

conn = sqlite3.connect('khokotiva.db')
c = conn.cursor()

# Tabela de produtos
c.execute('''CREATE TABLE IF NOT EXISTS products
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              category TEXT NOT NULL,
              price REAL NOT NULL,
              image TEXT)''')

# Produto de exemplo
c.execute("INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
          ('Produto Exemplo', 'Categoria Teste', 29.99))

conn.commit()
conn.close()
print("Base de dados criada com sucesso!")