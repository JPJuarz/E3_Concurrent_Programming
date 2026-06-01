import socket
import threading
import time
import unittest

HOST = '127.0.0.1'
PORT = 5555

# Todo el Setup

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

# Recibe todo lo disponible en el socket 
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

# Imprime la información de cada prueba antes de ejecutarla
def print_test_header(num, scenario, expected):
    print(f"\n{'='*60}")
    print(f"  Prueba {num}")
    print(f"  Escenario : {scenario}")
    print(f"  Se espera : {expected}")
    print(f"{'='*60}")

class TestConcurrentChat(unittest.TestCase):

    # Prueba de concurrencia: 5 clientes se conectan al mismo tiempo usando threads
    # Verifica que el servidor maneja múltiples conexiones simultáneas sin bloquear ninguna
    def test_1_multiple_clients_connect_simultaneously(self):
        print_test_header(
            1,
            "5 clientes se conectan al servidor al mismo tiempo usando threads",
            "5 conexiones exitosas y 0 errores"
        )

        clients = []
        errors = []

        # Función de cada thread para conectarse
        def connect(name):
            try:
                s = create_client(name)
                clients.append(s)
            except Exception as e:
                errors.append(e)

        # 5 threads que se conectan al mismo tiempo
        threads = [threading.Thread(target=connect, args=(f"Cliente{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print(f"  Resultado : {len(clients)} clientes conectados, {len(errors)} errores")

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(clients), 5)

        for s in clients:
            s.close()

    # Prueba de threads: verifica que el servidor atiende múltiples clientes al mismo tiempo
    # Solo es posible si hay un thread por cliente, si fuera secuencial el segundo esperaría al primero
    def test_2_thread_created_per_client(self):
        print_test_header(
            2,
            "2 pares de clientes se comunican entre sí al mismo tiempo",
            "Ambas comunicaciones funcionan simultáneamente sin bloquearse ni causar una race condition"
        )

        results = []

        # Cada cliente manda un mensaje y verifica que el otro lo recibio
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

        print(f"  Resultado : {sum(results)}/2 comunicaciones simultaneas exitosas")

        self.assertEqual(len(results), 2)
        self.assertTrue(all(results))

    # Prueba de broadcast: un mensaje debe llegar a todos los clientes qeu estan conectados
    # El servidor itera sobre todos los threads activos para reenviar el mensaje
    def test_3_broadcast_reaches_all_clients(self):
        print_test_header(
            3,
            "Cliente A manda mensaje con B y C conectados",
            "B y C reciben el mensaje de A"
        )

        a = create_client("A")
        b = create_client("B")
        c = create_client("C")
        receive_all(b)
        receive_all(c)
        send_message(a, "mensaje para todos")

        received_b = receive_all(b)
        received_c = receive_all(c)

        b_ok = "mensaje para todos" in received_b
        c_ok = "mensaje para todos" in received_c
        print(f"  Resultado : B recibió = {'Sí' if b_ok else 'No'}, C recibió = {'Sí' if c_ok else 'No'}")

        self.assertTrue(b_ok)
        self.assertTrue(c_ok)
        a.close()
        b.close()
        c.close()

    # Prueba del mutex: múltiples threads mandan mensajes al mismo tiempo
    # Sin el mutex dos threads podrían corromper la lista de clientes (race condition)
    def test_4_mutex_prevents_message_loss(self):
        print_test_header(
            4,
            "5 threads mandan mensajes al mismo tiempo para forzar una race condition",
            "Los 5 mensajes llegan sin race condition gracias al mutex"
        )

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

        count = sum(1 for i in range(5) if f"msg{i}" in received)
        print(f"  Resultado : {count}/5 mensajes recibidos correctamente")

        for i in range(5):
            self.assertIn(f"msg{i}", received)

        a.close()
        b.close()

    # Prueba de independencia de cada thread: un cliente lento no bloquea a los demás
    # Cada cliente tiene su propio thread, si uno tarda los otros siguen funcionando
    def test_5_threads_run_independently(self):
        print_test_header(
            5,
            "Cliente lento (B) conectado mientras A y C se comunican normalmente",
            "C recibe el mensaje de A aunque B no haga nada o sea más lento"
        )

        a = create_client("Rapido")
        b = create_client("Lento")
        c = create_client("Receptor")
        receive_all(c)

        send_message(a, "mensaje rapido")
        time.sleep(1)  # B simula ser lento

        received = receive_all(c)
        ok = "mensaje rapido" in received
        print(f"  Resultado : C recibió el mensaje={'Sí' if ok else 'No'} a pesar del cliente lento")

        self.assertTrue(ok)
        a.close()
        b.close()
        c.close()

    # Prueba de desconexión: el servidor limpia el thread de un cliente que se desconecta 
    # Los demás clientes no deben de ser afecctados
    def test_6_server_handles_disconnection(self):
        print_test_header(
            6,
            "Un cliente se desconecta abruptamente",
            "El servidor sigue funcionando y los demás no son afectados"
        )

        a = create_client("SeDesconecta")
        b = create_client("SigueConectado")
        a.close()
        time.sleep(0.3)

        c = create_client("NuevoCliente")
        receive_all(b)
        send_message(c, "hola después de desconexión")
        received = receive_all(b)
        ok = "hola después de desconexión" in received
        print(f"  Resultado : Servidor siguió activo={'Sí' if ok else 'No'}, mensaje entregado={'Sí' if ok else 'No'}")

        self.assertTrue(ok)
        b.close()
        c.close()

    # Prueba de lógica del broadcast: el thread de cada cliente solo reenvía a los demás
    # El remitente (el que mando el mensaje) nunca debe recibir su propio mensaje
    def test_7_no_echo_to_sender(self):
        print_test_header(
            7,
            "Cliente A manda mensaje y no le llega a él",
            "A no recibe su propio mensaje, B sí lo recibe"
        )

        a = create_client("Remitente")
        b = create_client("Receptor")
        receive_all(a)
        receive_all(b)
        send_message(a, "solo para otros")

        received_a = receive_all(a)
        received_b = receive_all(b)
        a_no_echo = "solo para otros" not in received_a
        b_received = "solo para otros" in received_b
        print(f"  Resultado : A no recibió su mensaje={'Sí' if a_no_echo else 'No'}, B sí recibió={'Sí' if b_received else 'No'}")

        self.assertTrue(a_no_echo)
        self.assertTrue(b_received)
        a.close()
        b.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)