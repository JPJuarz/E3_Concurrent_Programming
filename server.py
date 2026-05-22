import socket
import threading

HOST = '127.0.0.1'  # Dirección local 
PORT = 5555 # Puerto donde escucha el servidor

# Lista compartida de clientes conectados: cada elemento es (socket, nombre)
clients = []

# Mutex que protege el acceso a la lista de clientes
# Evita las race conditions cuando dos threads intentan modificarla al mismo tiempo
clients_mutex = threading.Lock()

# Envía un mensaje a todos los clientes excepto al remitente.
def broadcast(message, sender_socket):
    # Adquiere el mutex antes de iterar la lista 
    with clients_mutex:
        for client, name in clients:
            if client != sender_socket:  # No reenvia al que mando el mensaje
                try:
                    client.send(message)
                except:
                    # Si falla el envío, se cierra
                    client.close()

# Función que corre en su propio thread para cada cliente conectado.
def handle_client(client_socket, client_address):
    try:
        # El primer mensaje que manda el cliente es su nombre
        name = client_socket.recv(1024).decode('utf-8')
        print(f"[+] {name} conectado desde {client_address}")

        # Agrega el cliente a la lista compartida de forma segura con el mutex
        with clients_mutex:
            clients.append((client_socket, name))

        # Notifica a todos 
        broadcast(f"[{name} se unió al chat]\n".encode('utf-8'), client_socket)

        # Loop principal: escucha mensajes de este cliente indefinidamente
        while True:
            message = client_socket.recv(1024)
            if not message:
                # Si el mensaje esta vacío, el cliente cerro la conexión
                break
            full_message = f"{name}: {message.decode('utf-8')}"
            print(full_message)
            # Reenvia el mensaje a todos los demás 
            broadcast(full_message.encode('utf-8'), client_socket)

    except:
        # Captura cualquier error de conexión 
        pass

    finally:
        # Bloque que siempre se ejecuta, haya error o no, que elimina al cliente de la lista compartida de forma segura
        with clients_mutex:
            clients[:] = [(c, n) for c, n in clients if c != client_socket]
        # Notifica a los demás que este cliente salió
        broadcast(f"[{name} salió del chat]\n".encode('utf-8'), client_socket)
        client_socket.close()
        print(f"[-] {name} desconectado")

# Inicia el servidor y acepta conexiones entrantes.
def start_server():
    # Crea el socket del servidor usando TCP (SOCK_STREAM)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permite reutilizar el puerto después de cerrar el servidor
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[*] Servidor escuchando en {HOST}:{PORT}")

    # Loop infinito esperando nuevas conexiones
    while True:
        # accept() bloquea hasta que llega un cliente
        client_socket, client_address = server.accept()

        # Crea un thread dedicado para el cliente lo que permite atender al siguiente cliente sin esperar a que este termine
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.daemon = True  # El thread termina automáticamente si el servidor cierra
        thread.start()
        print(f"[*] Threads activos: {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()