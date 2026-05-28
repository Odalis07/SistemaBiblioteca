from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# USUARIOS

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    rol = db.Column(db.String(20), default='lector')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    prestamos = db.relationship('Prestamo', backref='usuario', lazy=True)
    multas = db.relationship('Multa', backref='usuario', lazy=True)



# LIBROS

class Libro(db.Model):
    __tablename__ = 'libros'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150), nullable=False)
    editorial = db.Column(db.String(100))
    categoria = db.Column(db.String(100))
    isbn = db.Column(db.String(50), unique=True)
    stock = db.Column(db.Integer, default=1)
    anio_publicacion = db.Column(db.Integer)
    estado = db.Column(db.String(20), default='disponible')

    prestamos = db.relationship('Prestamo', backref='libro', lazy=True)



# PRÉSTAMOS

class Prestamo(db.Model):
    __tablename__ = 'prestamos'

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)

    fecha_prestamo = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_devolucion = db.Column(db.DateTime)

    estado = db.Column(db.String(20), default='activo')

 
    multa = db.relationship('Multa', backref='prestamo', uselist=False)



# MULTAS

class Multa(db.Model):
    __tablename__ = 'multas'

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

   
    prestamo_id = db.Column(db.Integer, db.ForeignKey('prestamos.id'), nullable=True)

    monto = db.Column(db.Float, nullable=False)
    motivo = db.Column(db.String(255))
    pagada = db.Column(db.Boolean, default=False)
    fecha_multa = db.Column(db.DateTime, default=datetime.utcnow)



# REPORTES

class Reporte(db.Model):
    __tablename__ = 'reportes'

    id = db.Column(db.Integer, primary_key=True)

    tipo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)

    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)