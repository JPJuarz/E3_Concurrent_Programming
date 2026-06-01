# E3_Concurrent_Programming
### Juan Pablo Juárez Ortiz - A01708685

## Evidencia 3: Demostración de Paradigma Concurrente | Servidor de Chat

--- 

## Descripción
El problema a resolver para esta evidencia es el siguiente: ¿Cómo puede un servidor  atender múltiples clientes simultáneamente sin bloquear a ninguno? En un servidor secuencial tradicional, cada cliente debe esperar a que el anterior termine de ser atendido antes de recibir cualquier respuesta. Esto hace que el sistema sea mucho menos efectivo y mucho menos usable en la práctica para más de un usuario. La solución natural a este problema es el paradigma de programación concurrente, donde justamente múltiples flujos de ejecución (threads) corren de manera simultanea e intercalada compartiendo recursos del mismo proceso para lograr un trabajo mucho más eficiente y como lo dice, concurrente. (Tanenbaum, 2014)

En esta evidencia se implementa un servidor de chat local donde varios clientes pueden conectarse simultáneamente, enviar mensajes y recibirlos en tiempo real. Todos los mensajes enviados por un cliente son retransmitidos a todos los demás clientes conectados. El servidor crea un nuevo thread por cada cliente que se conecta, permitiendo atender conexiones en paralelo sin que una bloquee a las demás permitiendo que se pueda trabajar al mismo tiempo.

El problema lo escogi porque la concurrencia se me hizo un tema bastante interesante y al investigar un poco más me di cuenta que esta es la base de cualquier sistema de mensajería real, ya sea WhatsApp, Discord, Slack u otra, y porque justamente enseña directamente algunos de los problemas clásicos de la concurrencia los cuales son el acceso compartido a recursos (la lista de clientes conectados) y la necesidad de sincronización mediante locks para evitar condiciones de carrera (race conditions).

---

## Conceptos Clave
Antes de continuar, aquí hay unos conceptos importantes para entender lo que se hace en esta evidencia:
| **Concepto** | **Definición** |
|----------|---------|
| Thread       | Flujo de ejecución independiente dentro de un mismo proceso      |
| Lock / Mutex      | Mecanismo de sincronización que evita que dos threads accedan al mismo recurso simultáneamente      |
| Race Condition      | Error que ocurre cuando dos threads modifican un recurso compartido al mismo tiempo sin sincronización      |
| Broadcast      | Reenvío de un mensaje de un cliente a todos los demás conectados    |
| Socket      | Punto de comunicación entre dos procesos a través de una red (o localhost)|

---

## Modelos | Diagramas 

### Modelo 1 — Arquitectura general

El servidor principal corre en un loop infinito esperando conexiones entrantes. Cada vez que llega un cliente nuevo, se crea un thread dedicado exclusivamente a ese cliente y el loop regresa inmediatamente a esperar el siguiente. La lista de clientes conectados es un recurso compartido entre todos los threads y está potegida por un mutex para evitar race conditions.

<img width="1366" height="638" alt="image" src="https://github.com/user-attachments/assets/3a5a02c0-5f13-4e14-8d9c-bea934be4c90" />

### Modelo 2 — Flujo de un mensaje

Cuando un cliente envía un mensaje, su thread correspondiente recibe ese mensaje y adquiere el mutex de la lista de clientes conectados. Después itera sobre todos menos si mismo y reenvía el mensaje a cada cliente de la lista. Solo una vez que se termina, se libera el mutex para que otros threads puedan acceder a la lista.

<img width="665" height="759" alt="image" src="https://github.com/user-attachments/assets/5455e379-8557-4c47-a0b2-d642a8c110a0" />

### Modelo 3 — Estados de un cliente

Cada cliente pasa por cuatro diferentes estados en el tiempo que existe en el servidor. Antes que nada, espera la conexión inicial, después se conecta (donde se crea su thread y se agrega a la lista), después pasa al estado activo donde manda y recibe mensajes vía broadcast y finalmente la útlima la cuál es la desconexión donde el thread termina y el cliente se elimina de la lista.

<img width="1467" height="276" alt="image" src="https://github.com/user-attachments/assets/7bb9e4ef-141b-4f97-9422-ac599eebc415" />

---

## Funcionamiento

El paradigma concurrente se aplica de la siguiente manera en esta solución:

**Threads:** Cada cliente que se conecta recibe su propio thread dedicado (`handle_client`). Esto significa que el servidor puede atender a 10 clientes al mismo tiempo con 10 threads corriendo en paralelo, sin que ninguno espere al otro.

**Mutex:** La lista `clients` es un recurso compartido entre todos los threads. Sin protección, dos threads podrían intentar modificarla al mismo tiempo causando una race condition, por ejemplo uno agregando un cliente mientras otro lo elimina, lo que corrompería la lista. El mutex `clients_mutex` garantiza que solo un thread puede acceder a la lista a la vez.

**Broadcast:** Cuando un cliente manda un mensaje, su thread adquiere el mutex, itera sobre todos los clientes de la lista y reenvía el mensaje a cada uno. Este es el uso directo del paradigma: un thread coordinando la comunicación entre todos los demás.

**Client thread:** El cliente también usa un thread separado para recibir mensajes (`receive_messages`). Sin este thread, el cliente estaría bloqueado esperando que el usuario escriba y nunca podría recibir mensajes de otros al mismo tiempo.

---

## Implementación

La solución usa exclusivamente la biblioteca estándar de Python, sin
dependencias externas.

- `socket` — comunicación TCP (Protocolo de transmisión en lugar de UTP) entre servidor y clientes
- `threading` — creación de threads y locks para sincronización

### Archivos

| **Archivo** | **Descripción** |
|---------|-------------|
| server.py | Servidor concurrente, acepta conexiones y hace broadcast |
| client.py | Cliente que se conecta, manda y recibe mensajes |
| test_chat.py | Pruebas automatizadas |

### Requisitos

- Python 
- VScode
- Correr server.py

### Ejecución

Para la ejecución hay 2 maneras distintas de probarlo. Antes que nada se debe de abrir una terminal y correr server.py dentro de esa terminal. Después si se quiere hacer de manera automática, tienes que abrir ota terminal con Ctrl + Shift + ñ (o en el boton de + de vscode) y correr test_chat.py. Si quieres tu mandar los mensajes 1 por uno para probar que se reciben y como sale, abres las terminales necesarias y corres cliente.py. Una vez corrido mandara un mensaje de que ingreses nombre lo cual será el primer mensaje mandado y después dejara escribir libremente. Todos los mensajes y notificaciones se pueden checar en la terminal de server.py y los mensajes mandados por ejemplo de cliente A se veran también en la terminal de cliente B.

En pasos
1. Abrir terminal
2. Escribir python server.py
3. Abrir una o más terminales extra
4. Escribir python test_chat.py o client.py
5. Si se escribio client.py ingresar nombre
6. Probar

---

## Pruebas

Las pruebas están diseñadas específicamente para verificar el comportamiento concurrente del servidor, no solo su funcionalidad básica. Cada prueba corresponde a un aspecto del paradigma concurrente.

### Casos de prueba

| **Num** | **Escenario** | **Qué verifica** | **Resultado esperado** |
|---|---|---|---|
| 1 | 5 clientes se conectan simultáneamente con threads | Múltiples conexiones concurrentes | 5 conexiones exitosas, 0 errores |
| 2 | 2 pares de clientes se comunican al mismo tiempo | Un thread por cliente corriendo en paralelo | Ambas comunicaciones funcionan simultáneamente |
| 3 | A manda mensaje con B y C conectados | Broadcast llega a todos los threads | B y C reciben el mensaje de A |
| 4 | 5 threads mandan mensajes al mismo tiempo | El mutex evita race conditions | Los 5 mensajes llegan sin pérdida ni corrupción |
| 5 | Cliente lento conectado mientras otros se comunican | Independencia de threads | El mensaje llega aunque B no haga nada |
| 6 | Un cliente se desconecta de la nada | El servidor limpia el thread correctamente | El servidor sigue aceptando conexiones |
| 7 | Remitente manda mensaje | El broadcast excluye al remitente | A no recibe su propio mensaje, B sí |

### Reporte de Pruebas

| **Total** | **Correctas** | **Fallidas** | **Falsos positivos** | **Falsos negativos** |
|---|---|---|---|---|
| 7 | 7/7 | 0 | 0 | 0 |

El programa pasó correctamente las 7 pruebas definidas. Cada prueba verifica un aspecto específico del paradigma concurrente: desde la creación de múltiples threads simultáneos hasta la correcta sincronización con el mutex.

### Imagenes Pruebas
Prueba 1
<img width="1200" height="240" alt="image" src="https://github.com/user-attachments/assets/86147a56-3755-46de-97ff-f822ce53552c" />
<img width="818" height="385" alt="image" src="https://github.com/user-attachments/assets/6c784b52-9687-49fb-a4cc-42dee8a6b942" />

Prueba 2
<img width="1593" height="280" alt="image" src="https://github.com/user-attachments/assets/50e06cd3-a3d4-4a2c-8bc5-ba33eb63b2fe" />
<img width="478" height="140" alt="image" src="https://github.com/user-attachments/assets/93172fb5-b75c-4d23-8505-00e800d65f3a" />

Prueba 3
<img width="918" height="236" alt="image" src="https://github.com/user-attachments/assets/12cad215-dbb4-4e6a-a5bc-f02db33a034b" />
<img width="738" height="204" alt="image" src="https://github.com/user-attachments/assets/801b3c37-bc68-48a8-a529-d4c44d245a03" />

---

## Análisis | Complejidad de la concurrencia

### Solución concurrente (threads)

| **Operación** | **Complejidad** |
|-----------|-------------|
| Conectar un cliente nuevo | O(1) |
| Broadcast a n clientes | O(n) |
| Memoria total con n clientes | O(n) |

El broadcast es la parte más lenta donde por cada mensaje enviado, el servidor itera sobre todos los clientes conectados. Con `n` clientes y `m` mensajes, la complejidad final es **O(n · m)**.

### Paradigma Alternativo | Programación Asíncronica

Python ofrece `asyncio` como alternativa al modelo de threads. En lugar de crear un thread por cliente, `asyncio` implementa concurrencia mediante un event loop en un solo thread que intercala la ejecución de múltiples coroutines (una función especial que puede pausar su ejecución, devolver el control al programa y reanudarse exactamente en el punto donde se quedó), cediendo el control voluntariamente en operaciones de I/O (Input / Output). Esto significa que en lugar de tener 100 threads para 100 clientes, hay un solo thread manejando 100 coroutines (GeeksforGeeks, 2026)

### Comparación

| **Criterio** | **Threads** | **Asíncrono** |
|----------|----------------------|----------------------|
| Modelo de ejecución | Un thread por cliente | Un event loop, múltiples coroutines |
| Complejidad broadcast | O(n) | O(n) |
| Race conditions | Posibles, requiere mutex | N/A (single-thread) |
| Escalabilidad | Limitada ( Aprox cientos) | Alta (miles) |
| Legibilidad del código | Alta | Media (requiere async/await) |

Ambas soluciones tienen la misma complejidad temporal **O(n · m)**, pero `asyncio` escala mejor en memoria y elimina el problema de race conditions al no tener verdadero paralelismo de escritura. Aun así, para el alcance de este problema el cual es de pocos clientes locales, la solución con threads es más directa, fácil de leer y más representativa del paradigma concurrente visto en clase, donde los threads son la unidad de concurrencia explícita 

---

## Referencias
Tanenbaum, A. S., & Bos, H. (2014). Modern Operating Systems (4th ed.). (Capítulo 2: Processes and Threads) - PDF: https://os.ecci.ucr.ac.cr/slides/Andrew-S.-Tanenbaum-Modern-Operating-Systems.pdf

Beazley, D., & Jones, B. K. (2013). *Python Cookbook* (3rd ed.). O'Reilly
Media. PDF: https://elhacker.info/manuales/OReilly%204%20GB%20Collection/O'Reilly%20-%20Python%20Cookbook.pdf

GeeksforGeeks. (2025). Concurrency in Python. Recuperado de https://www.geeksforgeeks.org/python/python-program-with-concurrency/

Python Software Foundation. (2024). threading — Thread-based parallelism. Recuperado de https://docs.python.org/3/library/threading.html

Python Software Foundation. (2024). socket — Low-level networking interface. Recuperado de https://docs.python.org/3/library/socket.html

GeeksforGeeks. (2026). Python Async. Recuperado de https://www.geeksforgeeks.org/python/python-async/
