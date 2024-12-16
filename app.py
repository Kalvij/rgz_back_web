from flask import Flask, request, jsonify, render_template, session
import json
from storage_room import get_rooms, book_room, release_room
from registration import register, login, logout

import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Секретно-секретный секрет')
app.config['DB_TYPE'] = os.getenv('DB_TYPE', 'postgres')

from registration import registr
from storage_room import rooms

app.register_blueprint(registr)
app.register_blueprint(rooms)

@app.route("/")
def menu():
    return render_template('registration/menu.html', login=session.get('login'))

# Обработчик JSON-RPC запросов
@app.route('/api', methods=['POST'])
def json_rpc_handler():
    
    data = request.get_json()

    # Проверяем, что запрос содержит обязательные поля
    if not all(key in data for key in ('jsonrpc', 'method', 'id')):
        return jsonify({'jsonrpc': '2.0', 'error': {'code': -32600, 'message': 'Invalid Request'}, 'id': None}), 400

    # Обрабатываем метод
    method = data['method']
    params = data.get('params', {})

    # Обработка методов JSON-RPC
    if method == 'get_rooms':
        result = get_rooms()
    elif method == 'book_room':
        room_number = params.get('room_number')
        result = book_room(room_number)
    elif method == 'release_room':
        room_number = params.get('room_number')
        result = release_room(room_number)
    elif method == 'register':
        login = params.get('login')
        password = params.get('password')
        result = register(login, password)
    elif method == 'login':
        login = params.get('login')
        password = params.get('password')
        result = login(login, password)
    elif method == 'logout':
        result = logout()
    else:
        return jsonify({'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found'}, 'id': data['id']}), 404

    # Возвращаем результат
    return jsonify({'jsonrpc': '2.0', 'result': result, 'id': data['id']})