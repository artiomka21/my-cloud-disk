from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Логин-менеджер
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Проверка/создание папки uploads
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.mkdir(app.config['UPLOAD_FOLDER'])

# Подключение к SQLite
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Пользователь
class User(UserMixin):
    def __init__(self, id_, username, password):
        self.id = id_
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['username'], user['password'])
    return None

# Главная страница
@app.route('/')
def index():
    return redirect(url_for('login'))

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], username))
            flash('Регистрация успешна. Войдите.')
            return redirect(url_for('login'))
        except:
            flash('Имя пользователя занято.')
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['password']))
            return redirect(url_for('dashboard'))
        flash('Неверный логин или пароль.')
    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Панель управления
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    files = os.listdir(user_folder)
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(user_folder, f.filename))
        flash('Файл загружен.')
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', files=files)

# Скачать файл
@app.route('/download/<filename>')
@login_required
def download(filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    return send_from_directory(user_folder, filename, as_attachment=True)

# Удалить файл
@app.route('/delete/<filename>')
@login_required
def delete(filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    os.remove(os.path.join(user_folder, filename))
    flash('Файл удалён.')
    return redirect(url_for('dashboard'))

# Создание БД при первом запуске


if __name__ == '__main__':
    db = get_db()
    db.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    db.commit()

    app.run(debug=True)

import os

if __name__ == '__main__':
    db = get_db()
    db.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    db.commit()

    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
from flask import send_from_directory
import os

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

@app.route('/download/<path:username>/<path:filename>')
def download_file(username, filename):
    folder_path = os.path.join(UPLOAD_FOLDER, username)
    return send_from_directory(folder_path, filename, as_attachment=True)
