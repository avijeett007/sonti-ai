"""Tests for license validation system"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

from knova_ai.license import LicenseValidator, LicenseInfo, LicenseTier
from knova_ai.license_validator import LicenseBackgroundValidator
from knova_ai.feature_flags import FeatureFlags, Feature
from knova_ai.usage_tracker import UsageTracker
from knova_ai.config import ConfigManager


class TestLicenseFormatValidation:
    """Test license key format validation and checksum"""
    
    def test_valid_license_format(self):
        """Test valid license format"""
        valid_keys = [
            "KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-12345678",
            "KNOVA-PRO-123e4567-e89b-12d3-a456-426614174000-abcdef12",
            "KNOVA-ENTERPRISE-987e6543-a21b-34c5-d678-912345678901-87654321"
        ]
        
        for key in valid_keys:
            assert LicenseValidator.validate_license_format(key) is True
            
    def test_invalid_license_format(self):
        """Test invalid license formats"""
        invalid_keys = [
            "",
            "INVALID-KEY",
            "KNOVA-INVALID-TIER-uuid-checksum",
            "KNOVA-FREE-not-a-uuid-12345678",
            "KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000",  # Missing checksum
            "KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-short",  # Short checksum
        ]
        
        for key in invalid_keys:
            assert LicenseValidator.validate_license_format(key) is False
            
    def test_extract_license_components(self):
        """Test extracting components from license key"""
        key = "KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000-12345678"
        components = LicenseValidator.extract_license_components(key)
        
        assert components is not None
        assert components['tier'] == 'PRO'
        assert components['uuid'] == '550e8400-e29b-41d4-a716-446655440000'
        assert components['checksum'] == '12345678'
        
    def test_checksum_calculation(self):
        """Test checksum calculation"""
        key_without_checksum = "KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000"
        checksum = LicenseValidator.calculate_checksum(key_without_checksum)
        
        assert isinstance(checksum, str)
        assert len(checksum) == 8
        
    def test_checksum_verification(self):
        """Test checksum verification"""
        # Create a key with correct checksum
        key_without_checksum = "KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000"
        checksum = LicenseValidator.calculate_checksum(key_without_checksum)
        valid_key = f"{key_without_checksum}-{checksum}"
        
        validator = LicenseValidator("https://api.knova.ai", valid_key)
        assert validator.verify_checksum(valid_key) is True
        
        # Test with invalid checksum
        invalid_key = f"{key_without_checksum}-wrongsum"
        assert validator.verify_checksum(invalid_key) is False


class TestLicenseValidation:
    """Test license validation with API"""
    
    @pytest.mark.asyncio
    async def test_successful_validation(self):
        """Test successful license validation"""
        license_key = "KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000-12345678"
        validator = LicenseValidator("https://api.knova.ai", license_key)
        
        # Mock the API response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'key': license_key,
                'valid': True,
                'tier': 'PRO',
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
                'features': {'max_agents': 10}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await validator.validate()
            assert result is True
            
            # Check cache
            assert validator._cache is not None
            assert validator._cache.valid is True
            assert validator._cache.tier == 'PRO'
            
    @pytest.mark.asyncio
    async def test_invalid_license_validation(self):
        """Test invalid license validation"""
        license_key = "KNOVA-FREE-invalid-uuid-wrongsum"
        validator = LicenseValidator("https://api.knova.ai", license_key)
        
        result = await validator.validate()
        assert result is False  # Should fail format validation
        
    @pytest.mark.asyncio
    async def test_validation_with_retry(self):
        """Test validation with retry on network error"""
        license_key = "KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000-12345678"
        # Calculate correct checksum
        key_without_checksum = "KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000"
        checksum = LicenseValidator.calculate_checksum(key_without_checksum)
        license_key = f"{key_without_checksum}-{checksum}"
        
        validator = LicenseValidator("https://api.knova.ai", license_key)
        validator._max_retries = 3
        
        # Mock API failures then success
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                raise aiohttp.ClientError("Network error")
            
            # Success on third attempt
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'key': license_key,
                'valid': True,
                'tier': 'PRO'
            })
            return mock_response
            
        with patch('aiohttp.ClientSession.post', new=mock_post):
            with patch('asyncio.sleep'):  # Skip actual delays
                result = await validator.validate()
                assert result is True
                assert call_count == 3
                
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test validation returns from cache"""
        license_key = "KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000-12345678"
        validator = LicenseValidator("https://api.knova.ai", license_key)
        
        # Set up cache
        validator._cache = LicenseInfo(
            key=license_key,
            valid=True,
            tier='PRO',
            validation_timestamp=datetime.now()
        )
        validator._cache_expires = datetime.now() + timedelta(hours=1)
        
        # Validate - should use cache
        with patch('aiohttp.ClientSession.post') as mock_post:
            result = await validator.validate()
            assert result is True
            mock_post.assert_not_called()  # Should not make API call


class TestBackgroundValidator:
    """Test background license validation"""
    
    @pytest.mark.asyncio
    async def test_background_validator_start_stop(self):
        """Test starting and stopping background validator"""
        license_key = "KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000-12345678"
        validator = LicenseValidator("https://api.knova.ai", license_key)
        bg_validator = LicenseBackgroundValidator(validator)
        
        # Start validator
        bg_validator.start()
        assert bg_validator.is_running() is True
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Stop validator
        bg_validator.stop()
        await asyncio.sleep(0.1)
        assert bg_validator.is_running() is False
        
    def test_validation_intervals(self):
        """Test tier-based validation intervals"""
        license_key = "KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-12345678"
        validator = LicenseValidator("https://api.knova.ai", license_key)
        bg_validator = LicenseBackgroundValidator(validator)
        
        assert bg_validator.VALIDATION_INTERVALS[LicenseTier.FREE] == 24 * 3600
        assert bg_validator.VALIDATION_INTERVALS[LicenseTier.PRO] == 6 * 3600
        assert bg_validator.VALIDATION_INTERVALS[LicenseTier.ENTERPRISE] == 12 * 3600


class TestFeatureFlags:
    """Test feature flag system"""
    
    def test_check_feature_availability(self):
        """Test checking feature availability by tier"""
        flags = FeatureFlags()
        
        # Free tier license
        free_license = LicenseInfo(
            key="free-key",
            valid=True,
            tier="FREE"
        )
        
        assert flags.check_feature(Feature.CREATE_AGENT, free_license) is True
        assert flags.check_feature(Feature.CUSTOM_FUNCTIONS, free_license) is False
        assert flags.check_feature(Feature.MULTI_AGENT_COLLABORATION, free_license) is False
        
        # Pro tier license
        pro_license = LicenseInfo(
            key="pro-key",
            valid=True,
            tier="PRO"
        )
        
        assert flags.check_feature(Feature.CREATE_AGENT, pro_license) is True
        assert flags.check_feature(Feature.CUSTOM_FUNCTIONS, pro_license) is True
        assert flags.check_feature(Feature.MULTI_AGENT_COLLABORATION, pro_license) is True
        assert flags.check_feature(Feature.PRIORITY_SUPPORT, pro_license) is False
        
    def test_usage_limits(self):
        """Test getting usage limits by tier"""
        flags = FeatureFlags()
        
        free_limits = flags.get_usage_limits("FREE")
        assert free_limits['max_agents'] == 3
        assert free_limits['max_api_calls_per_day'] == 1000
        
        pro_limits = flags.get_usage_limits("PRO")
        assert pro_limits['max_agents'] == 10
        assert pro_limits['max_api_calls_per_day'] == 10000
        
        enterprise_limits = flags.get_usage_limits("ENTERPRISE")
        assert enterprise_limits['max_agents'] == -1  # Unlimited
        
    def test_check_usage_limit(self):
        """Test checking usage against limits"""
        flags = FeatureFlags()
        
        free_license = LicenseInfo(
            key="free-key",
            valid=True,
            tier="FREE"
        )
        
        # Check with no usage
        within_limit, current, limit = flags.check_usage_limit(
            Feature.CREATE_AGENT,
            free_license,
            current_usage=0
        )
        assert within_limit is True
        assert current == 0
        assert limit == 3
        
        # Check at limit
        within_limit, current, limit = flags.check_usage_limit(
            Feature.CREATE_AGENT,
            free_license,
            current_usage=3
        )
        assert within_limit is False
        assert current == 3
        assert limit == 3
        
    def test_track_usage(self):
        """Test usage tracking"""
        flags = FeatureFlags()
        license_key = "test-key"
        
        # Track usage
        flags.track_usage(Feature.API_CALLS, license_key, 5)
        
        # Check usage
        usage = flags.get_usage(Feature.API_CALLS, license_key)
        assert usage == 5
        
        # Track more usage
        flags.track_usage(Feature.API_CALLS, license_key, 3)
        usage = flags.get_usage(Feature.API_CALLS, license_key)
        assert usage == 8


class TestUsageTracker:
    """Test usage tracking and analytics"""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create usage tracker with temp config"""
        config = ConfigManager(tmp_path)
        return UsageTracker(config)
        
    def test_track_event(self, tracker):
        """Test tracking usage events"""
        tracker.track_event('test_event', 'license-key', {'data': 'value'})
        
        assert len(tracker._metrics_buffer) == 1
        event = tracker._metrics_buffer[0]
        assert event['event_type'] == 'test_event'
        assert 'timestamp' in event
        assert event['metadata']['data'] == 'value'
        
    def test_track_api_call(self, tracker):
        """Test tracking API calls"""
        tracker.track_api_call(
            endpoint='/v1/agents',
            method='POST',
            license_key='test-key',
            response_time_ms=150,
            status_code=200
        )
        
        assert len(tracker._metrics_buffer) == 1
        event = tracker._metrics_buffer[0]
        assert event['event_type'] == 'api_call'
        assert event['metadata']['endpoint'] == '/v1/agents'
        assert event['metadata']['response_time_ms'] == 150
        
    def test_get_usage_summary(self, tracker):
        """Test getting usage summary"""
        license_key = 'test-key'
        
        # Track some events
        tracker.track_api_call('/v1/agents', 'GET', license_key, 100, 200)
        tracker.track_api_call('/v1/agents', 'POST', license_key, 200, 201)
        tracker.track_voice_usage('session-1', license_key, 120, 'deepgram')
        
        # Force flush
        tracker._flush_metrics()
        
        # Get summary
        summary = tracker.get_usage_summary(license_key, 1)
        
        assert summary['total_events'] == 3
        assert summary['api_calls']['total'] == 2
        assert summary['api_calls']['avg_response_time_ms'] == 150.0
        assert summary['voice']['total_minutes'] == 2.0
        assert summary['voice']['sessions'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])