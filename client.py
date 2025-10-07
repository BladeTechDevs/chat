import socket
import threading
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from tkinter import font
import re
from crypto_utils import encrypt_message, decrypt_message

# Configuración: HOST y PORT deben coincidir con el servidor
HOST = "127.0.0.1"
PORT = 5000

class ChatClient:
    def __init__(self):
        self.client = None
        self.nickname = ""
        self.connected = False
        self.current_room = None  # Track current room
        
        # Ventana principal
        self.root = tk.Tk()
        self.root.title("Chat")
        self.root.geometry("600x700")
        self.root.configure(bg='#0f1419')
        
        # Configurar estilo
        self.setup_styles()
        
        # Mostrar menú de login
        self.show_login_menu()
        
    def setup_styles(self):
        # Configurar fuentes modernas
        self.title_font = font.Font(family="Segoe UI", size=18, weight="bold")
        self.button_font = font.Font(family="Segoe UI", size=11)
        self.text_font = font.Font(family="Segoe UI", size=10)
        self.message_font = font.Font(family="Segoe UI", size=10)
        self.small_font = font.Font(family="Segoe UI", size=8)
        
    def show_login_menu(self):
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Frame principal con gradiente simulado
        main_frame = tk.Frame(self.root, bg='#0f1419')
        main_frame.pack(expand=True, fill='both', padx=30, pady=30)
        
        # Título moderno
        title_label = tk.Label(main_frame, text="💬 Chat", 
                              font=self.title_font, fg='#00d4ff', bg='#0f1419')
        title_label.pack(pady=30)
        
        # Subtítulo
        subtitle_label = tk.Label(main_frame, text="Conecta y chatea en tiempo real", 
                                 font=self.button_font, fg='#8b949e', bg='#0f1419')
        subtitle_label.pack(pady=(0, 40))
        
        # Frame para opciones con bordes redondeados simulados
        options_frame = tk.Frame(main_frame, bg='#1c2128', relief='flat', bd=0)
        options_frame.pack(pady=20, padx=60, fill='x')
        
        # Padding interno
        inner_frame = tk.Frame(options_frame, bg='#1c2128')
        inner_frame.pack(padx=30, pady=30)
        
        # Botones modernos con hover effect simulado
        login_btn = tk.Button(inner_frame, text="🔑 Iniciar sesión", 
                             font=self.button_font, bg='#238636', fg='white',
                             command=self.show_login_form, width=25, height=2,
                             relief='flat', bd=0, cursor='hand2')
        login_btn.pack(pady=8)
        
        register_btn = tk.Button(inner_frame, text="📝 Registrarse", 
                                font=self.button_font, bg='#1f6feb', fg='white',
                                command=self.show_register_form, width=25, height=2,
                                relief='flat', bd=0, cursor='hand2')
        register_btn.pack(pady=8)
        
        exit_btn = tk.Button(inner_frame, text="❌ Salir", 
                            font=self.button_font, bg='#da3633', fg='white',
                            command=self.root.quit, width=25, height=2,
                            relief='flat', bd=0, cursor='hand2')
        exit_btn.pack(pady=8)
        
    def show_login_form(self):
        self.show_auth_form("LOGIN", "🔑 Iniciar Sesión")
        
    def show_register_form(self):
        self.show_auth_form("REGISTER", "📝 Registrarse")
        
    def show_auth_form(self, action, title):
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#0f1419')
        main_frame.pack(expand=True, fill='both', padx=30, pady=30)
        
        # Título
        title_label = tk.Label(main_frame, text=title, 
                              font=self.title_font, fg='#00d4ff', bg='#0f1419')
        title_label.pack(pady=30)
        
        # Frame para formulario
        form_frame = tk.Frame(main_frame, bg='#1c2128', relief='flat', bd=0)
        form_frame.pack(pady=20, padx=60, fill='x')
        
        # Padding interno
        inner_form = tk.Frame(form_frame, bg='#1c2128')
        inner_form.pack(padx=40, pady=40)
        
        # Usuario
        tk.Label(inner_form, text="👤 Usuario:", font=self.button_font, 
                fg='#f0f6fc', bg='#1c2128').pack(pady=(0,8), anchor='w')
        user_entry = tk.Entry(inner_form, font=self.text_font, width=35, 
                             bg='#21262d', fg='#f0f6fc', relief='flat', bd=5,
                             insertbackground='#00d4ff')
        user_entry.pack(pady=(0,20))
        
        # Contraseña
        tk.Label(inner_form, text="🔒 Contraseña:", font=self.button_font, 
                fg='#f0f6fc', bg='#1c2128').pack(pady=(0,8), anchor='w')
        pwd_entry = tk.Entry(inner_form, font=self.text_font, width=35, show="*",
                            bg='#21262d', fg='#f0f6fc', relief='flat', bd=5,
                            insertbackground='#00d4ff')
        pwd_entry.pack(pady=(0,30))
        
        # Botones
        btn_frame = tk.Frame(inner_form, bg='#1c2128')
        btn_frame.pack()
        
        connect_btn = tk.Button(btn_frame, text="🚀 Conectar", 
                               font=self.button_font, bg='#238636', fg='white',
                               command=lambda: self.authenticate(action, user_entry.get(), pwd_entry.get()),
                               relief='flat', bd=0, cursor='hand2', width=12, height=2)
        connect_btn.pack(side='left', padx=5)
        
        back_btn = tk.Button(btn_frame, text="⬅️ Volver", 
                            font=self.button_font, bg='#6e7681', fg='white',
                            command=self.show_login_menu, relief='flat', bd=0, 
                            cursor='hand2', width=12, height=2)
        back_btn.pack(side='left', padx=5)
        
        # Focus en primer campo
        user_entry.focus()
        
    def authenticate(self, action, username, password):
        if not username or not password:
            messagebox.showerror("Error", "Por favor completa todos los campos")
            return
            
        try:
            # Crear socket y conectar
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))
            
            # Enviar credenciales
            self.client.send(f"{action}|{username}|{password}".encode("utf-8"))
            
            # Recibir respuesta
            resp = self.client.recv(1024).decode("utf-8")
            if resp != "OK":
                messagebox.showerror("Error", f"Error: {resp}")
                self.client.close()
                return
                
            # Éxito
            self.nickname = username
            self.connected = True
            self.show_chat_window()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar al servidor: {e}")
            if self.client:
                self.client.close()
                
    def show_chat_window(self):
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.root.title(f"💬 Chat - {self.nickname}")
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#0f1419')
        main_frame.pack(expand=True, fill='both')
        
        header_frame = tk.Frame(main_frame, bg='#1c2128', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Top row - connection info
        top_header = tk.Frame(header_frame, bg='#1c2128')
        top_header.pack(fill='x', pady=5)
        
        connection_info = tk.Label(top_header, 
                                  text=f"🟢 Conectado como {self.nickname} • {HOST}:{PORT}", 
                                  font=self.button_font, fg='#00d4ff', bg='#1c2128')
        connection_info.pack(side='left', padx=15)
        
        # Room management buttons
        room_btn_frame = tk.Frame(top_header, bg='#1c2128')
        room_btn_frame.pack(side='right', padx=15)
        
        create_room_btn = tk.Button(room_btn_frame, text="🏠 Crear Sala", 
                                   font=self.small_font, bg='#238636', fg='white',
                                   command=self.create_room_dialog, relief='flat', bd=0, 
                                   cursor='hand2', padx=10, pady=5)
        create_room_btn.pack(side='left', padx=2)
        
        join_room_btn = tk.Button(room_btn_frame, text="🚪 Unirse", 
                                 font=self.small_font, bg='#1f6feb', fg='white',
                                 command=self.join_room_dialog, relief='flat', bd=0, 
                                 cursor='hand2', padx=10, pady=5)
        join_room_btn.pack(side='left', padx=2)
        
        my_rooms_btn = tk.Button(room_btn_frame, text="📋 Mis Salas", 
                                font=self.small_font, bg='#6e7681', fg='white',
                                command=self.show_my_rooms, relief='flat', bd=0, 
                                cursor='hand2', padx=10, pady=5)
        my_rooms_btn.pack(side='left', padx=2)
        
        # Bottom row - current room info
        bottom_header = tk.Frame(header_frame, bg='#1c2128')
        bottom_header.pack(fill='x', pady=(0,5))
        
        self.room_info_label = tk.Label(bottom_header, 
                                       text="📢 Chat Global - Usa /ayuda para ver comandos", 
                                       font=self.text_font, fg='#f0f6fc', bg='#1c2128')
        self.room_info_label.pack(side='left', padx=15)
        
        # Leave room button (initially hidden)
        self.leave_room_btn = tk.Button(bottom_header, text="🚪 Salir de Sala", 
                                       font=self.small_font, bg='#da3633', fg='white',
                                       command=self.leave_room, relief='flat', bd=0, 
                                       cursor='hand2', padx=10, pady=3)
        # Don't pack initially
        
        # ... existing code for chat area ...
        
        # Frame para el área de chat con scroll
        chat_frame = tk.Frame(main_frame, bg='#0f1419')
        chat_frame.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Canvas y scrollbar para el chat
        self.chat_canvas = tk.Canvas(chat_frame, bg='#0f1419', highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_frame, orient="vertical", command=self.chat_canvas.yview,
                                bg='#21262d', troughcolor='#0f1419', activebackground='#6e7681')
        self.scrollable_frame = tk.Frame(self.chat_canvas, bg='#0f1419')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )
        
        self.chat_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ... existing code for input area ...
        
        # Frame para entrada de mensaje
        input_frame = tk.Frame(main_frame, bg='#1c2128', height=80)
        input_frame.pack(fill='x')
        input_frame.pack_propagate(False)
        
        # Padding interno para el input
        input_inner = tk.Frame(input_frame, bg='#1c2128')
        input_inner.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Campo de entrada moderno
        entry_frame = tk.Frame(input_inner, bg='#21262d', relief='flat', bd=1)
        entry_frame.pack(side='left', expand=True, fill='x', padx=(0,10))
        
        self.message_entry = tk.Entry(entry_frame, font=self.text_font, 
                                     bg='#21262d', fg='#f0f6fc', relief='flat', bd=10,
                                     insertbackground='#00d4ff')
        self.message_entry.pack(expand=True, fill='both')
        self.message_entry.bind('<Return>', self.send_message)
        
        # Botón enviar moderno
        send_btn = tk.Button(input_inner, text="📤", 
                            font=font.Font(size=16), bg='#238636', fg='white',
                            command=self.send_message, relief='flat', bd=0, 
                            cursor='hand2', width=4, height=1)
        send_btn.pack(side='right')
        
        # Botón desconectar en la esquina
        disconnect_btn = tk.Button(input_inner, text="🔌", 
                                  font=font.Font(size=12), bg='#da3633', fg='white',
                                  command=self.disconnect, relief='flat', bd=0, 
                                  cursor='hand2', width=3, height=1)
        disconnect_btn.pack(side='right', padx=(5,0))
        
        # Focus en entrada
        self.message_entry.focus()
        
        # Iniciar hilo de recepción
        self.start_receive_thread()
        
        # Mensaje de bienvenida
        self.add_bubble_message("¡Bienvenido al chat! 🎉 Usa /ayuda para ver los comandos de salas", "system")
    
    def create_room_dialog(self):
        """Diálogo para crear nueva sala"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🏠 Crear Nueva Sala")
        dialog.geometry("400x500")
        dialog.configure(bg='#1c2128')
        dialog.resizable(False, False)
        
        # Centrar diálogo
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#1c2128')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame, text="🏠 Crear Nueva Sala", 
                              font=self.title_font, fg='#00d4ff', bg='#1c2128')
        title_label.pack(pady=(0,20))
        
        # Nombre de sala
        tk.Label(main_frame, text="📝 Nombre de la sala:", font=self.button_font, 
                fg='#f0f6fc', bg='#1c2128').pack(anchor='w', pady=(0,5))
        name_entry = tk.Entry(main_frame, font=self.text_font, width=40, 
                             bg='#21262d', fg='#f0f6fc', relief='flat', bd=5,
                             insertbackground='#00d4ff')
        name_entry.pack(pady=(0,15))
        
        # Descripción
        tk.Label(main_frame, text="📄 Descripción (opcional):", font=self.button_font, 
                fg='#f0f6fc', bg='#1c2128').pack(anchor='w', pady=(0,5))
        desc_text = tk.Text(main_frame, font=self.text_font, width=40, height=4,
                           bg='#21262d', fg='#f0f6fc', relief='flat', bd=5,
                           insertbackground='#00d4ff')
        desc_text.pack(pady=(0,20))
        
        # Botones
        btn_frame = tk.Frame(main_frame, bg='#1c2128')
        btn_frame.pack()
        
        def create_room():
            name = name_entry.get().strip()
            desc = desc_text.get("1.0", tk.END).strip()
            
            if not name:
                messagebox.showerror("Error", "El nombre de la sala es obligatorio")
                return
            
            # Enviar comando al servidor
            cmd = f"/crear_sala {name}"
            if desc:
                cmd += f" {desc}"
            
            self.send_command(cmd)
            dialog.destroy()
        
        create_btn = tk.Button(btn_frame, text="🚀 Crear", 
                              font=self.button_font, bg='#238636', fg='white',
                              command=create_room, relief='flat', bd=0, 
                              cursor='hand2', width=12, height=2)
        create_btn.pack(side='left', padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="❌ Cancelar", 
                              font=self.button_font, bg='#6e7681', fg='white',
                              command=dialog.destroy, relief='flat', bd=0, 
                              cursor='hand2', width=12, height=2)
        cancel_btn.pack(side='left', padx=5)
        
        name_entry.focus()
    
    def join_room_dialog(self):
        """Diálogo para unirse a sala"""
        room_id = simpledialog.askstring("🚪 Unirse a Sala", 
                                        "Ingresa el ID de la sala:",
                                        parent=self.root)
        if room_id:
            self.send_command(f"/unirse {room_id.strip()}")
    
    def show_my_rooms(self):
        """Mostrar salas del usuario"""
        self.send_command("/mis_salas")
    
    def leave_room(self):
        """Salir de la sala actual"""
        self.send_command("/salir_sala")
        self.current_room = None
        self.update_room_info("📢 Chat Global", False)
    
    def send_command(self, command):
        """Enviar comando al servidor"""
        if not self.connected:
            return
        try:
            self.client.send(command.encode("utf-8"))
        except Exception:
            self.add_bubble_message("❌ Error enviando comando", "system")
    
    def update_room_info(self, room_name, in_room=True):
        """Actualizar información de sala en la UI"""
        self.room_info_label.config(text=f"🏠 {room_name}" if in_room else room_name)
        
        if in_room:
            self.leave_room_btn.pack(side='right', padx=15)
        else:
            self.leave_room_btn.pack_forget()

    def add_bubble_message(self, message, msg_type="received"):
        """Agregar mensaje como burbuja de chat"""
        # Frame para la burbuja
        bubble_frame = tk.Frame(self.scrollable_frame, bg='#0f1419')
        bubble_frame.pack(fill='x', padx=10, pady=5)
        
        # Determinar colores y alineación según el tipo
        if msg_type == "sent":
            bg_color = '#238636'
            fg_color = 'white'
            anchor = 'e'
            side = 'right'
        elif msg_type == "system":
            bg_color = '#6e7681'
            fg_color = 'white'
            anchor = 'center'
            side = 'top'
        else:  # received
            bg_color = '#1c2128'
            fg_color = '#f0f6fc'
            anchor = 'w'
            side = 'left'
        
        # Frame interno para la burbuja
        if msg_type == "system":
            inner_frame = tk.Frame(bubble_frame, bg='#0f1419')
            inner_frame.pack()
        else:
            inner_frame = tk.Frame(bubble_frame, bg='#0f1419')
            inner_frame.pack(anchor=anchor)
        
        # Label con el mensaje
        max_width = 50 if len(message) > 50 else len(message)
        message_label = tk.Label(inner_frame, text=message, 
                                font=self.message_font, bg=bg_color, fg=fg_color,
                                wraplength=400, justify='left', padx=15, pady=10,
                                relief='flat', bd=0)
        message_label.pack(side=side)
        
        # Timestamp pequeño
        if msg_type != "system":
            time_str = time.strftime("%H:%M")
            time_label = tk.Label(inner_frame, text=time_str, 
                                 font=self.small_font, fg='#6e7681', bg='#0f1419')
            if msg_type == "sent":
                time_label.pack(side='right', padx=(5,0))
            else:
                time_label.pack(side='left', padx=(0,5))
        
        # Auto-scroll al final
        self.root.after(10, self._scroll_to_bottom)
        
    def _scroll_to_bottom(self):
        """Hacer scroll automático al final"""
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        
    def start_receive_thread(self):
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
    # def receive_messages(self):
    #     while self.connected:
    #         try:
    #             message = self.client.recv(4096).decode("utf-8")
    #             if not message:
    #                 self.add_bubble_message("❌ Conexión cerrada por el servidor", "system")
    #                 self.connected = False
    #                 break
                    
    #             if message == "NICK":
    #                 self.client.send(self.nickname.encode("utf-8"))
    #                 continue
                
    #             self.process_received_message(message)
                
    #         except Exception:
    #             if self.connected:
    #                 self.add_bubble_message("⚠️ Error recibiendo datos del servidor", "system")
    #             break

    def receive_messages(self):
        while self.connected:
            try:
                data = self.client.recv(4096)
                if not data:
                    self.add_bubble_message("❌ Conexión cerrada por el servidor", "system")
                    self.connected = False
                    break

                # 🔐 Intentar descifrar el mensaje
                try:
                    message = decrypt_message(data)
                except Exception:
                    message = data.decode("utf-8")  # si no está cifrado

                self.process_received_message(message)
                
            except Exception:
                if self.connected:
                    self.add_bubble_message("⚠️ Error recibiendo datos del servidor", "system")
                break

                
    def process_received_message(self, message):
        """Procesar y mostrar mensaje recibido"""
        if "Te uniste a la sala:" in message:
            # Extract room name and update UI
            room_name = message.split("Te uniste a la sala: ")[1]
            self.current_room = room_name
            self.update_room_info(room_name, True)
            self.add_bubble_message(message, "system")
        elif "Saliste de la sala" in message:
            self.current_room = None
            self.update_room_info("📢 Chat Global", False)
            self.add_bubble_message(message, "system")
        elif "Sala creada:" in message:
            # Extract room ID for easy copying
            self.add_bubble_message(message + " (ID copiado al portapapeles)", "system")
            # Try to copy to clipboard
            try:
                room_id = message.split("ID: ")[1].split(")")[0]
                self.root.clipboard_clear()
                self.root.clipboard_append(room_id)
            except:
                pass
        elif message.startswith("[") or "se unió" in message or "se desconectó" in message or "salió" in message:
            self.add_bubble_message(message, "system")
        else:
            # Separar usuario y mensaje si es posible
            if ":" in message and not message.startswith("Error"):
                parts = message.split(":", 1)
                if len(parts) == 2:
                    user, msg = parts
                    if user.strip() == self.nickname:
                        return  # No mostrar nuestros propios mensajes aquí
                    formatted_msg = f"{user.strip()}: {msg.strip()}"
                    self.add_bubble_message(formatted_msg, "received")
                else:
                    self.add_bubble_message(message, "received")
            else:
                self.add_bubble_message(message, "system")
        
    # def send_message(self, event=None):
    #     if not self.connected:
    #         return
            
    #     msg = self.message_entry.get().strip()
    #     if not msg:
    #         return
            
    #     try:
    #         if msg.lower() == "/quit":
    #             self.disconnect()
    #             return
                
    #         self.add_bubble_message(f"Tú: {msg}", "sent")
            
    #         self.client.send(msg.encode("utf-8"))
    #         self.message_entry.delete(0, 'end')
            
    #     except Exception:
    #         self.add_bubble_message("❌ Error enviando mensaje", "system")
    def send_message(self, event=None):
        if not self.connected:
            return
            
        msg = self.message_entry.get().strip()
        if not msg:
            return
            
        try:
            if msg.lower() == "/quit":
                self.disconnect()
                return
                
            self.add_bubble_message(f"Tú: {msg}", "sent")
            
            # 🔐 Encriptar mensaje antes de enviarlo
            encrypted_msg = encrypt_message(msg)
            self.client.send(encrypted_msg)
            self.message_entry.delete(0, 'end')
            
        except Exception:
            self.add_bubble_message("❌ Error enviando mensaje", "system")
            
    def disconnect(self):
        if self.connected:
            try:
                self.client.send("/quit".encode("utf-8"))
            except Exception:
                pass
            self.client.close()
            self.connected = False
            
        self.show_login_menu()
        
    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            if self.connected:
                self.disconnect()

if __name__ == "__main__":
    app = ChatClient()
    app.run()
