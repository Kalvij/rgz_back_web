from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
from storage_room import get_rooms, book_room, release_room
from registration import register, login, logout

app = Flask(__name__)

# Настройка секретного ключа и базы данных
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Секретно-секретный секрет')
app.config['DB_TYPE'] = os.getenv('DB_TYPE', 'postgres')

# Регистрация Blueprints
from registration import registr
from storage_room import rooms

app.register_blueprint(registr)
app.register_blueprint(rooms)

# Главная страница
@app.route("/")
def menu():
    return render_template('registration/menu.html', login=session.get('login'))

# Обработчик JSON-RPC запросов
@app.route('/json-rpc-api', methods=['POST'])
def json_rpc_handler():
    try:
        # Получаем данные из запроса
        data = request.get_json()

        # Проверяем, что запрос содержит обязательные поля
        if not all(key in data for key in ('jsonrpc', 'method', 'id')):
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32600, 'message': 'Invalid Request'},
                'id': None
            }), 400

        # Обрабатываем метод
        method = data['method']
        params = data.get('params', {})
        id = data['id']

        # Обработка методов JSON-RPC
        if method == 'get_rooms':
            result = get_rooms()
        elif method == 'book_room':
            room_number = params.get('room_number')
            if not room_number:
                return jsonify({
                    'jsonrpc': '2.0',
                    'error': {'code': -32602, 'message': 'Invalid params: room_number is required'},
                    'id': id
                }), 400
            result = book_room(room_number)
        elif method == 'release_room':
            room_number = params.get('room_number')
            if not room_number:
                return jsonify({
                    'jsonrpc': '2.0',
                    'error': {'code': -32602, 'message': 'Invalid params: room_number is required'},
                    'id': id
                }), 400
            result = release_room(room_number)
        elif method == 'register':
            login_param = params.get('login')
            password = params.get('password')
            if not login_param or not password:
                return jsonify({
                    'jsonrpc': '2.0',
                    'error': {'code': -32602, 'message': 'Invalid params: login and password are required'},
                    'id': id
                }), 400
            result = register(login_param, password)
        elif method == 'login':
            login_param = params.get('login')
            password = params.get('password')
            if not login_param or not password:
                return jsonify({
                    'jsonrpc': '2.0',
                    'error': {'code': -32602, 'message': 'Invalid params: login and password are required'},
                    'id': id
                }), 400
            result = login(login_param, password)
        elif method == 'logout':
            result = logout()
        else:
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32601, 'message': 'Method not found'},
                'id': id
            }), 404

        # Возвращаем результат
        return jsonify({'jsonrpc': '2.0', 'result': result, 'id': id})

    except Exception as e:
        # Обработка непредвиденных ошибок
        app.logger.error(f"Ошибка: {str(e)}")
        return jsonify({
            'jsonrpc': '2.0',
            'error': {'code': -32603, 'message': 'Internal error'},
            'id': None
        }), 500