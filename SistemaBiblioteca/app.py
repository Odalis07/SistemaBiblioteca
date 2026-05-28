from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

from config import Config
from models import db, Usuario

app = Flask(__name__)
app.config.from_object(Config)

# CONFIGURACIÓN ANTICAÍDAS POSTGRESQL (Añadido por seguridad)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 280,
    "pool_pre_ping": True
}

# BASE DE DATOS
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# --- RUTAS DE ACCESO ---

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and bcrypt.check_password_hash(usuario.password, password):
            login_user(usuario)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']

        existe = Usuario.query.filter_by(correo=correo).first()

        if existe:
            flash('El correo ya está registrado', 'warning')
            return redirect(url_for('register'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            password=password_hash
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/forgot-password', endpoint='forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))


# --- RUTAS DEL SISTEMA DE BIBLIOTECA (PROTEGIDAS) ---

@app.route('/index')
@login_required
def dashboard():
    return render_template('index.html')


@app.route('/libros')
@login_required
def libros():
    return render_template('libros.html')


@app.route('/autores')
@login_required
def autores():
    return render_template('autores.html')


@app.route('/prestamos')
@login_required
def prestamos():
    return render_template('prestamos.html')


@app.route('/multas')
@login_required
def multas():
    return render_template('multas.html')


if __name__ == '__main__':
    app.run(debug=True)