# server.py - servidor de chat con autenticación (login/register) y colores

import socket                                      # comunicación TCP/IP
import threading                                   # manejar múltiples clientes
import datetime                                    # timestamps
import hashlib                                     # hash para nicknames y passwords
import sys                                         # sys.exit y stdout
import random                                      # para generar IDs de sala
import string                                      # para generar IDs de sala
from crypto_utils import decrypt_message, encrypt_message
from models import SessionLocal, User, Room, RoomMember              # modelo de la BD

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

rooms = {}           # diccionario room_id -> {'clients': [], 'name': '', 'creator': ''}
client_rooms = {}    # diccionario client -> room_id

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

def generate_room_id():
    """Generar ID único para sala"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_room_in_db(name, creator_username, description=""):
    """Crear sala en la base de datos"""
    session = SessionLocal()
    try:
        # Buscar usuario creador
        creator = session.query(User).filter_by(username=creator_username).first()
        if not creator:
            return False, "Usuario no encontrado"
        
        # Generar ID único
        room_id = generate_room_id()
        while session.query(Room).filter_by(room_id=room_id).first():
            room_id = generate_room_id()
        
        # Crear sala
        room = Room(
            name=name,
            room_id=room_id,
            creator_id=creator.id,
            description=description
        )
        session.add(room)
        session.commit()
        
        # Agregar creador como miembro
        member = RoomMember(room_id=room.id, user_id=creator.id)
        session.add(member)
        session.commit()
        
        return True, room_id
    except Exception as e:
        session.rollback()
        return False, f"Error creando sala: {str(e)}"
    finally:
        session.close()

def join_room_in_db(room_id, username):
    """Unir usuario a sala en la base de datos"""
    session = SessionLocal()
    try:
        # Buscar sala y usuario
        room = session.query(Room).filter_by(room_id=room_id).first()
        user = session.query(User).filter_by(username=username).first()
        
        if not room:
            return False, "Sala no encontrada"
        if not user:
            return False, "Usuario no encontrado"
        
        # Verificar si ya está en la sala
        existing = session.query(RoomMember).filter_by(
            room_id=room.id, user_id=user.id
        ).first()
        
        if existing:
            return True, room.name  # Ya está en la sala
        
        # Agregar como miembro
        member = RoomMember(room_id=room.id, user_id=user.id)
        session.add(member)
        session.commit()
        
        return True, room.name
    except Exception as e:
        session.rollback()
        return False, f"Error uniéndose a sala: {str(e)}"
    finally:
        session.close()

def get_user_rooms(username):
    """Obtener salas del usuario"""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return []
        
        # Obtener salas donde es miembro
        rooms_query = session.query(Room).join(RoomMember).filter(
            RoomMember.user_id == user.id
        ).all()
        
        result = []
        for room in rooms_query:
            result.append({
                'id': room.room_id,
                'name': room.name,
                'description': room.description or '',
                'is_creator': room.creator_id == user.id
            })
        
        return result
    except Exception as e:
        return []
    finally:
        session.close()

def delete_room_in_db(room_id, username):
    """Eliminar sala (solo el creador puede)"""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        room = session.query(Room).filter_by(room_id=room_id).first()
        
        if not user or not room:
            return False, "Sala o usuario no encontrado"
        
        if room.creator_id != user.id:
            return False, "Solo el creador puede eliminar la sala"
        
        # Eliminar miembros y sala
        session.query(RoomMember).filter_by(room_id=room.id).delete()
        session.delete(room)
        session.commit()
        
        return True, "Sala eliminada"
    except Exception as e:
        session.rollback()
        return False, f"Error eliminando sala: {str(e)}"
    finally:
        session.close()

def broadcast_to_room(message, room_id, exclude_client=None):
    """Enviar mensaje a todos los clientes de una sala específica"""
    if room_id not in rooms:
        return
    
    for client in rooms[room_id]['clients']:
        if client is exclude_client:
            continue
        try:
            client.send(message.encode("utf-8"))
        except Exception:
            try:
                rooms[room_id]['clients'].remove(client)
            except ValueError:
                pass

def broadcast(message, exclude_client=None):
    """Broadcast global (mantener compatibilidad)"""
    for client in clients:
        if client is exclude_client:
            continue
        try:
            # client.send(message.encode("utf-8"))
            client.send(encrypt_message(message))
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
            # data = client.recv(4096).decode("utf-8")
            raw_data = client.recv(4096)
            try:
                data = decrypt_message(raw_data)
            except Exception:
                data = raw_data.decode("utf-8")  # por compatibilidad
                continue
            
            if not data:
                raise ConnectionResetError

            if data.strip() == "/quit":
                nickname = nicknames.get(client, "Alguien")
                
                # Remover de sala si está en una
                if client in client_rooms:
                    room_id = client_rooms[client]
                    if room_id in rooms:
                        rooms[room_id]['clients'].remove(client)
                        broadcast_to_room(
                            format_message(nickname, f"{nickname} salió de la sala.", system=True),
                            room_id, exclude_client=client
                        )
                    del client_rooms[client]
                
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
            
            elif data.startswith("/crear_sala "):
                parts = data.split(" ", 2)
                if len(parts) < 2:
                    client.send(format_message("Sistema", "Uso: /crear_sala <nombre> [descripción]", system=True).encode("utf-8"))
                    continue
                
                room_name = parts[1]
                description = parts[2] if len(parts) > 2 else ""
                nickname = nicknames.get(client, "Anonimo")
                
                success, result = create_room_in_db(room_name, nickname, description)
                if success:
                    client.send(format_message("Sistema", f"Sala creada: {room_name} (ID: {result})", system=True).encode("utf-8"))
                else:
                    client.send(format_message("Sistema", f"Error: {result}", system=True).encode("utf-8"))
            
            elif data.startswith("/unirse "):
                parts = data.split(" ", 1)
                if len(parts) < 2:
                    client.send(format_message("Sistema", "Uso: /unirse <ID_sala>", system=True).encode("utf-8"))
                    continue
                
                room_id = parts[1].strip()
                nickname = nicknames.get(client, "Anonimo")
                
                success, result = join_room_in_db(room_id, nickname)
                if success:
                    # Remover de sala anterior si estaba en una
                    if client in client_rooms:
                        old_room = client_rooms[client]
                        if old_room in rooms:
                            rooms[old_room]['clients'].remove(client)
                            broadcast_to_room(
                                format_message(nickname, f"{nickname} salió de la sala.", system=True),
                                old_room, exclude_client=client
                            )
                    
                    # Agregar a nueva sala
                    if room_id not in rooms:
                        rooms[room_id] = {'clients': [], 'name': result}
                    
                    rooms[room_id]['clients'].append(client)
                    client_rooms[client] = room_id
                    
                    client.send(format_message("Sistema", f"Te uniste a la sala: {result}", system=True).encode("utf-8"))
                    broadcast_to_room(
                        format_message(nickname, f"{nickname} se unió a la sala.", system=True),
                        room_id, exclude_client=client
                    )
                else:
                    client.send(format_message("Sistema", f"Error: {result}", system=True).encode("utf-8"))
            
            elif data.strip() == "/mis_salas":
                nickname = nicknames.get(client, "Anonimo")
                user_rooms = get_user_rooms(nickname)
                
                if not user_rooms:
                    client.send(format_message("Sistema", "No estás en ninguna sala.", system=True).encode("utf-8"))
                else:
                    msg = "Tus salas:\n"
                    for room in user_rooms:
                        creator_mark = " (Creador)" if room['is_creator'] else ""
                        msg += f"• {room['name']} - ID: {room['id']}{creator_mark}\n"
                    client.send(format_message("Sistema", msg.strip(), system=True).encode("utf-8"))
            
            elif data.startswith("/eliminar_sala "):
                parts = data.split(" ", 1)
                if len(parts) < 2:
                    client.send(format_message("Sistema", "Uso: /eliminar_sala <ID_sala>", system=True).encode("utf-8"))
                    continue
                
                room_id = parts[1].strip()
                nickname = nicknames.get(client, "Anonimo")
                
                success, result = delete_room_in_db(room_id, nickname)
                if success:
                    # Desconectar a todos los usuarios de la sala
                    if room_id in rooms:
                        for room_client in rooms[room_id]['clients']:
                            if room_client in client_rooms:
                                del client_rooms[room_client]
                            room_client.send(format_message("Sistema", f"La sala fue eliminada por {nickname}.", system=True).encode("utf-8"))
                        del rooms[room_id]
                    
                    client.send(format_message("Sistema", result, system=True).encode("utf-8"))
                else:
                    client.send(format_message("Sistema", f"Error: {result}", system=True).encode("utf-8"))
            
            elif data.strip() == "/salir_sala":
                if client not in client_rooms:
                    client.send(format_message("Sistema", "No estás en ninguna sala.", system=True).encode("utf-8"))
                    continue
                
                room_id = client_rooms[client]
                nickname = nicknames.get(client, "Anonimo")
                
                if room_id in rooms:
                    rooms[room_id]['clients'].remove(client)
                    broadcast_to_room(
                        format_message(nickname, f"{nickname} salió de la sala.", system=True),
                        room_id, exclude_client=client
                    )
                
                del client_rooms[client]
                client.send(format_message("Sistema", "Saliste de la sala.", system=True).encode("utf-8"))
            
            elif data.strip() == "/ayuda":
                help_msg = """Comandos disponibles:
/crear_sala <nombre> [descripción] - Crear nueva sala
/unirse <ID_sala> - Unirse a una sala
/mis_salas - Ver tus salas
/eliminar_sala <ID_sala> - Eliminar sala (solo creador)
/salir_sala - Salir de la sala actual
/lista - Ver usuarios conectados
/quit - Desconectarse"""
                client.send(format_message("Sistema", help_msg, system=True).encode("utf-8"))
            
            else:
                nickname = nicknames.get(client, "Anonimo")
                formatted = format_message(nickname, data)
                
                # Enviar a sala si está en una, sino broadcast global
                if client in client_rooms:
                    room_id = client_rooms[client]
                    broadcast_to_room(formatted, room_id)
                else:
                    broadcast(formatted)

        except Exception:
            if client in clients:
                clients.remove(client)
            nickname = nicknames.pop(client, None)
            
            # Remover de sala si estaba en una
            if client in client_rooms:
                room_id = client_rooms[client]
                if room_id in rooms:
                    try:
                        rooms[room_id]['clients'].remove(client)
                        if nickname:
                            broadcast_to_room(
                                format_message(nickname, f"{nickname} salió inesperadamente.", system=True),
                                room_id
                            )
                    except ValueError:
                        pass
                del client_rooms[client]
            
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
            welcome_msg = """Conectado al servidor. 
Comandos: /ayuda para ver todos los comandos
/crear_sala <nombre> para crear una sala
/unirse <ID_sala> para unirse a una sala"""
            client.send(format_message("Sistema", welcome_msg, system=True).encode("utf-8"))
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
