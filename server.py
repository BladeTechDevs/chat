# server.py - servidor de chat con autenticación (login/register) y colores

import socket                                      # comunicación TCP/IP
import threading                                   # manejar múltiples clientes
import datetime                                    # timestamps
import hashlib                                     # hash para nicknames y passwords
import sys                                         # sys.exit y stdout

from models import SessionLocal, User              # modelo de la BD

# intento de inicializar colorama (opcional para Windows)
try:
    import colorama
    colorama.init()
except Exception:
    pass

# intento de usar pyfiglet para banner bonito
try:
    import pyfiglet
    BANNER = pyfiglet.figlet_format("CHAT SERVER")
except Exception:
    BANNER = "=== CHAT SERVER ==="

# códigos ANSI básicos
RESET = "\033[0m"
BOLD = "\033[1m"

PALETTE = [
    "\033[38;5;196m",  # rojo brillante
    "\033[38;5;208m",  # naranja
    "\033[38;5;226m",  # amarillo
    "\033[38;5;82m",   # verde
    "\033[38;5;39m",   # azul
    "\033[38;5;99m",   # violeta/rosa
    "\033[38;5;51m",   # cyan claro
    "\033[38;5;214m",  # ambar
]

# función para dar color según el nickname
def get_color_for_nickname(nickname):
    h = hashlib.md5(nickname.encode("utf-8")).hexdigest()
    num = int(h[:8], 16)
    return PALETTE[num % len(PALETTE)]

# formato de mensajes
def format_message(nickname, message, system=False):
    ts = datetime.datetime.now().strftime("%H:%M")
    if system:
        return f"{BOLD}[{ts}]{RESET} {PALETTE[5]}* {message}{RESET}"
    color = get_color_for_nickname(nickname)
    return f"{BOLD}[{ts}]{RESET} {color}{nickname}{RESET}: {message}"

# configuración del servidor
HOST = "127.0.0.1"
PORT = 5000

# creación del socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)

print(BANNER)
print(f"{BOLD}Servidor escuchando en {HOST}:{PORT}{RESET}")

clients = []       # lista de sockets
nicknames = {}     # diccionario socket -> nickname

# === Funciones de autenticación con BD ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    session = SessionLocal()
    if session.query(User).filter_by(username=username).first():
        session.close()
        return False, "Usuario ya existe"
    user = User(username=username, password=hash_password(password))
    session.add(user)
    session.commit()
    session.close()
    return True, "Usuario registrado con éxito"

def login_user(username, password):
    session = SessionLocal()
    user = session.query(User).filter_by(username=username).first()
    if user and user.password == hash_password(password):
        session.close()
        return True, "Login correcto"
    session.close()
    return False, "Usuario o contraseña incorrectos"

# === funciones principales del chat ===
def broadcast(message, exclude_client=None):
    for client in clients:
        if client is exclude_client:
            continue
        try:
            client.send(message.encode("utf-8"))
        except Exception:
            try:
                clients.remove(client)
            except ValueError:
                pass
            if client in nicknames:
                left_nick = nicknames.pop(client)
                broadcast(format_message(left_nick, f"{left_nick} perdió conexión.", system=True))

def handle_client(client):
    while True:
        try:
            data = client.recv(4096).decode("utf-8")
            if not data:
                raise ConnectionResetError

            if data.strip() == "/quit":
                nickname = nicknames.get(client, "Alguien")
                broadcast(format_message(nickname, f"{nickname} se ha desconectado.", system=True), exclude_client=client)
                if client in clients:
                    clients.remove(client)
                nicknames.pop(client, None)
                client.close()
                break

            elif data.strip() == "/lista":
                lista = ", ".join(nicknames.values()) or "No hay usuarios conectados"
                try:
                    client.send(format_message("Sistema", f"Usuarios: {lista}", system=True).encode("utf-8"))
                except Exception:
                    pass
            else:
                nickname = nicknames.get(client, "Anonimo")
                formatted = format_message(nickname, data)
                broadcast(formatted)

        except Exception:
            if client in clients:
                clients.remove(client)
            nickname = nicknames.pop(client, None)
            if nickname:
                try:
                    broadcast(format_message(nickname, f"{nickname} salió inesperadamente.", system=True))
                except Exception:
                    pass
            try:
                client.close()
            except Exception:
                pass
            break

def receive_connections():
    while True:
        client, address = server.accept()
        print(f"{BOLD}Conexión entrante desde {address}{RESET}")

        try:
            data = client.recv(1024).decode("utf-8").strip()
            parts = data.split("|")
            if len(parts) != 3:
                client.send("Formato inválido".encode("utf-8"))
                client.close()
                continue

            action, username, password = parts

            if action == "REGISTER":
                ok, msg = register_user(username, password)
                if not ok:
                    client.send(msg.encode("utf-8"))
                    client.close()
                    continue
                client.send("OK".encode("utf-8"))

            elif action == "LOGIN":
                ok, msg = login_user(username, password)
                if not ok:
                    client.send(msg.encode("utf-8"))
                    client.close()
                    continue
                client.send("OK".encode("utf-8"))
            else:
                client.send("Acción inválida".encode("utf-8"))
                client.close()
                continue

            nickname = username
        except Exception as e:
            print(f"Error en autenticación: {e}")
            client.close()
            continue

        # usuario autenticado -> lo añadimos al chat
        clients.append(client)
        nicknames[client] = nickname
        broadcast(format_message("Sistema", f"{nickname} se unió al chat.", system=True))
        try:
            client.send(format_message("Sistema", "Conectado al servidor. Usa /quit para salir, /lista para ver usuarios.", system=True).encode("utf-8"))
        except Exception:
            pass

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.daemon = True
        thread.start()

# === main ===
if __name__ == "__main__":
    try:
        receive_connections()
    except KeyboardInterrupt:
        print("\nServidor detenido por teclado.")
        try:
            server.close()
        except Exception:
            pass
        sys.exit(0)
