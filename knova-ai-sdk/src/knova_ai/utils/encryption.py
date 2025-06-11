"""Encryption utilities for sensitive data"""

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption for sensitive data with persistent key management"""
    
    _instance: Optional["EncryptionManager"] = None
    _cipher: Optional[Fernet] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._cipher is None:
            self._initialize_cipher()
    
    def _initialize_cipher(self):
        """Initialize the cipher with a persistent key"""
        key = self._get_or_create_key()
        self._cipher = Fernet(key)
    
    def _get_key_path(self) -> Path:
        """Get the path to store the encryption key"""
        # Try environment variable first
        key_path = os.environ.get('KNOVA_ENCRYPTION_KEY_PATH')
        if key_path:
            return Path(key_path)
        
        # Default to user's home directory
        home = Path.home()
        knova_dir = home / '.knova'
        knova_dir.mkdir(exist_ok=True)
        
        # Set restrictive permissions on the directory (Unix-like systems)
        if hasattr(os, 'chmod'):
            os.chmod(knova_dir, 0o700)
        
        return knova_dir / 'encryption.key'
    
    def _get_or_create_key(self) -> bytes:
        """Get existing key or create a new one"""
        # First, check environment variable
        env_key = os.environ.get('KNOVA_ENCRYPTION_KEY')
        if env_key:
            try:
                # Validate the key
                key = base64.urlsafe_b64decode(env_key.encode())
                Fernet(key)  # This will raise an exception if invalid
                return key
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Check for key file
        key_path = self._get_key_path()
        
        if key_path.exists():
            try:
                with open(key_path, 'rb') as f:
                    key = f.read()
                # Validate the key
                Fernet(key)
                return key
            except Exception as e:
                logger.warning(f"Invalid encryption key in file {key_path}: {e}")
                # Backup the invalid key
                backup_path = key_path.with_suffix('.invalid')
                key_path.rename(backup_path)
                logger.info(f"Backed up invalid key to {backup_path}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save to file
        try:
            with open(key_path, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(key_path, 0o600)
            logger.info(f"Generated new encryption key at {key_path}")
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")
        
        return key
    
    def rotate_key(self, new_key: Optional[bytes] = None) -> bytes:
        """Rotate the encryption key
        
        Args:
            new_key: Optional new key to use. If not provided, generates a new one.
            
        Returns:
            The new encryption key
        """
        if new_key is None:
            new_key = Fernet.generate_key()
        else:
            # Validate the provided key
            try:
                Fernet(new_key)
            except Exception:
                raise ValueError("Invalid encryption key provided")
        
        # Save the new key
        key_path = self._get_key_path()
        
        # Backup old key
        if key_path.exists():
            backup_path = key_path.with_suffix('.backup')
            key_path.rename(backup_path)
            logger.info(f"Backed up old key to {backup_path}")
        
        # Write new key
        with open(key_path, 'wb') as f:
            f.write(new_key)
        
        # Set restrictive permissions
        if hasattr(os, 'chmod'):
            os.chmod(key_path, 0o600)
        
        # Update cipher
        self._cipher = Fernet(new_key)
        
        logger.info("Encryption key rotated successfully")
        return new_key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return data
        
        try:
            encrypted = self._cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Derive an encryption key from a password
        
        Args:
            password: The password to derive the key from
            salt: Optional salt. If not provided, generates a new one.
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return key, salt


# Singleton instance
_encryption_manager = EncryptionManager()


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using singleton encryption manager"""
    return _encryption_manager.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using singleton encryption manager"""
    return _encryption_manager.decrypt(encrypted_data)


def rotate_encryption_key(new_key: Optional[bytes] = None) -> bytes:
    """Rotate the encryption key
    
    Args:
        new_key: Optional new key to use. If not provided, generates a new one.
        
    Returns:
        The new encryption key
    """
    return _encryption_manager.rotate_key(new_key)