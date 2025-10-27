from cryptography.fernet import Fernet

# Clave secreta para cifrar y descifrar mensajes
# ⚠️ Guárdala en una variable de entorno en producción
SECRET_FERNET_KEY = Fernet.generate_key()
fernet = Fernet(SECRET_FERNET_KEY)

def encrypt_message(message: str) -> str:
    return fernet.encrypt(message.encode()).decode()

def decrypt_message(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()
