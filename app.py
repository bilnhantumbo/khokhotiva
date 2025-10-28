from flask import Flask, render_template, session, redirect, url_for, request
import sqlite3
import os
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import uuid

app = Flask(__name__)
app.secret_key = 'khokotiva_secret'

# Configurações do Supabase
SUPABASE_URL = 'https://jjjiwdepcgvvzeflwxaq.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impqaml3ZGVwY2d2dnplZmx3eGFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1MTE2NDEsImV4cCI6MjA3NzA4NzY0MX0.LDS2LGy-ludnPaynzEz2AyX77S6ZMTTCk4rYj8uJW9A'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Dados de login
USERS = {
    'admin': 'khokhotiva123'
}

# Tipos de arquivo permitidos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_products():
    conn = sqlite3.connect('khokotiva.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return products

@app.route('/')
def index():
    products = get_products()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username] == password:
            session['user'] = username
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return "Login falhou! Tente novamente."
    
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/login')
    
    products = get_products()
    return render_template('admin.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect('/login')
        
    name = request.form['name']
    category = request.form['category']
    price = float(request.form['price'])
    
    print(f"DEBUG: Adicionando produto: {name}, {category}, {price}")
    
    # Processar imagem
    image_url = None
    if 'image' in request.files:
        image = request.files['image']
        print(f"DEBUG: Arquivo recebido: {image.filename}")
        
        if image.filename != '' and allowed_file(image.filename):
            print("DEBUG: Arquivo permitido, processando...")
            # Verificar tamanho
            image.seek(0, os.SEEK_END)
            file_size = image.tell()
            image.seek(0)
            print(f"DEBUG: Tamanho do arquivo: {file_size} bytes")
            
            if file_size <= MAX_FILE_SIZE:
                try:
                    # Gerar nome único
                    file_extension = image.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4()}.{file_extension}"
                    print(f"DEBUG: Nome único gerado: {unique_filename}")
                    
                    # Upload para Supabase
                    image_data = image.read()
                    print("DEBUG: Fazendo upload para Supabase...")
                    
                    upload_result = supabase.storage.from_('produtos').upload(unique_filename, image_data)
                    
                    print(f"DEBUG: Resultado do upload: {upload_result}")
                    
                    if upload_result:
                        # Criar URL manualmente
                        image_url = f"https://jjjiwdepcgvvzeflwxaq.supabase.co/storage/v1/object/public/produtos/{unique_filename}"
                        print(f"DEBUG: URL da imagem: {image_url}")
                    else:
                        print("DEBUG: Erro no upload para Supabase")
                        return "Erro ao fazer upload da imagem"
                        
                except Exception as e:
                    print(f"DEBUG: Erro no upload para Supabase: {e}")
                    return f"Erro ao fazer upload da imagem: {e}"
            else:
                print(f"DEBUG: Arquivo muito grande: {file_size} bytes")
                return "Arquivo muito grande! Máximo 5MB."
        else:
            print("DEBUG: Arquivo não permitido ou sem arquivo")
    else:
        print("DEBUG: Nenhum arquivo de imagem recebido")
    
    print(f"DEBUG: URL final da imagem: {image_url}")
    
    # INSERIR NA BASE DE DADOS - VERSÃO CORRIGIDA
    conn = sqlite3.connect('khokotiva.db')
    c = conn.cursor()
    
    # DEBUG: Verificar o que vamos inserir
    print(f"DEBUG A INSERIR: name={name}, category={category}, price={price}, image_url={image_url}")
    
    c.execute("INSERT INTO products (name, category, price, image_url) VALUES (?, ?, ?, ?)", 
              (name, category, price, image_url))
    conn.commit()
    
    # Verificar se foi inserido
    c.execute("SELECT * FROM products WHERE id = (SELECT MAX(id) FROM products)")
    last_product = c.fetchone()
    print(f"DEBUG PRODUTO INSERIDO: {last_product}")
    
    conn.close()
    
    print("DEBUG: Produto inserido na base de dados")
    return redirect('/admin')

@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if not session.get('logged_in'):
        return redirect('/login')
        
    conn = sqlite3.connect('khokotiva.db')
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)