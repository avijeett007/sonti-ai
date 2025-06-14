"""License validation for Knova AI SDK"""

import asyncio
import hashlib
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from enum import Enum

import aiohttp
from pydantic import BaseModel


class LicenseTier(str, Enum):
    """Available license tiers"""
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class LicenseInfo(BaseModel):
    """License information model"""
    key: str
    valid: bool
    tier: str
    expires_at: Optional[datetime] = None
    features: Dict[str, Any] = {}
    usage_limits: Dict[str, int] = {}
    validation_timestamp: Optional[datetime] = None
    

class LicenseValidator:
    """Handles license key validation"""
    
    # License format: KNOVA-{tier}-{uuid}-{checksum}
    LICENSE_PATTERN = re.compile(r'^KNOVA-([A-Z]+)-([a-f0-9-]+)-([a-f0-9]{8})$')
    
    # Tier-based cache durations (in hours)
    CACHE_DURATIONS = {
        LicenseTier.FREE: 24,
        LicenseTier.PRO: 6,
        LicenseTier.ENTERPRISE: 12
    }
    
    # Grace period settings
    OFFLINE_CACHE_VALIDITY_DAYS = 30
    GRACE_PERIOD_DAYS = 7
    
    def __init__(self, api_url: str, license_key: str, config_manager=None):
        self.api_url = api_url
        self.license_key = license_key
        self.config_manager = config_manager
        self._cache: Optional[LicenseInfo] = None
        self._cache_expires: Optional[datetime] = None
        self._validation_history: list = []
        self._max_retries = 3
        self._base_delay = 1  # Base delay for exponential backoff in seconds
    
    @staticmethod
    def validate_license_format(license_key: str) -> bool:
        """
        Validate license key format
        
        Args:
            license_key: License key to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not license_key:
            return False
        return bool(LicenseValidator.LICENSE_PATTERN.match(license_key))
    
    @staticmethod
    def extract_license_components(license_key: str) -> Optional[Dict[str, str]]:
        """
        Extract components from license key
        
        Args:
            license_key: License key to parse
            
        Returns:
            Dictionary with tier, uuid, and checksum or None if invalid
        """
        match = LicenseValidator.LICENSE_PATTERN.match(license_key)
        if not match:
            return None
            
        return {
            'tier': match.group(1),
            'uuid': match.group(2),
            'checksum': match.group(3)
        }
    
    @staticmethod
    def calculate_checksum(license_key: str) -> str:
        """
        Calculate checksum for license key validation
        
        Args:
            license_key: License key without checksum
            
        Returns:
            8-character checksum
        """
        # Remove existing checksum if present
        parts = license_key.split('-')
        if len(parts) > 3:
            license_key = '-'.join(parts[:-1])
            
        # Calculate SHA256 and take first 8 characters
        hash_obj = hashlib.sha256(license_key.encode())
        return hash_obj.hexdigest()[:8]
    
    def verify_checksum(self, license_key: str) -> bool:
        """
        Verify license key checksum
        
        Args:
            license_key: Complete license key with checksum
            
        Returns:
            True if checksum is valid, False otherwise
        """
        components = self.extract_license_components(license_key)
        if not components:
            return False
            
        # Reconstruct key without checksum
        key_without_checksum = f"KNOVA-{components['tier']}-{components['uuid']}"
        expected_checksum = self.calculate_checksum(key_without_checksum)
        
        return components['checksum'] == expected_checksum
        
    async def validate(self) -> bool:
        """
        Validate license key with the API
        
        Returns:
            True if license is valid, False otherwise
        """
        # First validate format and checksum
        if not self.validate_license_format(self.license_key):
            self._record_validation_attempt(False, "Invalid license format")
            return False
            
        if not self.verify_checksum(self.license_key):
            self._record_validation_attempt(False, "Invalid checksum")
            return False
        
        # Check memory cache first
        if self._is_cache_valid():
            self._record_validation_attempt(True, "Memory cache hit")
            return self._cache.valid
        
        # Check persistent cache if config manager is available
        if self.config_manager and self._check_persistent_cache():
            self._record_validation_attempt(True, "Persistent cache hit")
            return self._cache.valid
            
        # Attempt API validation with retry logic
        for attempt in range(self._max_retries):
            try:
                success = await self._validate_with_api()
                if success:
                    self._record_validation_attempt(True, "API validation successful")
                    return True
                else:
                    self._record_validation_attempt(False, "API validation failed")
                    return False
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Calculate exponential backoff delay
                if attempt < self._max_retries - 1:
                    delay = self._base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    # Last attempt failed, check for grace period
                    self._record_validation_attempt(False, f"API unreachable: {str(e)}")
                    return self._check_grace_period()
                    
        return False
    
    async def _validate_with_api(self) -> bool:
        """Perform actual API validation"""
        connector = aiohttp.TCPConnector(limit_per_host=10)  # Connection pooling
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.post(
                f"{self.api_url}/v1/auth/license",
                json={"license_key": self.license_key},
                headers={"User-Agent": "Knova-AI-SDK/1.0"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Extract tier for cache duration
                    tier = data.get('tier', 'FREE').upper()
                    cache_hours = self.CACHE_DURATIONS.get(
                        LicenseTier(tier), 
                        self.CACHE_DURATIONS[LicenseTier.FREE]
                    )
                    
                    # Update cache
                    self._cache = LicenseInfo(**data)
                    self._cache.validation_timestamp = datetime.now()
                    self._cache_expires = datetime.now() + timedelta(hours=cache_hours)
                    
                    # Store in persistent cache if available
                    if self.config_manager:
                        self._store_persistent_cache()
                        
                    return True
                elif response.status == 401:
                    # Invalid license
                    self._cache = None
                    self._cache_expires = None
                    return False
                else:
                    # Server error, don't invalidate cache
                    raise aiohttp.ClientError(f"Server returned {response.status}")
    
    def _is_cache_valid(self) -> bool:
        """Check if memory cache is valid"""
        return (
            self._cache is not None 
            and self._cache_expires is not None 
            and datetime.now() < self._cache_expires
        )
    
    def _check_persistent_cache(self) -> bool:
        """Check and load from persistent cache"""
        if not self.config_manager:
            return False
            
        cache_data = self.config_manager.get(f"license_cache_{self.license_key}")
        if not cache_data:
            return False
            
        try:
            # Load cache data
            self._cache = LicenseInfo(**cache_data['info'])
            cache_timestamp = datetime.fromisoformat(cache_data['timestamp'])
            
            # Check if cache is within validity period
            cache_age = datetime.now() - cache_timestamp
            if cache_age.days <= self.OFFLINE_CACHE_VALIDITY_DAYS:
                # Calculate appropriate cache expiry
                tier = self._cache.tier.upper()
                cache_hours = self.CACHE_DURATIONS.get(
                    LicenseTier(tier),
                    self.CACHE_DURATIONS[LicenseTier.FREE]
                )
                self._cache_expires = cache_timestamp + timedelta(hours=cache_hours)
                return True
                
        except Exception:
            pass
            
        return False
    
    def _store_persistent_cache(self):
        """Store license info in persistent cache"""
        if not self.config_manager or not self._cache:
            return
            
        cache_data = {
            'info': self._cache.dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store with extended TTL for offline support
        ttl_seconds = self.OFFLINE_CACHE_VALIDITY_DAYS * 24 * 3600
        self.config_manager.set(
            f"license_cache_{self.license_key}",
            cache_data,
            ttl_seconds
        )
    
    def _check_grace_period(self) -> bool:
        """Check if license is within grace period"""
        if not self._cache:
            return False
            
        # Check if we have a cached license and it's within grace period
        if self._cache.validation_timestamp:
            time_since_validation = datetime.now() - self._cache.validation_timestamp
            if time_since_validation.days <= self.GRACE_PERIOD_DAYS:
                return self._cache.valid
                
        return False
    
    def _record_validation_attempt(self, success: bool, reason: str):
        """Record validation attempt for monitoring"""
        attempt = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'reason': reason,
            'license_key': self.license_key[:20] + '...' if len(self.license_key) > 20 else self.license_key
        }
        
        self._validation_history.append(attempt)
        
        # Keep only last 100 attempts
        if len(self._validation_history) > 100:
            self._validation_history = self._validation_history[-100:]
            
    async def get_license_info(self) -> Optional[LicenseInfo]:
        """Get detailed license information"""
        if await self.validate():
            return self._cache
        return None
        
    def is_free_tier(self) -> bool:
        """Check if this is a free tier license"""
        if self._cache:
            return self._cache.tier.upper() == LicenseTier.FREE.value
        return True  # Default to free tier restrictions
    
    def get_tier(self) -> str:
        """Get current license tier"""
        if self._cache:
            return self._cache.tier.upper()
        
        # Try to extract from license key
        components = self.extract_license_components(self.license_key)
        if components:
            return components['tier']
            
        return LicenseTier.FREE.value
    
    def get_validation_history(self, limit: int = 10) -> list:
        """Get recent validation history"""
        return self._validation_history[-limit:]
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get current cache status information"""
        status = {
            'has_cache': self._cache is not None,
            'cache_valid': self._is_cache_valid(),
            'cache_expires': self._cache_expires.isoformat() if self._cache_expires else None,
            'tier': self.get_tier(),
            'grace_period_active': False
        }
        
        if self._cache and self._cache.validation_timestamp:
            time_since_validation = datetime.now() - self._cache.validation_timestamp
            status['days_since_validation'] = time_since_validation.days
            status['grace_period_active'] = (
                time_since_validation.days <= self.GRACE_PERIOD_DAYS
                and time_since_validation.days > 0
            )
            
        return status
    
    def should_revalidate(self) -> bool:
        """Check if license should be revalidated based on tier"""
        if not self._cache or not self._cache_expires:
            return True
            
        # Check if cache has expired
        if datetime.now() >= self._cache_expires:
            return True
            
        # For non-free tiers, check if we're approaching expiry
        tier = self.get_tier()
        if tier != LicenseTier.FREE.value:
            time_until_expiry = self._cache_expires - datetime.now()
            cache_duration_hours = self.CACHE_DURATIONS.get(
                LicenseTier(tier),
                self.CACHE_DURATIONS[LicenseTier.FREE]
            )
            
            # Revalidate if we're in the last 10% of cache duration
            threshold = timedelta(hours=cache_duration_hours * 0.1)
            if time_until_expiry <= threshold:
                return True
                
        return False