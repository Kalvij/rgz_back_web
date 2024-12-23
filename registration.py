from flask import Blueprint, render_template, redirect, request, session, current_app
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from os import path
import re

registr = Blueprint('registr', __name__)


VALID_INPUT_PATTERN = re.compile(r'^[A-Za-z0-9@#$%^&+=_-]+$')

def is_valid_input(input_str):
    return bool(VALID_INPUT_PATTERN.match(input_str))

def db_connect():

    
    if current_app.config['DB_TYPE'] == 'postgres':
        
        conn = psycopg2.connect(
            host = '127.0.0.1',
            database = 'bogdan_yroslavcev_knowledge_base',
            user = 'bogdan_yroslavcev_knowledge_base',
            password = '123'
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
    else:
        dir_path = path.dirname(path.realpath(__file__))
        db_path = path.join(dir_path, "database.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

    return conn, cur

def db_close(conn, cur):

    conn.commit()
    cur.close()
    conn.close()

@registr.route('/registration/register', methods=['GET', 'POST'])
def register():

    if 'login' in session:
        
        return redirect('/')

    if request.method == 'GET':
       
        return render_template('registration/register.html')
    
    
    login = request.form.get('login')
    password = request.form.get('password')

    
    if not (login and password):
        return render_template('registration/register.html', error='Не все поля заполнены')

    if not is_valid_input(login):
        return render_template('registration/register.html', error='Недопустимые символы в логине')
    
    if not is_valid_input(password):
        return render_template('registration/register.html', error='Недопустимые символы в пароле')

    
    conn, cur = db_connect()
    
    
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT login FROM users WHERE login=%s;", (login,))
    else:
        cur.execute("SELECT login FROM users WHERE login=?;", (login,))
        
    if cur.fetchone():
        db_close(conn, cur)
        return render_template('registration/register.html', error='Пользователь существует')

    
    password_hash = generate_password_hash(password)
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("INSERT INTO users (login, password) VALUES (%s, %s);", (login, password_hash))
    else:    
        cur.execute("INSERT INTO users (login, password) VALUES (?, ?);", (login, password_hash))
    db_close(conn, cur)

   
    return render_template('registration/success.html', login=login)

@registr.route('/registration/login', methods=['GET', 'POST'])
def login():

    if 'login' in session:
        return redirect('/')

    if request.method == 'GET':
        return render_template('registration/login.html')
    
    login = request.form.get('login')
    password = request.form.get('password')

    if not (login and password):
        return render_template('registration/login.html', error='Заполните все поля')

    if not is_valid_input(login):
        return render_template('registration/login.html', error='Недопустимые символы в логине')
    
    if not is_valid_input(password):
        return render_template('registration/login.html', error='Недопустимые символы в пароле')

    conn, cur = db_connect()
    
    if current_app.config['DB_TYPE'] == 'postgres':
        cur.execute("SELECT * FROM users WHERE login=%s;", (login,))
    else:
        cur.execute("SELECT * FROM users WHERE login=?;", (login,))
        
    user = cur.fetchone()

    if not user:
        db_close(conn, cur)
        return render_template('registration/login.html', error='Не верный логин или пароль')

    if not check_password_hash(user['password'], password):
        db_close(conn, cur)
        return render_template('registration/login.html', error='Не верный логин или пароль')

    session['login'] = login
    db_close(conn, cur)

    return render_template('registration/success_login.html', login=login)

@registr.route('/registration/logout')
def logout():

    session.pop('login', None) 
    return redirect('/')
