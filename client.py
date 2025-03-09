import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(message)
        except:
            print("З'єднання розірвано")
            client_socket.close()
            break

def start_client(host='192.168.1.4', port=12345):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    thread = threading.Thread(target=receive_messages, args=(client_socket,))
    thread.start()

    while True:
        message = input()
        client_socket.send(message.encode('utf-8'))

if __name__ == "__main__":
    start_client()
