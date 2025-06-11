"""Configuration management for Knova AI SDK"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from cryptography.fernet import Fernet


class ConfigManager:
    """Manages local configuration and caching"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db_path = self.config_dir / "knova.db"
        self._init_db()
        
        # Initialize encryption
        self._init_encryption()
        
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS license_cache (
                    license_key TEXT PRIMARY KEY,
                    valid BOOLEAN,
                    tier TEXT,
                    features TEXT,
                    expires_at TIMESTAMP,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_cache (
                    agent_id TEXT PRIMARY KEY,
                    config TEXT,
                    deployment_info TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
    def _init_encryption(self):
        """Initialize encryption for sensitive data"""
        key_file = self.config_dir / ".key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self._key = f.read()
        else:
            self._key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self._key)
            # Set restrictive permissions
            key_file.chmod(0o600)
            
        self._cipher = Fernet(self._key)
        
    def get(self, key: str) -> Optional[Any]:
        """Get a configuration value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value, expires_at FROM config WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                value, expires_at = row
                if expires_at:
                    expires = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires:
                        # Expired, delete it
                        conn.execute("DELETE FROM config WHERE key = ?", (key,))
                        return None
                        
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
                    
        return None
        
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set a configuration value"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
            
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO config (key, value, expires_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value, expires_at))
            
    def delete(self, key: str):
        """Delete a configuration value"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM config WHERE key = ?", (key,))
            
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self._cipher.encrypt(data.encode()).decode()
        
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self._cipher.decrypt(encrypted_data.encode()).decode()
        
    def cache_license(
        self,
        license_key: str,
        valid: bool,
        tier: str,
        features: Dict[str, Any],
        expires_at: Optional[datetime] = None
    ):
        """Cache license information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO license_cache 
                (license_key, valid, tier, features, expires_at, cached_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                self.encrypt(license_key),
                valid,
                tier,
                json.dumps(features),
                expires_at
            ))
            
    def has_valid_cached_license(self, license_key: str) -> bool:
        """Check if we have a valid cached license"""
        encrypted_key = self.encrypt(license_key)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT valid, expires_at FROM license_cache 
                WHERE license_key = ?
            """, (encrypted_key,))
            row = cursor.fetchone()
            
            if row:
                valid, expires_at = row
                if expires_at:
                    expires = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires:
                        return False
                return bool(valid)
                
        return False
        
    def cache_agent_config(self, agent_id: str, config: Dict[str, Any]):
        """Cache agent configuration"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO agent_cache 
                (agent_id, config, cached_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (agent_id, json.dumps(config)))
            
    def get_cached_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get cached agent configuration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT config FROM agent_cache WHERE agent_id = ?",
                (agent_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
                
        return None