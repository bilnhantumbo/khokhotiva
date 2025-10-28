from flask import Flask, render_template, session, redirect, url_for, request
import os
from supabase import create_client, Client
import uuid

app = Flask(__name__)
app.secret_key = 'khokotiva_secret'

# Configurações do Supabase (Corretas)
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

# ===== FUNÇÃO ATUALIZADA =====
def get_products():
    """Busca produtos do banco de dados Supabase."""
    try:
        # Seleciona todos os produtos da tabela 'products'
        response = supabase.table('products').select('*').order('id', desc=True).execute()
        
        products_list_of_dicts = response.data
        
        # O seu template index.html espera uma LISTA DE TUPLAS (id, name, category, price, image_url)
        # Vamos converter a resposta do Supabase para esse formato:
        products_list_of_tuples = []
        for product in products_list_of_dicts:
            products_list_of_tuples.append(
                (
                    product['id'],
                    product['name'],
                    product['category'],
                    product['price'],
                    product['image_url']
                )
            )
        
        print(f"DEBUG: {len(products_list_of_tuples)} produtos encontrados no Supabase.")
        return products_list_of_tuples
        
    except Exception as e:
        print(f"ERRO ao buscar produtos no Supabase: {e}")
        return []

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

# ===== FUNÇÃO ATUALIZADA =====
@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect('/login')
        
    name = request.form['name']
    category = request.form['category']
    price = float(request.form['price'])
    
    print(f"DEBUG: Adicionando produto: {name}, {category}, {price}")
    
    # Processar imagem (Seu código de upload já estava correto!)
    image_url = None
    if 'image' in request.files:
        image = request.files['image']
        print(f"DEBUG: Arquivo recebido: {image.filename}")
        
        if image.filename != '' and allowed_file(image.filename):
            print("DEBUG: Arquivo permitido, processando...")
            image.seek(0, os.SEEK_END)
            file_size = image.tell()
            image.seek(0)
            print(f"DEBUG: Tamanho do arquivo: {file_size} bytes")
            
            if file_size <= MAX_FILE_SIZE:
                try:
                    file_extension = image.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4()}.{file_extension}"
                    print(f"DEBUG: Nome único gerado: {unique_filename}")
                    
                    image_data = image.read()
                    print("DEBUG: Fazendo upload para Supabase Storage...")
                    
                    # CORREÇÃO: Passar o content_type explicitamente
                    content_type = image.content_type
                    upload_result = supabase.storage.from_('produtos').upload(
                        unique_filename, 
                        image_data,
                        file_options={"content-type": content_type}
                    )
                    
                    print(f"DEBUG: Resultado do upload: {upload_result.status_code}")
                    
                    if upload_result.status_code == 200:
                        image_url = f"https://jjjiwdepcgvvzeflwxaq.supabase.co/storage/v1/object/public/produtos/{unique_filename}"
                        print(f"DEBUG: URL da imagem: {image_url}")
                    else:
                        print(f"DEBUG: Erro no upload para Supabase: {upload_result.text}")
                        return f"Erro ao fazer upload da imagem: {upload_result.text}"
                        
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
    
    # ===== INSERIR NO SUPABASE (NÃO MAIS NO SQLITE) =====
    try:
        data_to_insert = {
            'name': name,
            'category': category,
            'price': price,
            'image_url': image_url
        }
        
        print(f"DEBUG A INSERIR: {data_to_insert}")
        
        response = supabase.table('products').insert(data_to_insert).execute()
        
        print(f"DEBUG PRODUTO INSERIDO NO SUPABASE: {response.data}")
        
    except Exception as e:
        print(f"ERRO ao inserir produto no Supabase: {e}")
        return f"Erro ao salvar produto: {e}"
    
    print("DEBUG: Produto inserido na base de dados")
    return redirect('/admin')

# ===== FUNÇÃO ATUALIZADA =====
@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if not session.get('logged_in'):
        return redirect('/login')
        
    try:
        print(f"DEBUG: Apagando produto ID: {product_id} do Supabase...")
        
        # (Opcional: Apagar a imagem do Storage antes de apagar o registro)
        
        # Apagar o registro do banco de dados
        response = supabase.table('products').delete().eq('id', product_id).execute()
        
        print(f"DEBUG PRODUTO APAGADO: {response.data}")
        
    except Exception as e:
        print(f"ERRO ao apagar produto no Supabase: {e}")
        return f"Erro ao apagar produto: {e}"
    
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)