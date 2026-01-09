from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import requests  # <--- IMPORTANTE: Librería para llamar a otras APIs

app = Flask(__name__)

# Configuración JWT
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
jwt = JWTManager(app)

# --- CONFIGURACIÓN OPENWEATHER ---
OPENWEATHER_API_KEY = 'e940390402fe5b6c07ac4a1be179fdc6' 
GEOCODING_API_URL = 'http://api.openweathermap.org/geo/1.0/direct'
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'

# Base de datos simulada
users = {}

# ---------------------------------------------------------
# RUTAS DE AUTENTICACIÓN (Del Ejercicio 6)
# ---------------------------------------------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username in users:
        return jsonify({"msg": "User already exists"}), 400
        
    users[username] = generate_password_hash(password)
    return jsonify({"msg": "User created"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username not in users or not check_password_hash(users[username], password):
        return jsonify({"msg": "Bad username or password"}), 401
        
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

# ---------------------------------------------------------
# RUTA DEL CLIMA (Ejercicio 7 - El Reto)
# ---------------------------------------------------------
@app.route('/weather', methods=['GET'])
def get_weather():
    # 1. Validar que tenemos API Key configurada
    if OPENWEATHER_API_KEY == 'TU_API_KEY_AQUI':
        return jsonify({
            'error': 'Configuration Error', 
            'message': 'Please set a valid OPENWEATHER_API_KEY in app.py'
        }), 500

    # 2. Obtener parámetros de la URL (ej: /weather?city=Madrid&country=ES)
    city = request.args.get('city')
    country = request.args.get('country', '') # Opcional

    if not city:
        return jsonify({'error': 'Missing data', 'message': 'City parameter is required'}), 400

    try:
        # -----------------------------------------------------
        # PASO 1: GEOCODIFICACIÓN (Ciudad -> Coordenadas)
        # -----------------------------------------------------
        # Construimos la query. Ej: "Madrid,ES" o solo "Madrid"
        query = f"{city},{country}" if country else city
        
        geo_payload = {
            'q': query,
            'limit': 1,
            'appid': OPENWEATHER_API_KEY
        }

        # Llamada externa 1
        geo_response = requests.get(GEOCODING_API_URL, params=geo_payload)
        geo_response.raise_for_status() # Lanza error si falla la conexión
        geo_data = geo_response.json()

        if not geo_data:
            return jsonify({'error': 'Not Found', 'message': f'City "{city}" not found'}), 404

        # Extraemos latitud y longitud
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        found_name = geo_data[0]['name']
        found_country = geo_data[0]['country']

        # -----------------------------------------------------
        # PASO 2: CLIMA ACTUAL (Coordenadas -> Datos)
        # -----------------------------------------------------
        weather_payload = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric', # Para obtener Celsius
            'lang': 'es'       # Descripción en español
        }

        # Llamada externa 2
        weather_response = requests.get(WEATHER_API_URL, params=weather_payload)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        # -----------------------------------------------------
        # PASO 3: RESPUESTA FINAL
        # -----------------------------------------------------
        return jsonify({
            'location': {
                'city': found_name,
                'country': found_country,
                'coordinates': {'lat': lat, 'lon': lon}
            },
            'weather': {
                'temperature': weather_data['main']['temp'],
                'description': weather_data['weather'][0]['description'],
                'humidity': weather_data['main']['humidity'],
                'wind_speed': weather_data['wind']['speed']
            }
        }), 200

    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': 'External API Error', 'message': str(http_err)}), 502
    except Exception as err:
        return jsonify({'error': 'Internal Error', 'message': str(err)}), 500

if __name__ == '__main__':
    print("Servidor corriendo. Prueba: http://127.0.0.1:5000/weather?city=Madrid")
    app.run(debug=True)

