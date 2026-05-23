from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Obtener datos del formulario
    name = request.form.get('name')
    age = request.form.get('age')
    
    # Procesar los datos (aquí solo los mostramos en pantalla)
    return f"Hola, {name}. Tienes {age} años."

if __name__ == '__main__':
    app.run(debug=True)