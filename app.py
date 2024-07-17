from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from flask import send_file
from openpyxl import Workbook
app = Flask(__name__)
app.secret_key = 'your_secret_key'

def create_table():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS 
                      inventory(itemId TEXT, itemName TEXT, itemPrice TEXT, itemQuantity TEXT)""")
    conn.commit()
    conn.close()

# Appel de la fonction pour s'assurer que la table est créée au démarrage de l'application
create_table()

def get_db():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ajout d'utilisateurs par défaut si la table est vide
def add_default_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count == 0:
            default_users = {
                'admin': '1',
                'user1': '1'
            }
            for username, password in default_users.items():
                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()

# Initialisation de la base de données au démarrage de l'application


# Formulaire de connexion
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

# Formulaire pour les items d'inventaire
class InventoryForm(FlaskForm):
    id = StringField('ID', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Route pour la page d'accueil

@app.route('/')
def index():
    conn = get_db()
    items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()
    return render_template('index.html', items=items)

# Route pour la page de connexion

# Route pour la génération du fichier Excel
@app.route('/generate_excel')
def generate_excel():
    conn = get_db()
    items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()

    # Création du fichier Excel
    from openpyxl import Workbook
    
    wb = Workbook()
    ws = wb.active
    ws.append(['ID', 'Name', 'Price', 'Quantity'])

    for item in items:
        ws.append([item['itemId'], item['itemName'], item['itemPrice'], item['itemQuantity']])

    excel_filename = 'inventory.xlsx'
    wb.save(excel_filename)

    return send_file(excel_filename, as_attachment=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['username'] = username
            return redirect(url_for('inventory'))  # Rediriger vers la page d'inventaire après la connexion réussie
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

# Route pour la page d'inventaire
@app.route('/inventory')
def inventory():
    conn = get_db()
    items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()
    
    return render_template('inventory.html', items=items)

# Route pour la page d'ajout d'un nouvel item
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        price = request.form['price']
        quantity = request.form['quantity']
        
        conn = get_db()
        conn.execute('INSERT INTO inventory (itemId, itemName, itemPrice, itemQuantity) VALUES (?, ?, ?, ?)',
                     (id, name, price, quantity))
        conn.commit()
        conn.close()
        return redirect(url_for('inventory'))
    return render_template('add.html')
#pour quitter le user

# Ajouter cette route pour gérer la déconnexion
@app.route('/logout')
def logout():
    session.pop('username', None)  # Supprime l'utilisateur de la session
    flash('You have been logged out')
    return redirect(url_for('login'))  # Rediriger vers la page de connexion après la déconnexion


# Route pour la suppression d'un item
@app.route('/delete/<string:id>')
def delete(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    conn.execute('DELETE FROM inventory WHERE itemId = ?', (id,))
    conn.commit()
    conn.close()
    flash('Item deleted successfully')
    return redirect(url_for('inventory'))  # Rediriger vers la page d'accueil après la suppression

# Route pour la mise à jour d'un item
@app.route('/update/<string:id>', methods=['GET', 'POST'])
def update(id):
    conn = get_db()
    item = conn.execute('SELECT * FROM inventory WHERE itemId = ?', (id,)).fetchone()
    conn.close()
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form['quantity']
        
        conn = get_db()
        conn.execute('UPDATE inventory SET itemName = ?, itemPrice = ?, itemQuantity = ? WHERE itemId = ?',
                     (name, price, quantity, id))
        conn.commit()
        conn.close()
        return redirect(url_for('inventory'))
    
    return render_template('update.html', item=item)

# Route pour la page d'enregistrement d'un nouvel utilisateur
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = get_db()
        hashed_password = generate_password_hash(password)
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('User registered successfully')
            return redirect(url_for('login'))  # Rediriger vers la page de connexion après l'enregistrement
        except sqlite3.IntegrityError:
            flash('Username already exists')
        finally:
            conn.close()
    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
