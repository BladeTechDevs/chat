import hashlib
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA

def sha256_hash(data: str) -> str:
    """Devuelve el hash SHA-256 en hexadecimal"""
    return hashlib.sha256(data.encode()).hexdigest()

def sign_message(message: str, private_key: RSA.RsaKey) -> bytes:
    """Firma el hash del mensaje con la clave privada RSA"""
    h = hashlib.sha256(message.encode()).digest()
    signer = pkcs1_15.new(private_key)
    signature = signer.sign(RSA.import_key(private_key.export_key()))
    return signature

def verify_signature(message: str, signature: bytes, public_key: RSA.RsaKey) -> bool:
    """Verifica la firma de un mensaje con la clave pública RSA"""
    try:
        h = hashlib.sha256(message.encode()).digest()
        pkcs1_15.new(public_key).verify(RSA.import_key(public_key.export_key()), h)
        return True
    except (ValueError, TypeError):
        return False
