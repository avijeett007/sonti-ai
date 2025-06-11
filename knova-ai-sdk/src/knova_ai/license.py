"""License validation for Knova AI SDK"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import aiohttp
from pydantic import BaseModel


class LicenseInfo(BaseModel):
    """License information model"""
    key: str
    valid: bool
    tier: str
    expires_at: Optional[datetime] = None
    features: Dict[str, Any] = {}
    

class LicenseValidator:
    """Handles license key validation"""
    
    def __init__(self, api_url: str, license_key: str):
        self.api_url = api_url
        self.license_key = license_key
        self._cache: Optional[LicenseInfo] = None
        self._cache_expires: Optional[datetime] = None
        
    async def validate(self) -> bool:
        """
        Validate license key with the API
        
        Returns:
            True if license is valid, False otherwise
        """
        # Check cache first
        if self._cache and self._cache_expires and datetime.now() < self._cache_expires:
            return self._cache.valid
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/auth/license",
                    json={"license_key": self.license_key},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._cache = LicenseInfo(**data)
                        # Cache for 1 hour
                        self._cache_expires = datetime.now() + timedelta(hours=1)
                        return self._cache.valid
                    else:
                        return False
                        
        except (aiohttp.ClientError, asyncio.TimeoutError):
            # If we can't reach the API, check if we have a valid cached license
            if self._cache:
                return self._cache.valid
            return False
            
    async def get_license_info(self) -> Optional[LicenseInfo]:
        """Get detailed license information"""
        if await self.validate():
            return self._cache
        return None
        
    def is_free_tier(self) -> bool:
        """Check if this is a free tier license"""
        if self._cache:
            return self._cache.tier == "free"
        return True  # Default to free tier restrictions