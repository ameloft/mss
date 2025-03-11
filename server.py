from flask import Flask, request
from flask_socketio import SocketIO, emit
import base64
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Словник для зберігання ніків та їх socket IDs
users = {}

# Папка для зберігання файлів
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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

@socketio.on('set_nickname')
def handle_set_nickname(nickname):
    users[nickname] = request.sid
    emit('user_connected', nickname, broadcast=True)
    emit('user_list', list(users.keys()), broadcast=True)  # Оновлення списку користувачів
    print(f"User {nickname} joined the chat")

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
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
