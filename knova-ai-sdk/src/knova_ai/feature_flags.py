"""Feature flag system for license-based restrictions"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

from .license import LicenseInfo, LicenseTier

logger = logging.getLogger(__name__)


class Feature(str, Enum):
    """Available features that can be restricted by license tier"""
    # Agent features
    CREATE_AGENT = "create_agent"
    DELETE_AGENT = "delete_agent"
    UPDATE_AGENT = "update_agent"
    DEPLOY_AGENT = "deploy_agent"
    
    # Knowledge base features
    CREATE_KNOWLEDGE_BASE = "create_knowledge_base"
    UPLOAD_DOCUMENT = "upload_document"
    
    # API features
    API_CALLS = "api_calls"
    WEBHOOK_CALLS = "webhook_calls"
    
    # Voice features
    VOICE_MINUTES = "voice_minutes"
    TRANSCRIPTION = "transcription"
    
    # Advanced features
    CUSTOM_FUNCTIONS = "custom_functions"
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"
    ANALYTICS_ACCESS = "analytics_access"
    PRIORITY_SUPPORT = "priority_support"


class FeatureFlags:
    """Manages feature availability and usage limits based on license tier"""
    
    # Tier-based feature limits
    TIER_LIMITS = {
        LicenseTier.FREE: {
            "max_agents": 3,
            "max_api_calls_per_day": 1000,
            "max_storage_mb": 100,
            "max_voice_minutes_per_month": 60,
            "max_knowledge_bases": 1,
            "max_documents_per_kb": 10,
            "max_webhook_calls_per_day": 100,
            "custom_functions_allowed": False,
            "multi_agent_allowed": False,
            "analytics_access": False,
            "priority_support": False
        },
        LicenseTier.PRO: {
            "max_agents": 10,
            "max_api_calls_per_day": 10000,
            "max_storage_mb": 1000,
            "max_voice_minutes_per_month": 1000,
            "max_knowledge_bases": 5,
            "max_documents_per_kb": 100,
            "max_webhook_calls_per_day": 1000,
            "custom_functions_allowed": True,
            "multi_agent_allowed": True,
            "analytics_access": True,
            "priority_support": False
        },
        LicenseTier.ENTERPRISE: {
            "max_agents": -1,  # Unlimited
            "max_api_calls_per_day": -1,
            "max_storage_mb": -1,
            "max_voice_minutes_per_month": -1,
            "max_knowledge_bases": -1,
            "max_documents_per_kb": -1,
            "max_webhook_calls_per_day": -1,
            "custom_functions_allowed": True,
            "multi_agent_allowed": True,
            "analytics_access": True,
            "priority_support": True
        }
    }
    
    # Feature to limit mapping
    FEATURE_LIMIT_MAP = {
        Feature.CREATE_AGENT: "max_agents",
        Feature.API_CALLS: "max_api_calls_per_day",
        Feature.VOICE_MINUTES: "max_voice_minutes_per_month",
        Feature.CREATE_KNOWLEDGE_BASE: "max_knowledge_bases",
        Feature.UPLOAD_DOCUMENT: "max_documents_per_kb",
        Feature.WEBHOOK_CALLS: "max_webhook_calls_per_day",
        Feature.CUSTOM_FUNCTIONS: "custom_functions_allowed",
        Feature.MULTI_AGENT_COLLABORATION: "multi_agent_allowed",
        Feature.ANALYTICS_ACCESS: "analytics_access",
        Feature.PRIORITY_SUPPORT: "priority_support"
    }
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self._usage_cache: Dict[str, Dict[str, Any]] = {}
        
    def check_feature(self, feature: Feature, license_info: LicenseInfo) -> bool:
        """
        Check if a feature is available for the given license
        
        Args:
            feature: Feature to check
            license_info: License information
            
        Returns:
            True if feature is available, False otherwise
        """
        if not license_info or not license_info.valid:
            return False
            
        tier = LicenseTier(license_info.tier.upper())
        tier_limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS[LicenseTier.FREE])
        
        # Check if feature has a corresponding limit
        limit_key = self.FEATURE_LIMIT_MAP.get(feature)
        if not limit_key:
            # Feature not in map, assume it's available
            return True
            
        # Check boolean features
        if isinstance(tier_limits.get(limit_key), bool):
            return tier_limits.get(limit_key, False)
            
        # For numeric limits, just check if limit exists and is not 0
        limit = tier_limits.get(limit_key, 0)
        return limit != 0
        
    def get_usage_limits(self, tier: str) -> Dict[str, Any]:
        """Get all usage limits for a given tier"""
        tier_enum = LicenseTier(tier.upper())
        return self.TIER_LIMITS.get(tier_enum, self.TIER_LIMITS[LicenseTier.FREE]).copy()
        
    def check_usage_limit(
        self,
        feature: Feature,
        license_info: LicenseInfo,
        current_usage: Optional[int] = None
    ) -> tuple[bool, int, int]:
        """
        Check if usage is within limits
        
        Args:
            feature: Feature to check
            license_info: License information
            current_usage: Current usage count (will be fetched if not provided)
            
        Returns:
            Tuple of (within_limit, current_usage, limit)
        """
        if not license_info or not license_info.valid:
            return False, 0, 0
            
        tier = LicenseTier(license_info.tier.upper())
        tier_limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS[LicenseTier.FREE])
        
        limit_key = self.FEATURE_LIMIT_MAP.get(feature)
        if not limit_key:
            return True, 0, -1
            
        limit = tier_limits.get(limit_key, 0)
        
        # Unlimited
        if limit == -1:
            return True, current_usage or 0, -1
            
        # Get current usage if not provided
        if current_usage is None:
            current_usage = self.get_usage(feature, license_info.key)
            
        return current_usage < limit, current_usage, limit
        
    def track_usage(self, feature: Feature, license_key: str, amount: int = 1):
        """
        Track usage of a feature
        
        Args:
            feature: Feature being used
            license_key: License key
            amount: Usage amount to add
        """
        usage_key = self._get_usage_key(feature, license_key)
        
        # Get current usage
        current = self.get_usage(feature, license_key)
        new_usage = current + amount
        
        # Update cache
        if license_key not in self._usage_cache:
            self._usage_cache[license_key] = {}
        self._usage_cache[license_key][feature.value] = {
            'count': new_usage,
            'last_updated': datetime.now()
        }
        
        # Persist to storage if available
        if self.config_manager:
            self._persist_usage(usage_key, new_usage)
            
        logger.debug(f"Tracked usage for {feature.value}: {current} -> {new_usage}")
        
    def get_usage(self, feature: Feature, license_key: str) -> int:
        """
        Get current usage for a feature
        
        Args:
            feature: Feature to check
            license_key: License key
            
        Returns:
            Current usage count
        """
        # Check cache first
        if license_key in self._usage_cache:
            feature_usage = self._usage_cache[license_key].get(feature.value, {})
            if feature_usage:
                # Check if cache is recent (within last hour)
                if datetime.now() - feature_usage['last_updated'] < timedelta(hours=1):
                    return feature_usage['count']
                    
        # Load from storage if available
        if self.config_manager:
            usage_key = self._get_usage_key(feature, license_key)
            stored_usage = self.config_manager.get(usage_key)
            if stored_usage:
                return stored_usage.get('count', 0)
                
        return 0
        
    def reset_usage(self, feature: Feature, license_key: str):
        """Reset usage counter for a feature"""
        usage_key = self._get_usage_key(feature, license_key)
        
        # Clear cache
        if license_key in self._usage_cache:
            self._usage_cache[license_key].pop(feature.value, None)
            
        # Clear storage
        if self.config_manager:
            self.config_manager.delete(usage_key)
            
        logger.info(f"Reset usage counter for {feature.value}")
        
    def get_all_usage(self, license_key: str) -> Dict[str, int]:
        """Get all usage counters for a license"""
        all_usage = {}
        
        for feature in Feature:
            usage = self.get_usage(feature, license_key)
            if usage > 0:
                all_usage[feature.value] = usage
                
        return all_usage
        
    def _get_usage_key(self, feature: Feature, license_key: str) -> str:
        """Generate storage key for usage tracking"""
        # Include date for daily limits
        if feature in [Feature.API_CALLS, Feature.WEBHOOK_CALLS]:
            date_str = datetime.now().strftime("%Y-%m-%d")
            return f"usage_{license_key}_{feature.value}_{date_str}"
        # Include month for monthly limits
        elif feature == Feature.VOICE_MINUTES:
            month_str = datetime.now().strftime("%Y-%m")
            return f"usage_{license_key}_{feature.value}_{month_str}"
        # No time component for cumulative limits
        else:
            return f"usage_{license_key}_{feature.value}"
            
    def _persist_usage(self, usage_key: str, count: int):
        """Persist usage to storage"""
        if not self.config_manager:
            return
            
        usage_data = {
            'count': count,
            'last_updated': datetime.now().isoformat()
        }
        
        # Set TTL based on usage type
        if "_daily" in usage_key or any(d in usage_key for d in ["2024", "2025", "2026"]):
            # Daily counters expire after 2 days
            ttl = 2 * 24 * 3600
        elif "_monthly" in usage_key:
            # Monthly counters expire after 35 days
            ttl = 35 * 24 * 3600
        else:
            # Cumulative counters don't expire
            ttl = None
            
        self.config_manager.set(usage_key, usage_data, ttl)
        
    def check_and_track_usage(
        self,
        feature: Feature,
        license_info: LicenseInfo,
        amount: int = 1
    ) -> tuple[bool, str]:
        """
        Check if usage is within limits and track if allowed
        
        Args:
            feature: Feature to use
            license_info: License information
            amount: Usage amount
            
        Returns:
            Tuple of (allowed, message)
        """
        # First check if feature is available
        if not self.check_feature(feature, license_info):
            return False, f"Feature '{feature.value}' is not available in {license_info.tier} tier"
            
        # Check usage limit
        within_limit, current, limit = self.check_usage_limit(feature, license_info)
        
        if not within_limit:
            limit_type = self._get_limit_type(feature)
            return False, f"Usage limit exceeded for '{feature.value}': {current}/{limit} {limit_type}"
            
        # Track usage
        self.track_usage(feature, license_info.key, amount)
        
        return True, "Success"
        
    def _get_limit_type(self, feature: Feature) -> str:
        """Get human-readable limit type"""
        if feature in [Feature.API_CALLS, Feature.WEBHOOK_CALLS]:
            return "per day"
        elif feature == Feature.VOICE_MINUTES:
            return "per month"
        else:
            return "total"