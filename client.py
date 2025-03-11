import logging
import tkinter as tk
from tkinter import ttk, filedialog
import socketio
import base64

# Логування для відладки
logging.basicConfig(level=logging.DEBUG)

# Підключення до сервера
sio = socketio.Client(logger=True, engineio_logger=True)

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Messenger")
        self.nickname = None

        # Вибір ніка
        self.nickname_frame = ttk.Frame(root)
        self.nickname_frame.pack(pady=10)

        ttk.Label(self.nickname_frame, text="Enter your nickname:").pack(side=tk.LEFT)
        self.nickname_entry = ttk.Entry(self.nickname_frame)
        self.nickname_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.nickname_frame, text="Join", command=self.set_nickname).pack(side=tk.LEFT)

        # Чат
        self.chat_frame = ttk.Frame(root)
        self.chat_frame.pack(pady=10)

        self.chat_area = tk.Text(self.chat_frame, state='disabled', height=20, width=50)
        self.chat_area.pack()

        # Введення повідомлення
        self.message_frame = ttk.Frame(root)
        self.message_frame.pack(pady=10)

        self.message_entry = ttk.Entry(self.message_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.message_frame, text="Send", command=self.send_message).pack(side=tk.LEFT)

        # Вибір одержувача
        self.recipient_frame = ttk.Frame(root)
        self.recipient_frame.pack(pady=10)

        ttk.Label(self.recipient_frame, text="To:").pack(side=tk.LEFT)
        self.recipient_var = tk.StringVar(value="all")
        self.recipient_dropdown = ttk.Combobox(self.recipient_frame, textvariable=self.recipient_var, state="readonly")
        self.recipient_dropdown.pack(side=tk.LEFT, padx=5)

        # Кнопка для вибору файлу
        self.file_frame = ttk.Frame(root)
        self.file_frame.pack(pady=10)

        ttk.Button(self.file_frame, text="Send File", command=self.send_file).pack(side=tk.LEFT)

        # Обробка подій Socket.IO
        sio.on('user_connected', self.handle_user_connected)
        sio.on('user_disconnected', self.handle_user_disconnected)
        sio.on('receive_message', self.handle_receive_message)
        sio.on('user_list', self.handle_user_list)
        sio.on('receive_file', self.handle_receive_file)  # Обробник для отримання файлу

    def set_nickname(self):
        self.nickname = self.nickname_entry.get()
        if self.nickname:
            print(f"Setting nickname: {self.nickname}")  # Логування
            sio.emit('set_nickname', self.nickname)
            self.nickname_frame.pack_forget()
            self.chat_frame.pack()
            self.message_frame.pack()
            self.recipient_frame.pack()
            self.file_frame.pack()

    def send_message(self):
        message = self.message_entry.get()
        recipient = self.recipient_var.get()
        if message:
            print(f"Sending message: {message} to {recipient}")  # Логування
            sio.emit('send_message', {'recipient': recipient, 'message': message})
            self.message_entry.delete(0, tk.END)

    def send_file(self):
        file_path = filedialog.askopenfilename()  # Вибір файлу
        if file_path:
            with open(file_path, "rb") as file:
                file_data = file.read()
                file_name = file_path.split("/")[-1]  # Отримання імені файлу
                file_base64 = base64.b64encode(file_data).decode('utf-8')  # Кодування файлу в base64
                recipient = self.recipient_var.get()
                sio.emit('send_file', {'recipient': recipient, 'file_name': file_name, 'file_data': file_base64})

    def handle_user_connected(self, nickname):
        print(f"User connected: {nickname}")  # Логування
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{nickname} joined the chat.\n")
        self.chat_area.config(state='disabled')
        sio.emit('get_users')  # Запит на оновлення списку користувачів

    def handle_user_disconnected(self, nickname):
        print(f"User disconnected: {nickname}")  # Логування
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{nickname} left the chat.\n")
        self.chat_area.config(state='disabled')
        sio.emit('get_users')  # Запит на оновлення списку користувачів

    def handle_receive_message(self, data):
        print(f"Received message: {data}")  # Логування
        sender = data['sender']
        message = data['message']
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        self.chat_area.config(state='disabled')

    def handle_receive_file(self, data):
        print(f"Received file: {data}")  # Логування
        sender = data['sender']
        file_name = data['file_name']
        file_data = data['file_data']
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{sender} sent a file: {file_name}\n")
        self.chat_area.config(state='disabled')

        # Збереження файлу
        with open(file_name, "wb") as file:
            file.write(base64.b64decode(file_data))

    def handle_user_list(self, users):
        print(f"Received user list: {users}")  # Логування
        self.recipient_dropdown['values'] = ["all"] + users

# Обробка подій підключення та відключення
@sio.event
def connect():
    print("Connected to server")

@sio.event
def disconnect():
    print("Disconnected from server")

# Запуск клієнта
if __name__ == '__main__':
    sio.connect('http://192.168.1.6:5000')  # Замініть на IP-адресу сервера
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
