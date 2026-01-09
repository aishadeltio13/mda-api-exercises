from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import uuid  # <--- 1. Importamos librería para generar claves únicas
from functools import wraps

app = Flask(__name__)
auth = HTTPBasicAuth()

# Base de datos simulada
users = {}

# ============================================================================
# VERIFICACIÓN AUTH BÁSICA (Solo para recuperar la clave perdida)
# ============================================================================

@auth.verify_password
def verify_password(username, password):
    """Verifica usuario y contraseña para Auth Básica"""
    if username in users:
        if check_password_hash(users[username]['password'], password):
            return username
    return None


# ============================================================================
# DECORADOR API KEY (El corazón de este ejercicio)
# ============================================================================

def api_key_required(f):
    """
    Decorador para proteger rutas con autenticación por API Key.
    Busca la cabecera 'x-api-key'.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # <--- 2. Obtenemos la clave de las cabeceras
        api_key = request.headers.get('x-api-key')

        if not api_key:
            return jsonify({'error': 'API key missing', 'message': 'Include x-api-key header'}), 401

        # <--- 3. Verificamos si la clave existe en nuestra base de datos
        # Recorremos todos los usuarios para ver si alguno tiene esta clave
        for username, user_data in users.items():
            if user_data.get('api_key') == api_key:
                # ¡Clave válida! Ejecutamos la función original
                return f(*args, **kwargs)

        # Si termina el bucle y no la encuentra:
        return jsonify({'error': 'Invalid API key', 'message': 'API key not recognized'}), 401

    return decorated


# ============================================================================
# ENDPOINTS PÚBLICOS
# ============================================================================

@app.route('/register', methods=['POST'])
def register():
    """Registra un usuario nuevo y devuelve su API Key"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'error': 'User already exists'}), 409

    # <--- 4. Generamos una API Key única (UUID v4) y la convertimos a texto
    api_key = str(uuid.uuid4())

    # Guardamos el usuario
    users[username] = {
        'password': generate_password_hash(password),
        'api_key': api_key
    }

    return jsonify({
        'message': 'User registered successfully',
        'username': username,
        'api_key': api_key  # Devolvemos la clave para que el usuario la guarde
    }), 201


# ============================================================================
# ENDPOINTS PROTEGIDOS POR AUTH BÁSICA (Recuperación)
# ============================================================================

# <--- 5. Método GET para recuperar información
@app.route('/api-key', methods=['GET'])  
@auth.login_required
def get_api_key():
    """
    Recuperar tu API Key si la has perdido.
    Requiere Auth Básica (Usuario y Contraseña).
    """
    current_user = auth.current_user()

    return jsonify({
        'username': current_user,
        'api_key': users[current_user]['api_key']
    }), 200


# ============================================================================
# ENDPOINTS PROTEGIDOS POR API KEY (Uso diario)
# ============================================================================

@app.route('/users', methods=['GET'])
@api_key_required  # <--- 6. Aplicamos nuestro decorador personalizado
def get_users():
    """
    Obtener lista de usuarios.
    Requiere cabecera 'x-api-key'.
    """
    user_list = list(users.keys())
    return jsonify({
        'users': user_list,
        'count': len(user_list)
    }), 200


# ============================================================================
# MANEJO DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405


if __name__ == '__main__':
    # Mensajes de ayuda al iniciar
    print("\n" + "="*70)
    print("EJERCICIO 5: API KEY AUTHENTICATION - CORREGIDO")
    print("="*70)
    print("Server running at: http://127.0.0.1:5000")
    print("="*70 + "\n")

    app.run(debug=True)