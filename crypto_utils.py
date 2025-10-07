from cryptography.fernet import Fernet

# Cambia esta clave por una generada y guárdala de forma segura
FERNET_KEY = b'Az6EWuucD4fjCgopkTUM-wwdqLcVtw8HXL7L3LZkFOs='  # Reemplaza por la clave generada

cipher = Fernet(FERNET_KEY)

def encrypt_message(message: str) -> bytes:
    return cipher.encrypt(message.encode('utf-8'))

def decrypt_message(token: bytes) -> str:
    return cipher.decrypt(token).decode('utf-8')