"""Tests for license validation"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from knova_ai.license import LicenseValidator, LicenseInfo


@pytest.mark.asyncio
async def test_license_validation_success():
    """Test successful license validation"""
    validator = LicenseValidator("https://api.test.com", "valid-key")
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "key": "valid-key",
            "valid": True,
            "tier": "free",
            "features": {}
        })
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        result = await validator.validate()
        assert result is True
        

@pytest.mark.asyncio
async def test_license_validation_failure():
    """Test failed license validation"""
    validator = LicenseValidator("https://api.test.com", "invalid-key")
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        result = await validator.validate()
        assert result is False
        

@pytest.mark.asyncio
async def test_license_caching():
    """Test license result caching"""
    validator = LicenseValidator("https://api.test.com", "valid-key")
    
    # Set cache manually
    validator._cache = LicenseInfo(
        key="valid-key",
        valid=True,
        tier="free",
        features={}
    )
    validator._cache_expires = datetime.now() + timedelta(hours=1)
    
    # Should return cached result without making API call
    result = await validator.validate()
    assert result is True