"""Encryption utilities for Knova AI SDK"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """Generate encryption key from password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key
    

def encrypt_data(data: str, key: bytes) -> str:
    """Encrypt string data"""
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()
    

def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """Decrypt string data"""
    f = Fernet(key)
    decoded = base64.urlsafe_b64decode(encrypted_data)
    decrypted = f.decrypt(decoded)
    return decrypted.decode()