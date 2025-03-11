from flask import Flask, request
from flask_socketio import SocketIO, emit
import sqlite3
import base64
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Підключення до бази даних
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ініціалізація бази даних
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Словник для зберігання ніків та їх socket IDs
users = {}

@app.route('/')
def index():
    return "Chat Server is running!"

@socketio.on('connect')
def handle_connect():
    print("A user connected")

@socketio.on('disconnect')
def handle_disconnect():
    for nickname, sid in list(users.items()):
        if sid == request.sid:
            del users[nickname]
            emit('user_disconnected', nickname, broadcast=True)
            emit('user_list', list(users.keys()), broadcast=True)  # Оновлення списку користувачів
            break

@socketio.on('register')
def handle_register(data):
    username = data.get('username')
    password = data.get('password')
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        emit('registration_success', {'message': 'Registration successful!'})
    except sqlite3.IntegrityError:
        emit('registration_error', {'message': 'Username already exists!'})
    finally:
        conn.close()

@socketio.on('login')
def handle_login(data):
    username = data.get('username')
    password = data.get('password')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    if user:
        users[username] = request.sid
        emit('login_success', {'message': 'Login successful!', 'username': username})
        emit('user_connected', username, broadcast=True)
        emit('user_list', list(users.keys()), broadcast=True)
    else:
        emit('login_error', {'message': 'Invalid username or password!'})

@socketio.on('send_message')
def handle_send_message(data):
    print(f"Received message: {data}")  # Логування
    recipient = data.get('recipient')
    message = data.get('message')
    sender = [nick for nick, sid in users.items() if sid == request.sid][0]

    if recipient == "all":  # Групове повідомлення
        print(f"Broadcasting message to all: {message}")  # Логування
        emit('receive_message', {'sender': sender, 'message': message}, broadcast=True)
    else:  # Приватне повідомлення
        recipient_sid = users.get(recipient)
        if recipient_sid:
            print(f"Sending private message to {recipient}: {message}")  # Логування
            emit('receive_message', {'sender': sender, 'message': message}, room=recipient_sid)
            emit('receive_message', {'sender': sender, 'message': message}, room=request.sid)  # Відправка собі

@socketio.on('send_file')
def handle_send_file(data):
    print(f"Received file: {data}")  # Логування
    recipient = data.get('recipient')
    file_name = data.get('file_name')
    file_data = data.get('file_data')
    sender = [nick for nick, sid in users.items() if sid == request.sid][0]

    # Збереження файлу на сервері
    file_path = os.path.join('uploads', file_name)
    with open(file_path, "wb") as file:
        file.write(base64.b64decode(file_data))

    if recipient == "all":  # Групове повідомлення
        print(f"Broadcasting file to all: {file_name}")  # Логування
        emit('receive_file', {'sender': sender, 'file_name': file_name, 'file_data': file_data}, broadcast=True)
    else:  # Приватне повідомлення
        recipient_sid = users.get(recipient)
        if recipient_sid:
            print(f"Sending private file to {recipient}: {file_name}")  # Логування
            emit('receive_file', {'sender': sender, 'file_name': file_name, 'file_data': file_data}, room=recipient_sid)
            emit('receive_file', {'sender': sender, 'file_name': file_name, 'file_data': file_data}, room=request.sid)  # Відправка собі

@socketio.on('get_users')
def handle_get_users():
    emit('user_list', list(users.keys()))

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
