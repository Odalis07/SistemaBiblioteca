from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from datetime import datetime

from config import Config
from models import db, Usuario, Libro, Prestamo, Multa, Autor

app = Flask(__name__)
app.config.from_object(Config)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 280,
    "pool_pre_ping": True
}

db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

with app.app_context():
    db.create_all()


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


@app.route('/usuarios')
@login_required
def usuarios():
    todos_usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=todos_usuarios, preguntas=PREGUNTAS_SECRETAS)

@app.route('/usuarios/add', methods=['POST'])
@login_required
def usuarios_add():
    nombre = request.form['nombre']
    correo = request.form['correo']
    password = request.form['password']
    rol = request.form.get('rol', 'lector')
    telefono = request.form.get('telefono', '')
    direccion = request.form.get('direccion', '')
    pregunta = request.form.get('pregunta_secreta', '')
    respuesta = request.form.get('respuesta_secreta', '').strip().lower()

    existe = Usuario.query.filter_by(correo=correo).first()
    if existe:
        flash('El correo ya está registrado', 'danger')
        return redirect(url_for('usuarios'))

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    respuesta_hash = bcrypt.generate_password_hash(respuesta).decode('utf-8') if respuesta else None

    nuevo = Usuario(
        nombre=nombre,
        correo=correo,
        password=password_hash,
        rol=rol,
        telefono=telefono,
        direccion=direccion,
        pregunta_secreta=pregunta,
        respuesta_secreta=respuesta_hash
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Usuario creado exitosamente', 'success')
    return redirect(url_for('usuarios'))

@app.route('/usuarios/edit/<int:id>', methods=['POST'])
@login_required
def usuarios_edit(id):
    usuario = Usuario.query.get_or_404(id)
    usuario.nombre = request.form['nombre']
    usuario.correo = request.form['correo']
    usuario.rol = request.form.get('rol', 'lector')
    usuario.telefono = request.form.get('telefono', '')
    usuario.direccion = request.form.get('direccion', '')

    new_password = request.form.get('password')
    if new_password:
        usuario.password = bcrypt.generate_password_hash(new_password).decode('utf-8')

    pregunta = request.form.get('pregunta_secreta')
    if pregunta:
        usuario.pregunta_secreta = pregunta
    
    respuesta = request.form.get('respuesta_secreta')
    if respuesta:
        usuario.respuesta_secreta = bcrypt.generate_password_hash(respuesta.strip().lower()).decode('utf-8')

    db.session.commit()
    flash('Usuario actualizado exitosamente', 'success')
    return redirect(url_for('usuarios'))

@app.route('/usuarios/delete', methods=['POST'])
@login_required
def usuarios_delete():
    usuario_id = request.form.get('id')
    if not usuario_id:
        flash('No se especificó el ID del usuario', 'danger')
        return redirect(url_for('usuarios'))
    
    usuario = Usuario.query.get(int(usuario_id))
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('usuarios'))

    if usuario.id == current_user.id:
        flash('No puedes eliminarte a ti mismo', 'danger')
        return redirect(url_for('usuarios'))

    # Cascade delete in Python code
    Multa.query.filter_by(usuario_id=usuario.id).delete()
    Prestamo.query.filter_by(usuario_id=usuario.id).delete()
    
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('usuarios'))


@app.route('/libros')
@login_required
def libros():
    todos_libros = Libro.query.all()
    return render_template('libros.html', libros=todos_libros)

@app.route('/libros/add', methods=['POST'])
@login_required
def libros_add():
    titulo = request.form['titulo']
    autor = request.form['autor']
    editorial = request.form.get('editorial', '')
    categoria = request.form.get('categoria', '')
    isbn = request.form.get('isbn', '')
    stock = int(request.form.get('stock', 1))
    anio = request.form.get('anio_publicacion')
    anio_publicacion = int(anio) if anio else None
    estado = request.form.get('estado', 'disponible')

    # Registrar el autor automáticamente si no existe en la base de datos
    if autor:
        autor_limpio = autor.strip()
        existe_autor = Autor.query.filter(Autor.nombre.ilike(autor_limpio)).first()
        if not existe_autor:
            nuevo_autor = Autor(
                nombre=autor_limpio,
                nacionalidad='Desconocida',
                fecha_nacimiento=None
            )
            db.session.add(nuevo_autor)

    nuevo = Libro(
        titulo=titulo,
        autor=autor,
        editorial=editorial,
        categoria=categoria,
        isbn=isbn,
        stock=stock,
        anio_publicacion=anio_publicacion,
        estado=estado
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Libro creado exitosamente y autor verificado/registrado', 'success')
    return redirect(url_for('libros'))

@app.route('/libros/edit/<int:id>', methods=['POST'])
@login_required
def libros_edit(id):
    libro = Libro.query.get_or_404(id)
    libro.titulo = request.form['titulo']
    autor = request.form['autor']
    libro.autor = autor
    libro.editorial = request.form.get('editorial', '')
    libro.categoria = request.form.get('categoria', '')
    libro.isbn = request.form.get('isbn', '')
    libro.stock = int(request.form.get('stock', 1))
    anio = request.form.get('anio_publicacion')
    libro.anio_publicacion = int(anio) if anio else None
    libro.estado = request.form.get('estado', 'disponible')

    # Registrar el autor automáticamente si no existe en la base de datos
    if autor:
        autor_limpio = autor.strip()
        existe_autor = Autor.query.filter(Autor.nombre.ilike(autor_limpio)).first()
        if not existe_autor:
            nuevo_autor = Autor(
                nombre=autor_limpio,
                nacionalidad='Desconocida',
                fecha_nacimiento=None
            )
            db.session.add(nuevo_autor)

    db.session.commit()
    flash('Libro actualizado exitosamente y autor verificado/registrado', 'success')
    return redirect(url_for('libros'))


@app.route('/libros/delete', methods=['POST'])
@login_required
def libros_delete():
    libro_id = request.form.get('id')
    if not libro_id:
        flash('No se especificó el ID del libro', 'danger')
        return redirect(url_for('libros'))
    
    libro = Libro.query.get(int(libro_id))
    if not libro:
        flash('Libro no encontrado', 'danger')
        return redirect(url_for('libros'))

    # Delete loans associated
    Prestamo.query.filter_by(libro_id=libro.id).delete()

    db.session.delete(libro)
    db.session.commit()
    flash('Libro eliminado exitosamente', 'success')
    return redirect(url_for('libros'))


@app.route('/autores')
@login_required
def autores():
    todos_autores = Autor.query.all()
    return render_template('autores.html', autores=todos_autores)

@app.route('/autores/add', methods=['POST'])
@login_required
def autores_add():
    nombre = request.form['nombre']
    nacionalidad = request.form.get('nacionalidad', '')
    fecha_nacimiento = request.form.get('fecha_nacimiento', '')

    nuevo = Autor(
        nombre=nombre,
        nacionalidad=nacionalidad,
        fecha_nacimiento=fecha_nacimiento
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Autor registrado exitosamente', 'success')
    return redirect(url_for('autores'))

@app.route('/autores/edit/<int:id>', methods=['POST'])
@login_required
def autores_edit(id):
    autor = Autor.query.get_or_404(id)
    autor.nombre = request.form['nombre']
    autor.nacionalidad = request.form.get('nacionalidad', '')
    autor.fecha_nacimiento = request.form.get('fecha_nacimiento', '')

    db.session.commit()
    flash('Autor actualizado exitosamente', 'success')
    return redirect(url_for('autores'))

@app.route('/autores/delete', methods=['POST'])
@login_required
def autores_delete():
    autor_id = request.form.get('id')
    if not autor_id:
        flash('No se especificó el ID del autor', 'danger')
        return redirect(url_for('autores'))
    
    autor = Autor.query.get(int(autor_id))
    if not autor:
        flash('Autor no encontrado', 'danger')
        return redirect(url_for('autores'))

    db.session.delete(autor)
    db.session.commit()
    flash('Autor eliminado exitosamente', 'success')
    return redirect(url_for('autores'))


@app.route('/prestamos')
@login_required
def prestamos():
    todos_prestamos = Prestamo.query.all()
    todos_usuarios = Usuario.query.all()
    todos_libros = Libro.query.filter(Libro.stock > 0).all() # only books with stock for new loans
    all_libros_for_edit = Libro.query.all() # all books for edit dropdowns
    return render_template('prestamos.html', prestamos=todos_prestamos, usuarios=todos_usuarios, libros=todos_libros, todos_libros=all_libros_for_edit)

@app.route('/prestamos/add', methods=['POST'])
@login_required
def prestamos_add():
    usuario_id = int(request.form['usuario_id'])
    libro_id = int(request.form['libro_id'])
    fecha_p = request.form.get('fecha_prestamo')
    fecha_d = request.form.get('fecha_devolucion')
    estado = request.form.get('estado', 'activo')

    libro = Libro.query.get(libro_id)
    if not libro or libro.stock <= 0:
        flash('El libro no tiene stock disponible', 'danger')
        return redirect(url_for('prestamos'))

    fecha_prestamo = datetime.strptime(fecha_p, '%Y-%m-%d') if fecha_p else datetime.utcnow()
    fecha_devolucion = datetime.strptime(fecha_d, '%Y-%m-%d') if fecha_d else None

    # Decrement stock
    libro.stock -= 1
    if libro.stock == 0:
        libro.estado = 'prestado'

    nuevo = Prestamo(
        usuario_id=usuario_id,
        libro_id=libro_id,
        fecha_prestamo=fecha_prestamo,
        fecha_devolucion=fecha_devolucion,
        estado=estado
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Préstamo registrado exitosamente', 'success')
    return redirect(url_for('prestamos'))

@app.route('/prestamos/edit/<int:id>', methods=['POST'])
@login_required
def prestamos_edit(id):
    prestamo = Prestamo.query.get_or_404(id)
    old_libro_id = prestamo.libro_id
    new_libro_id = int(request.form['libro_id'])
    old_estado = prestamo.estado
    new_estado = request.form.get('estado', 'activo')

    prestamo.usuario_id = int(request.form['usuario_id'])
    prestamo.libro_id = new_libro_id
    
    fecha_p = request.form.get('fecha_prestamo')
    fecha_d = request.form.get('fecha_devolucion')
    if fecha_p:
        prestamo.fecha_prestamo = datetime.strptime(fecha_p, '%Y-%m-%d')
    if fecha_d:
        prestamo.fecha_devolucion = datetime.strptime(fecha_d, '%Y-%m-%d')

    prestamo.estado = new_estado

    # Adjust stock if book changed or state returned/active changed
    if old_libro_id != new_libro_id:
        # Returned old book
        old_libro = Libro.query.get(old_libro_id)
        if old_libro:
            old_libro.stock += 1
            if old_libro.stock > 0:
                old_libro.estado = 'disponible'
        # Loaned new book
        new_libro = Libro.query.get(new_libro_id)
        if new_libro:
            new_libro.stock -= 1
            if new_libro.stock <= 0:
                new_libro.estado = 'prestado'
    else:
        # Same book, check status transition
        libro = Libro.query.get(new_libro_id)
        if libro:
            if old_estado == 'activo' and new_estado == 'devuelto':
                libro.stock += 1
                if libro.stock > 0:
                    libro.estado = 'disponible'
            elif old_estado == 'devuelto' and new_estado == 'activo':
                libro.stock -= 1
                if libro.stock <= 0:
                    libro.estado = 'prestado'

    db.session.commit()
    flash('Préstamo actualizado exitosamente', 'success')
    return redirect(url_for('prestamos'))

@app.route('/prestamos/delete', methods=['POST'])
@login_required
def prestamos_delete():
    prestamo_id = request.form.get('id')
    if not prestamo_id:
        flash('No se especificó el ID del préstamo', 'danger')
        return redirect(url_for('prestamos'))
    
    prestamo = Prestamo.query.get(int(prestamo_id))
    if not prestamo:
        flash('Préstamo no encontrado', 'danger')
        return redirect(url_for('prestamos'))

    # If deleted loan was active, restore book stock
    if prestamo.estado == 'activo':
        libro = Libro.query.get(prestamo.libro_id)
        if libro:
            libro.stock += 1
            if libro.stock > 0:
                libro.estado = 'disponible'

    # Set foreign keys in multas to null
    Multa.query.filter_by(prestamo_id=prestamo.id).update({Multa.prestamo_id: None})

    db.session.delete(prestamo)
    db.session.commit()
    flash('Préstamo eliminado exitosamente', 'success')
    return redirect(url_for('prestamos'))


@app.route('/multas')
@login_required
def multas():
    todos_multas = Multa.query.all()
    todos_usuarios = Usuario.query.all()
    todos_prestamos = Prestamo.query.filter_by(estado='activo').all() # only active loans for context
    all_prestamos_for_edit = Prestamo.query.all()
    return render_template('multas.html', multas=todos_multas, usuarios=todos_usuarios, prestamos=todos_prestamos, todos_prestamos=all_prestamos_for_edit)

@app.route('/multas/add', methods=['POST'])
@login_required
def multas_add():
    usuario_id = int(request.form['usuario_id'])
    prestamo_id_str = request.form.get('prestamo_id')
    prestamo_id = int(prestamo_id_str) if (prestamo_id_str and prestamo_id_str != 'None' and prestamo_id_str != '') else None
    monto = float(request.form['monto'])
    motivo = request.form.get('motivo', '')
    pagada = request.form.get('pagada') == 'on' or request.form.get('pagada') == 'true'

    nuevo = Multa(
        usuario_id=usuario_id,
        prestamo_id=prestamo_id,
        monto=monto,
        motivo=motivo,
        pagada=pagada
    )
    db.session.add(nuevo)
    db.session.commit()
    flash('Multa registrada exitosamente', 'success')
    return redirect(url_for('multas'))

@app.route('/multas/edit/<int:id>', methods=['POST'])
@login_required
def multas_edit(id):
    multa = Multa.query.get_or_404(id)
    multa.usuario_id = int(request.form['usuario_id'])
    prestamo_id_str = request.form.get('prestamo_id')
    multa.prestamo_id = int(prestamo_id_str) if (prestamo_id_str and prestamo_id_str != 'None' and prestamo_id_str != '') else None
    multa.monto = float(request.form['monto'])
    multa.motivo = request.form.get('motivo', '')
    multa.pagada = request.form.get('pagada') == 'on' or request.form.get('pagada') == 'true' or request.form.get('pagada') == '1'

    db.session.commit()
    flash('Multa actualizada exitosamente', 'success')
    return redirect(url_for('multas'))

@app.route('/multas/delete', methods=['POST'])
@login_required
def multas_delete():
    multa_id = request.form.get('id')
    if not multa_id:
        flash('No se especificó el ID de la multa', 'danger')
        return redirect(url_for('multas'))
    
    multa = Multa.query.get(int(multa_id))
    if not multa:
        flash('Multa no encontrada', 'danger')
        return redirect(url_for('multas'))

    db.session.delete(multa)
    db.session.commit()
    flash('Multa eliminada exitosamente', 'success')
    return redirect(url_for('multas'))


if __name__ == '__main__':
    app.run(debug=True)