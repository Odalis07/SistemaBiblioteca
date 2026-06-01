from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from datetime import datetime

from config import Config
from models import db, Usuario

app = Flask(__name__)
app.config.from_object(Config)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 280,
    "pool_pre_ping": True
}

db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

PREGUNTAS_SECRETAS = [
    "¿Cuál es el nombre de tu primera mascota?",
    "¿En qué ciudad naciste?",
    "¿Cuál es tu película favorita?",
    "¿Cómo se llamaba tu primera escuela?",
    "¿Cuál es el segundo nombre de tu madre?"
]

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


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
        pregunta = request.form['pregunta_secreta']
        respuesta_limpia = request.form['respuesta_secreta'].strip().lower()

        existe = Usuario.query.filter_by(correo=correo).first()
        if existe:
            flash('El correo ya está registrado', 'warning')
            return redirect(url_for('register'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        respuesta_hash = bcrypt.generate_password_hash(respuesta_limpia).decode('utf-8')

        nuevo_usuario = Usuario(
            nombre=nombre,
            correo=correo,
            password=password_hash,
            pregunta_secreta=pregunta,
            respuesta_secreta=respuesta_hash
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', preguntas=PREGUNTAS_SECRETAS)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    usuario = None
    correo = request.args.get('correo', '')

    if request.method == 'POST':
        accion = request.form.get('accion')
        correo = request.form.get('correo')
        usuario = Usuario.query.filter_by(correo=correo).first()

        if accion == 'verificar_correo':
            if not usuario:
                flash('El correo electrónico no está registrado', 'danger')
                return render_template('forgot_password.html', usuario=None, correo='')
            
            if not usuario.pregunta_secreta:
                flash('Este usuario no configuró una pregunta secreta.', 'warning')
                return render_template('forgot_password.html', usuario=None, correo='')

            return render_template('forgot_password.html', usuario=usuario, correo=correo)

        elif accion == 'restablecer_password':
            if usuario:
                respuesta_ingresada = request.form.get('respuesta_secreta', '').strip().lower()
                nueva_password = request.form.get('nueva_password')

                if bcrypt.check_password_hash(usuario.respuesta_secreta, respuesta_ingresada):
                    usuario.password = bcrypt.generate_password_hash(nueva_password).decode('utf-8')
                    db.session.commit()
                    flash('Contraseña actualizada con éxito. Ya puedes iniciar sesión.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('La respuesta a la pregunta secreta es incorrecta.', 'danger')
                    return render_template('forgot_password.html', usuario=usuario, correo=correo)

    return render_template('forgot_password.html', usuario=usuario, correo=correo)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))


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