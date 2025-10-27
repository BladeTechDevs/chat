from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# === Generar claves RSA si no existen ===
def generate_keys():
    with open("private.pem", "wb") as f_private, open("public.pem", "wb") as f_public:
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        f_private.write(private_key)
        f_public.write(public_key)
    print("🔐 Claves RSA generadas: private.pem y public.pem")

# === Cargar claves ===
def load_keys():
    with open("private.pem", "rb") as f:
        private_key = RSA.import_key(f.read())
    with open("public.pem", "rb") as f:
        public_key = RSA.import_key(f.read())
    return private_key, public_key

# === Cifrar con clave pública ===
def encrypt_rsa(message: str, public_key) -> bytes:
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(message.encode())

# === Descifrar con clave privada ===
def decrypt_rsa(cipher_text: bytes, private_key) -> str:
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(cipher_text).decode()
