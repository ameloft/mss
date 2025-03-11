import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import base64
import socketio

# Логування для відладки
logging.basicConfig(level=logging.DEBUG)

# Підключення до сервера
sio = socketio.Client(logger=True, engineio_logger=True)

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 11 Messenger")
        self.nickname = None
        self.current_chat = None  # Поточний чат (нікнейм користувача)

        # Налаштування кольорів
        self.bg_color = "#F3F3F3"  # Світло-сірий фон
        self.accent_color = "#0078D7"  # Синій акцент
        self.text_color = "#333333"  # Темно-сірий текст
        self.button_color = "#0078D7"  # Синій для кнопок
        self.button_hover_color = "#005BB5"  # Темніший синій при наведенні

        # Налаштування шрифтів
        self.font = ("Segoe UI", 10)
        self.title_font = ("Segoe UI", 12, "bold")

        # Вікно реєстрації/входу
        self.auth_frame = ttk.Frame(root, style="Auth.TFrame")
        self.auth_frame.pack(pady=50)

        ttk.Label(self.auth_frame, text="Username:", style="Auth.TLabel").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.auth_frame, style="Auth.TEntry")
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.auth_frame, text="Password:", style="Auth.TLabel").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.auth_frame, show="*", style="Auth.TEntry")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.auth_frame, text="Register", command=self.register, style="Auth.TButton").grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(self.auth_frame, text="Login", command=self.login, style="Auth.TButton").grid(row=2, column=1, padx=5, pady=5)

        # Основний інтерфейс (прихований спочатку)
        self.main_frame = ttk.Frame(root, style="Main.TFrame")

        # Ліва панель (список чатів)
        self.left_panel = ttk.Frame(self.main_frame, width=200, style="Left.TFrame")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)

        # Список чатів
        self.chat_list = tk.Listbox(self.left_panel, bg="white", fg=self.text_color, font=self.font, borderwidth=0, highlightthickness=0)
        self.chat_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_list.bind('<<ListboxSelect>>', self.select_chat)

        # Права панель (вікно чату)
        self.right_panel = ttk.Frame(self.main_frame, style="Right.TFrame")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Canvas для прокрутки повідомлень
        self.canvas = tk.Canvas(self.right_panel, bg="white", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar для Canvas
        self.scrollbar = ttk.Scrollbar(self.right_panel, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Налаштування Canvas для прокрутки
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Frame для повідомлень всередині Canvas
        self.messages_frame = ttk.Frame(self.canvas, style="Messages.TFrame")
        self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")

        # Панель введення повідомлень
        self.input_frame = ttk.Frame(self.right_panel, style="Input.TFrame")
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.message_entry = ttk.Entry(self.input_frame, style="Input.TEntry")
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.send_message, style="Send.TButton")
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.file_button = ttk.Button(self.input_frame, text="📎", command=self.send_file, style="File.TButton")
        self.file_button.pack(side=tk.LEFT, padx=5)

        # Налаштування стилів
        self.setup_styles()

        # Обробка подій Socket.IO
        sio.on('registration_success', self.handle_registration_success)
        sio.on('registration_error', self.handle_registration_error)
        sio.on('login_success', self.handle_login_success)
        sio.on('login_error', self.handle_login_error)
        sio.on('user_connected', self.handle_user_connected)
        sio.on('user_disconnected', self.handle_user_disconnected)
        sio.on('receive_message', self.handle_receive_message)
        sio.on('user_list', self.handle_user_list)
        sio.on('receive_file', self.handle_receive_file)

    def setup_styles(self):
        style = ttk.Style()

        # Стилі для рамок
        style.configure("Auth.TFrame", background=self.bg_color)
        style.configure("Main.TFrame", background=self.bg_color)
        style.configure("Left.TFrame", background="white", borderwidth=1, relief="solid")
        style.configure("Right.TFrame", background="white", borderwidth=1, relief="solid")
        style.configure("Messages.TFrame", background="white")
        style.configure("Input.TFrame", background=self.bg_color, borderwidth=1, relief="solid")

        # Стилі для текстових полів
        style.configure("Auth.TEntry", font=self.font, padding=5, relief="flat", background="white")
        style.configure("Input.TEntry", font=self.font, padding=5, relief="flat", background="white")

        # Стилі для кнопок
        style.configure("Auth.TButton", font=self.font, padding=5, background=self.button_color, foreground="white", borderwidth=0, focusthickness=0, focuscolor="none")
        style.map("Auth.TButton", background=[("active", self.button_hover_color)])

        style.configure("Send.TButton", font=self.font, padding=5, background=self.button_color, foreground="white", borderwidth=0, focusthickness=0, focuscolor="none")
        style.map("Send.TButton", background=[("active", self.button_hover_color)])

        style.configure("File.TButton", font=self.font, padding=5, background=self.button_color, foreground="white", borderwidth=0, focusthickness=0, focuscolor="none")
        style.map("File.TButton", background=[("active", self.button_hover_color)])

        # Стилі для текстів
        style.configure("Auth.TLabel", font=self.font, background=self.bg_color, foreground=self.text_color)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            sio.emit('register', {'username': username, 'password': password})

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            sio.emit('login', {'username': username, 'password': password})

    def handle_registration_success(self, data):
        messagebox.showinfo("Success", data['message'])

    def handle_registration_error(self, data):
        messagebox.showerror("Error", data['message'])

    def handle_login_success(self, data):
        self.nickname = data['username']
        self.auth_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        sio.emit('get_users')

    def handle_login_error(self, data):
        messagebox.showerror("Error", data['message'])

    def select_chat(self, event):
        selected = self.chat_list.curselection()
        if selected:
            self.current_chat = self.chat_list.get(selected[0])
            self.messages_frame.destroy()
            self.messages_frame = ttk.Frame(self.canvas, style="Messages.TFrame")
            self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")

    def send_message(self):
        message = self.message_entry.get()
        if message and self.current_chat:
            sio.emit('send_message', {'recipient': self.current_chat, 'message': message})
            self.add_message(f"You: {message}", "right")
            self.message_entry.delete(0, tk.END)

    def send_file(self):
        file_path = filedialog.askopenfilename()  # Вибір файлу
        if file_path and self.current_chat:
            with open(file_path, "rb") as file:
                file_data = file.read()
                file_name = file_path.split("/")[-1]  # Отримання імені файлу
                file_base64 = base64.b64encode(file_data).decode('utf-8')  # Кодування файлу в base64
                sio.emit('send_file', {'recipient': self.current_chat, 'file_name': file_name, 'file_data': file_base64})
                self.add_message(f"You sent a file: {file_name}", "right")

    def handle_user_connected(self, nickname):
        self.add_message(f"{nickname} joined the chat.", "left")
        self.chat_list.insert(tk.END, nickname)

    def handle_user_disconnected(self, nickname):
        self.add_message(f"{nickname} left the chat.", "left")
        self.chat_list.delete(self.chat_list.get(0, tk.END).index(nickname))

    def handle_receive_message(self, data):
        sender = data['sender']
        message = data['message']
        if sender == self.current_chat:
            self.add_message(f"{sender}: {message}", "left")

    def handle_receive_file(self, data):
        sender = data['sender']
        file_name = data['file_name']
        file_data = data['file_data']
        if sender == self.current_chat:
            self.add_message(f"{sender} sent a file: {file_name}", "left")

            # Збереження файлу
            try:
                with open(file_name, "wb") as file:
                    file.write(base64.b64decode(file_data))
            except Exception as e:
                print(f"Error saving file: {e}")

            # Відображення зображення або PDF
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.display_image(file_name, sender)
            elif file_name.lower().endswith('.pdf'):
                self.display_pdf(file_name)

    def add_message(self, message, align):
        message_frame = ttk.Frame(self.messages_frame, style="Message.TFrame")
        message_frame.pack(fill=tk.X, pady=2, anchor="e" if align == "right" else "w")

        message_label = ttk.Label(message_frame, text=message, wraplength=400, style="Message.TLabel")
        message_label.pack(side=tk.LEFT, padx=5)

    def display_image(self, file_name, sender):
        try:
            image = Image.open(file_name)
            image.thumbnail((200, 200))  # Зменшення розміру зображення
            photo = ImageTk.PhotoImage(image)

            # Створення нового Frame для зображення
            image_frame = ttk.Frame(self.messages_frame, style="Message.TFrame")
            image_frame.pack(fill=tk.X, pady=2, anchor="w")

            # Додавання Label з зображенням
            image_label = ttk.Label(image_frame, image=photo, style="Message.TLabel")
            image_label.image = photo  # Збереження посилання на зображення
            image_label.pack(side=tk.LEFT, padx=5)

            # Додавання тексту (ім'я відправника)
            sender_label = ttk.Label(image_frame, text=f"Image from {sender}", style="Message.TLabel")
            sender_label.pack(side=tk.LEFT, padx=5)
        except Exception as e:
            print(f"Error displaying image: {e}")

    def display_pdf(self, file_name):
        try:
            with open(file_name, "rb") as file:
                reader = PyPDF2.PdfFileReader(file)
                page = reader.getPage(0)
                text = page.extract_text()
                self.add_message(f"PDF content:\n{text}", "left")
        except Exception as e:
            print(f"Error displaying PDF: {e}")

    def handle_user_list(self, users):
        self.chat_list.delete(0, tk.END)
        for user in users:
            if user != self.nickname:
                self.chat_list.insert(tk.END, user)

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
