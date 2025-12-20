from flask import Flask

app = Flask(__name__)

# Crear el archivo app.py
@app.route('/')
def hello_world():
    return '¡Hola, estudiantes!'
    
# Rutas
@app.route('/about')
def about():
    return '¡Bienvenidos a mi primera aplicación Flask!'

@app.route('/user/<username>')
def show_user(username):
    return f'¡Hola, {username}!'

# METODOS HTTP
from flask import request

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return 'Procesando login...'
    return 'Por favor, inicia sesión'

if __name__ == '__main__':
    app.run(debug=True)