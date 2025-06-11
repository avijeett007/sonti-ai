"""Encryption utilities for sensitive data"""

from cryptography.fernet import Fernet
from typing import Optional


class EncryptionManager:
    """Manages encryption for sensitive data"""
    
    _instance: Optional["EncryptionManager"] = None
    _key: Optional[bytes] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._key is None:
            self._key = Fernet.generate_key()
            self._cipher = Fernet(self._key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        return self._cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        return self._cipher.decrypt(encrypted_data.encode()).decode()


# Singleton instance
_encryption_manager = EncryptionManager()


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using singleton encryption manager"""
    return _encryption_manager.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using singleton encryption manager"""
    return _encryption_manager.decrypt(encrypted_data)