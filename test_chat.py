import socket
import threading
import time
import unittest

HOST = '127.0.0.1'
PORT = 5555

# Crea y conecta un cliente de prueba
def create_client(name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(name.encode('utf-8'))
    time.sleep(0.1)
    return s

# Envía un mensaje y espera a que el servidor lo procese
def send_message(s, message):
    s.send(message.encode('utf-8'))
    time.sleep(0.2)

# Recibe todo lo disponible en el socket hasta que no haya más datos
def receive_all(s, timeout=0.5):
    s.settimeout(timeout)
    data = b''
    try:
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    return data.decode('utf-8')

class TestConcurrentChat(unittest.TestCase):

    # Prueba de concurrencia: 5 clientes se conectan al mismo tiempo usando threads
    # Verifica que el servidor maneja múltiples conexiones simultáneas sin bloquear ninguna
    def test_1_multiple_clients_connect_simultaneously(self):
        clients = []
        errors = []

        # Función que cada thread ejecuta para conectarse
        def connect(name):
            try:
                s = create_client(name)
                clients.append(s)
            except Exception as e:
                errors.append(e)

        # Lanza 5 threads que se conectan al mismo tiempo
        threads = [threading.Thread(target=connect, args=(f"Cliente{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Todos deben haberse conectado sin error
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(clients), 5)

        for s in clients:
            s.close()

    # Prueba de threads: verifica que el servidor atiende múltiples clientes al mismo tiempo
    # Solo es posible si hay un thread por cliente, si fuera secuencial el segundo esperaría al primero
    def test_2_thread_created_per_client(self):
        results = []

        # Cada cliente manda un mensaje y verifica que el otro lo recibió
        def client_task(name, target):
            s = create_client(name)
            other = create_client(target)
            receive_all(other)
            send_message(s, f"hola de {name}")
            received = receive_all(other)
            results.append(f"hola de {name}" in received)
            s.close()
            other.close()

        # Dos pares de clientes se comunican al mismo tiempo
        t1 = threading.Thread(target=client_task, args=("ClienteA", "ReceptorA"))
        t2 = threading.Thread(target=client_task, args=("ClienteB", "ReceptorB"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Ambas comunicaciones deben haber funcionado simultáneamente
        self.assertEqual(len(results), 2)
        self.assertTrue(all(results))

    # Prueba de broadcast: un mensaje debe llegar a todos los clientes conectados
    # El servidor itera sobre todos los threads activos para reenviar el mensaje
    def test_3_broadcast_reaches_all_clients(self):
        a = create_client("A")
        b = create_client("B")
        c = create_client("C")
        receive_all(b)
        receive_all(c)
        send_message(a, "mensaje para todos")
        self.assertIn("mensaje para todos", receive_all(b))
        self.assertIn("mensaje para todos", receive_all(c))
        a.close()
        b.close()
        c.close()

    # Prueba del mutex: múltiples threads mandan mensajes al mismo tiempo
    # Sin el mutex dos threads podrían corromper la lista de clientes (race condition)
    # Con el mutex todos los mensajes deben llegar correctamente
    def test_4_mutex_prevents_message_loss(self):
        a = create_client("A")
        b = create_client("B")
        receive_all(a)
        receive_all(b)

        # 5 threads mandan mensajes simultáneamente para forzar concurrencia
        threads = [
            threading.Thread(target=send_message, args=(a, f"msg{i}"))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(0.5)
        received = receive_all(b)

        # B debe haber recibido los 5 mensajes sin pérdida
        for i in range(5):
            self.assertIn(f"msg{i}", received)

        a.close()
        b.close()

    # Prueba de independencia de threads: un cliente lento no bloquea a los demás
    # Cada cliente tiene su propio thread, si uno tarda los otros siguen funcionando
    def test_5_threads_run_independently(self):
        a = create_client("Rapido")
        b = create_client("Lento")
        c = create_client("Receptor")
        receive_all(c)

        send_message(a, "mensaje rapido")

        # B simula ser lento sin hacer nada por 1 segundo
        time.sleep(1)

        # C debe haber recibido el mensaje de A sin importar que B esté lento
        self.assertIn("mensaje rapido", receive_all(c))
        a.close()
        b.close()
        c.close()

    # Prueba de robustez: el servidor limpia el thread de un cliente que se desconecta abruptamente
    # Los demás clientes no deben verse afectados
    def test_6_server_handles_disconnection(self):
        a = create_client("SeDesconecta")
        b = create_client("SigueConectado")
        a.close()  # Se desconecta sin avisar
        time.sleep(0.3)

        # Si el servidor sigue vivo acepta nuevas conexiones sin problema
        c = create_client("NuevoCliente")
        receive_all(b)
        send_message(c, "hola después de desconexión")
        self.assertIn("hola después de desconexión", receive_all(b))
        b.close()
        c.close()

    # Prueba de lógica del broadcast: el thread de cada cliente solo reenvía a los demás
    # El remitente nunca debe recibir su propio mensaje
    def test_7_no_echo_to_sender(self):
        a = create_client("Remitente")
        b = create_client("Receptor")
        receive_all(a)
        receive_all(b)
        send_message(a, "solo para otros")
        self.assertNotIn("solo para otros", receive_all(a))
        self.assertIn("solo para otros", receive_all(b))
        a.close()
        b.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)