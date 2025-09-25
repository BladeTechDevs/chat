# client.py - cliente de chat con estilo en consola y comentarios en español por línea


import socket                                      # socket para conexión TCP/IP
import threading                                   # threading para recibir y enviar simultáneamente
import sys                                         # sys para escribir en stdout y flush
import time                                        # time para pequeños sleeps opcionales


# intentamos colorama y pyfiglet para mejor aspecto en Windows/terminal
try:
    import colorama                                # soporte Windows ANSI
    colorama.init()                                # inicializa colorama
except Exception:
    pass
try:
    import pyfiglet                                # texto grande opcional
    BANNER = pyfiglet.figlet_format("CHAT CLIENT")
except Exception:
    BANNER = "=== CHAT CLIENT ==="


# algunos códigos ANSI (los mismos que usa el servidor para compatibilidad visual)
RESET = "\033[0m"                                  # resetea color/estilo
BOLD = "\033[1m"                                   # negrita


# configuración: HOST y PORT deben coincidir con el servidor
HOST = "127.0.0.1"                                 # host del servidor (localhost)
PORT = 5000                                        # puerto del servidor

def menu_login():
    while True:
        print("\n=== MENÚ ===")
        print("1. Iniciar sesión")
        print("2. Registrarse")
        print("3. Salir")
        opcion = input("Elige opción: ").strip()
        
        if opcion == "1":
            username = input("Usuario: ")
            password = input("Contraseña: ")
            return "LOGIN", username, password
        elif opcion == "2":
            username = input("Nuevo usuario: ")
            password = input("Nueva contraseña: ")
            return "REGISTER", username, password
        elif opcion == "3":
            sys.exit(0)
        else:
            print("Opción inválida")


action, user, pwd = menu_login()

# solicitud del nickname al usuario
# nickname = input("Elige un nickname: ")            # pide al usuario que ingrese su nickname


# creación del socket cliente y conexión al servidor
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket TCP
try:
    client.connect((HOST, PORT))                    # intenta conectar al servidor
except Exception as e:
    print(f"No se pudo conectar al servidor: {e}")  # muestra error si falla la conexión
    sys.exit(1)                                     # sale del programa con código de error

# Mandamos al servidor acción + credenciales
client.send(f"{action}|{user}|{pwd}".encode("utf-8"))

resp = client.recv(1024).decode("utf-8")
if resp != "OK":
    print(f"Error: {resp}")
    client.close()
    sys.exit(1)

nickname = user  # usamos el username como nickname

print(BANNER)                                       # imprime banner del cliente
print(f"{BOLD}Conectado a {HOST}:{PORT} como {nickname}{RESET}")  # muestra mensaje de confirmación


# función para recibir mensajes del servidor
def receive_messages():                              # hilo que escucha mensajes entrantes
    while True:                                      # bucle infinito de recepción
        try:
            message = client.recv(4096).decode("utf-8")  # recibe datos y decodifica UTF-8
            if not message:                          # si el servidor cerró la conexión, romper
                print("\nConexión cerrada por el servidor.")  # informa
                client.close()                       # cierra socket local
                break                                 # sale del bucle
            if message == "NICK":                    # si el servidor pide el nickname (handshake)
                client.send(nickname.encode("utf-8")) # enviamos nuestro nickname
                continue                              # seguimos esperando otros mensajes
            # impresión "amigable" que no rompe la línea de input actual
            sys.stdout.write("\r" + " " * 80 + "\r")   # limpia la línea actual (intento simple)
            print(message)                            # imprime el mensaje recibido
            sys.stdout.write("> ")                    # reimprime prompt
            sys.stdout.flush()                        # fuerza impresión inmediata
        except Exception:
            print("\nError recibiendo datos del servidor.")  # muestra error si falla recepción
            client.close()                            # cierra socket
            break                                     # rompe bucle


# función para enviar mensajes al servidor
def write_messages():                                 # hilo que lee input del usuario y envía
    while True:                                       # bucle infinito de envío
        try:
            msg = input("> ")                         # lee mensaje del usuario con prompt
            if msg.strip() == "":                     # si ingreso vacío, lo ignora
                continue
            if msg.strip().lower() == "/quit":       # si usuario quiere salir con /quit
                client.send("/quit".encode("utf-8"))  # enviamos comando de salida al servidor
                print("Desconectando...")             # informamos al usuario
                time.sleep(0.2)                       # pequeño delay para que el mensaje salga
                client.close()                        # cerramos socket
                break                                 # salimos del bucle y terminamos hilo
            client.send(msg.encode("utf-8"))          # enviamos mensaje normal al servidor
        except Exception:
            print("Error enviando mensaje.")          # en caso de excepción informamos
            client.close()                            # cerramos socket por seguridad
            break                                     # terminamos el hilo


# creamos y arrancamos los hilos de recepción y escritura
receive_thread = threading.Thread(target=receive_messages)  # hilo receptor
receive_thread.daemon = True                           # daemon para que no impida cerrar el programa
receive_thread.start()                                 # iniciamos el hilo receptor


write_thread = threading.Thread(target=write_messages) # hilo para enviar mensajes
write_thread.daemon = True                            # daemon también
write_thread.start()                                  # iniciamos hilo de envío


# mantenemos el hilo principal vivo mientras los hilos trabajen
try:
    while True:
        time.sleep(0.1)                               # bucle liviano que evita terminar el main thread
        if not receive_thread.is_alive():             # si el hilo de recepción terminó, salimos
            break
        if not write_thread.is_alive():               # si hilo de escritura terminó, salimos
            break
except KeyboardInterrupt:
    try:
        client.send("/quit".encode("utf-8"))          # intenta avisar al servidor si ctrl+c
    except Exception:
        pass
    client.close()                                    # cierra socket local
    print("\nCliente detenido por teclado.")          # mensaje final
    sys.exit(0)                                       # salimos del programa


