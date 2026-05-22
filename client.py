import socket
import threading

HOST = '127.0.0.1'
PORT = 5555

# Corre en un thread separado para escuchar mensajes entrantes
# Sin este thread, el cliente estaría bloqueado esperando input y nunca recibiría mensajes
def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(message)
        except:
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # El primer dato que se manda al servidor es el nombre
    name = input("Ingresa tu nombre: ")
    client.send(name.encode('utf-8'))

    # Thread para recibir mensajes, corre en paralelo al input del usuario
    thread = threading.Thread(target=receive_messages, args=(client,))
    thread.daemon = True
    thread.start()

    print("[*] Conectado. Escribe 'salir' para desconectarte.\n")

    while True:
        message = input()
        if message.lower() == 'salir':
            client.close()
            break
        if message.strip():  # Ignora mensajes vacíos
            client.send(message.encode('utf-8'))

if __name__ == "__main__":
    start_client()