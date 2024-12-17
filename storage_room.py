from flask import Blueprint, render_template, session, current_app, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from os import path
import sqlite3

rooms = Blueprint('rooms', __name__)

# Функция для подключения к базе данных
def db_connect():
    if current_app.config['DB_TYPE'] == 'postgres':
        conn = psycopg2.connect(
            host='127.0.0.1',
            database='bogdan_yroslavcev_knowledge_base',
            user='bogdan_yroslavcev_knowledge_base',
            password='123'
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
    else:
        dir_path = path.dirname(path.realpath(__file__))
        db_path = path.join(dir_path, "database.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
    return conn, cur

# Функция для закрытия соединения с базой данных
def db_close(conn, cur):
    conn.commit()
    cur.close()
    conn.close()

# Маршрут для отображения страницы с комнатами
@rooms.route('/storage_room/')
def lab():
    return render_template('storage_room/room.html')

# Функция для получения списка комнат
def get_rooms():
    login = session.get('login')
    conn, cur = db_connect()

    # Получаем все комнаты
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT * FROM rooms")
    else:
        cur.execute("SELECT * FROM rooms")

    rooms = [dict(row) for row in cur.fetchall()]

    # Считаем количество свободных и занятых комнат
    total_rooms = len(rooms)
    occupied_rooms = sum(1 for room in rooms if room['tenant'])
    free_rooms = total_rooms - occupied_rooms

    # Если пользователь не авторизован, скрываем информацию о владельцах
    if not login:
        for room in rooms:
            if room['tenant']:
                room['tenant'] = 'Зарезервирована'

    db_close(conn, cur)
    return {'rooms': rooms, 'free': free_rooms, 'occupied': occupied_rooms}

# Функция для бронирования комнаты
def book_room(room_number):
    login = session.get('login')
    if not login:
        return {'error': 'Пожалуйста, авторизуйтесь'}

    conn, cur = db_connect()

    # Проверяем, сколько комнат уже забронировано текущим пользователем
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT COUNT(*) as count FROM rooms WHERE tenant = %s", (login,))
    else:
        cur.execute("SELECT COUNT(*) as count FROM rooms WHERE tenant = ?", (login,))

    count = cur.fetchone()['count']
    if count >= 5:
        db_close(conn, cur)
        return {'error': 'Вы не можете забронировать больше 5 ячеек'}

    # Проверяем, свободна ли комната
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT tenant FROM rooms WHERE number = %s", (room_number,))
    else:
        cur.execute("SELECT tenant FROM rooms WHERE number = ?", (room_number,))

    room = cur.fetchone()
    if room and room['tenant']:
        db_close(conn, cur)
        return {'error': 'Комната уже забронирована'}

    # Бронируем комнату
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("UPDATE rooms SET tenant = %s WHERE number = %s", (login, room_number))
    else:
        cur.execute("UPDATE rooms SET tenant = ? WHERE number = ?", (login, room_number))

    db_close(conn, cur)
    return {'result': 'Успешно забронировано'}

# Функция для отмены бронирования комнаты
def cancel_room(room_number):
    login = session.get('login')
    if not login:
        return {'error': 'Пожалуйста, авторизуйтесь'}

    conn, cur = db_connect()

    # Проверяем, принадлежит ли комната текущему пользователю
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT tenant FROM rooms WHERE number = %s", (room_number,))
    else:
        cur.execute("SELECT tenant FROM rooms WHERE number = ?", (room_number,))

    room = cur.fetchone()
    if room and room['tenant'] != login:
        db_close(conn, cur)
        return {'error': 'Вы не можете снять чужую бронь'}

    # Отменяем бронь
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("UPDATE rooms SET tenant = NULL WHERE number = %s", (room_number,))
    else:
        cur.execute("UPDATE rooms SET tenant = NULL WHERE number = ?", (room_number,))

    db_close(conn, cur)
    return {'result': 'Бронирование отменено'}

# Функция для освобождения комнаты
def release_room(room_number):
    login = session.get('login')
    if not login:
        return {'error': 'Пожалуйста, авторизуйтесь'}

    conn, cur = db_connect()

    # Проверяем, принадлежит ли комната текущему пользователю
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT tenant FROM rooms WHERE number = %s", (room_number,))
    else:
        cur.execute("SELECT tenant FROM rooms WHERE number = ?", (room_number,))

    room = cur.fetchone()
    if room and room['tenant'] != login:
        db_close(conn, cur)
        return {'error': 'Вы не можете снять чужую бронь'}

    # Освобождаем комнату
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("UPDATE rooms SET tenant = NULL WHERE number = %s", (room_number,))
    else:
        cur.execute("UPDATE rooms SET tenant = NULL WHERE number = ?", (room_number,))

    db_close(conn, cur)
    return {'result': 'Комната освобождена'}