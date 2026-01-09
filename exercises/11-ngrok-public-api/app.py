from flask import Flask, request, jsonify

app = Flask(__name__)

# Almacenamiento en memoria para demostración
users = {}
webhook_events = []


@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint de estado para verificar que la API funciona.
    """
    return jsonify({
        'status': 'ok',
        'service': 'github-webhook-demo',
        'version': '1.0',
        'message': 'API is running and accessible!'
    }), 200


@app.route('/info', methods=['GET'])
def info():
    """
    Devuelve información sobre la petición entrante.
    Útil para depurar el reenvío de ngrok.
    """
    return jsonify({
        'your_ip': request.remote_addr,
        'your_user_agent': request.headers.get('User-Agent'),
        'host': request.host,
        'path': request.path,
        'method': request.method,
        'headers': dict(request.headers)
    }), 200


@app.route('/users', methods=['GET', 'POST'])
def users_endpoint():
    """
    Gestión simple de usuarios.
    """
    if request.method == 'GET':
        return jsonify(list(users.values())), 200

    # POST: Crear usuario
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    email = data.get('email')

    if not username:
        return jsonify({'error': 'username is required'}), 400

    if username in users:
        return jsonify({'error': 'User already exists'}), 409

    user = {
        'username': username,
        'email': email,
        'id': len(users) + 1
    }
    users[username] = user

    return jsonify(user), 201


# ============================================================================
# ENDPOINT DEL WEBHOOK DE GITHUB - TAREA RESUELTA
# ============================================================================

# 1. SOLUCIÓN: Definimos el método POST
@app.route('/webhooks/github', methods=['POST']) 
def github_webhook():
    """
    Recibe eventos REALES de push desde GitHub.
    """
    # 2. SOLUCIÓN: Obtener el JSON del webhook
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid payload'}), 400

    # Manejar evento "ping" de GitHub (lo envían al crear el webhook)
    if 'zen' in data and 'hook_id' in data:
        print(f"\n{'='*60}")
        print(f"📥 GitHub Webhook Ping Received!")
        print(f"   Hook ID: {data.get('hook_id')}")
        print(f"   Zen: {data.get('zen')}")
        print(f"   ✅ Webhook is configured correctly!")
        print(f"{'='*60}\n")
        return jsonify({'status': 'pong'}), 200

    # 3. SOLUCIÓN: Extraer info del repositorio
    repository = data.get('repository', {})
    repo_name = repository.get('full_name', 'unknown') if repository else 'unknown'

    # 4. SOLUCIÓN: Extraer info de quién hizo el push
    pusher = data.get('pusher', {})
    pusher_name = pusher.get('name', 'unknown') if pusher else 'unknown'

    # 5. SOLUCIÓN: Extraer lista de commits
    commits = data.get('commits', [])

    # 6. SOLUCIÓN: Extraer la rama (ref)
    ref = data.get('ref', 'unknown')

    # Log detallado en consola
    print(f"\n{'='*60}")
    print(f"🎉 REAL GitHub Webhook Received!")
    print(f"📦 Repository: {repo_name}")
    print(f"👤 Pushed by: {pusher_name}")
    print(f"🌿 Branch: {ref}")
    print(f"📝 Commits: {len(commits)}")

    # Mostrar detalles de cada commit
    for i, commit in enumerate(commits, 1):
        commit_msg = commit.get('message', 'No message')
        commit_id = commit.get('id', 'unknown')[:7]  # Short SHA
        author = commit.get('author', {}).get('name', 'unknown')
        print(f"   {i}. [{commit_id}] {commit_msg} (by {author})")

    print(f"{'='*60}\n")

    # Guardar evento en memoria para verlo en /webhooks/events
    webhook_event = {
        'type': 'github_push',
        'repository': repo_name,
        'pusher': pusher_name,
        'ref': ref,
        'commits_count': len(commits),
        'commit_messages': [c.get('message', '') for c in commits]
    }
    webhook_events.append(webhook_event)

    # 7. SOLUCIÓN: Devolver 200 OK
    return jsonify({'status': 'received', 'commits_processed': len(commits)}), 200


# ============================================================================
# MONITORIZACIÓN Y DEBUG
# ============================================================================

@app.route('/webhooks/events', methods=['GET'])
def list_webhook_events():
    """
    Devuelve todos los eventos recibidos.
    """
    return jsonify({
        'total_events': len(webhook_events),
        'events': webhook_events
    }), 200


@app.route('/webhooks/events/clear', methods=['POST'])
def clear_webhook_events():
    """
    Limpia el historial de eventos.
    """
    global webhook_events
    count = len(webhook_events)
    webhook_events = []
    return jsonify({
        'message': f'Cleared {count} webhook events',
        'remaining': 0
    }), 200


# ============================================================================
# LOG DE PETICIONES (DEBUG)
# ============================================================================

@app.before_request
def log_request():
    """
    Registra todas las peticiones entrantes para ver el tráfico de ngrok.
    """
    if request.path in ['/favicon.ico']:
        return

    print(f"\n{'='*60}")
    print(f"📨 Incoming Request:")
    print(f"   Method: {request.method}")
    print(f"   Path: {request.path}")
    print(f"   From: {request.remote_addr}")
    print(f"   User-Agent: {request.headers.get('User-Agent', 'Unknown')[:50]}")

    if request.method in ['POST', 'PUT', 'PATCH']:
        body = request.get_json(silent=True)
        if body:
            print(f"   Body: {body}")

    print(f"{'='*60}\n")


# ============================================================================
# MANEJO DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': f'The endpoint {request.path} does not exist',
        'tip': 'Try /health to verify the API is running'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method Not Allowed',
        'message': f'{request.method} is not allowed for {request.path}'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Something went wrong on the server'
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌐 GitHub Webhook Demo - ngrok Exercise")
    print("="*70)
    print("Running on: http://127.0.0.1:5000")
    print("\nQuick Start:")
    print("1. In another terminal, run: ngrok http 5000")
    print("2. Copy the https://....ngrok-free.app URL")
    print("3. Configure GitHub webhook with that URL + /webhooks/github")
    print("4. Make a commit to trigger the webhook!")
    print("="*70 + "\n")

    app.run(debug=True, port=5000)