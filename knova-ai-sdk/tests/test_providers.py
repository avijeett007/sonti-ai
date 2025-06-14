"""Tests for the AI provider abstraction framework"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from knova_ai.providers import (
    ProviderRegistry, ProviderType, ProviderCapability,
    create_provider, list_providers, register_provider,
    ProviderError, AuthenticationError, RateLimitError,
    OpenAILLMProvider, OpenAISTTProvider, OpenAITTSProvider,
    AzureOpenAILLMProvider,
    LiveKitProviderAdapter, LiveKitAgentConfig
)


class TestProviderRegistry:
    """Test provider registry functionality"""
    
    def test_singleton_registry(self):
        """Test that registry is a singleton"""
        registry1 = ProviderRegistry.get_instance()
        registry2 = ProviderRegistry.get_instance()
        assert registry1 is registry2
    
    def test_register_provider(self):
        """Test provider registration"""
        registry = ProviderRegistry.get_instance()
        
        # Mock provider class
        class MockLLMProvider:
            PROVIDER_NAME = "mock"
            SUPPORTED_MODELS = ["mock-model"]
            CAPABILITIES = [ProviderCapability.STREAMING]
            REQUIRED_CONFIG = ["api_key"]
            
        # Register provider
        register_provider("mock", ProviderType.LLM, MockLLMProvider)
        
        # Verify registration
        provider_info = registry.get_provider_info("mock", ProviderType.LLM)
        assert provider_info.name == "mock"
        assert provider_info.provider_type == ProviderType.LLM
        assert provider_info.provider_class == MockLLMProvider
    
    def test_list_providers(self):
        """Test listing providers"""
        # List all providers
        all_providers = list_providers()
        assert len(all_providers) > 0
        
        # List LLM providers only
        llm_providers = list_providers(ProviderType.LLM)
        assert all(p.provider_type == ProviderType.LLM for p in llm_providers)
        
        # Verify OpenAI is registered
        openai_providers = [p for p in llm_providers if p.name == "openai"]
        assert len(openai_providers) == 1
    
    def test_create_provider_missing_config(self):
        """Test creating provider with missing configuration"""
        with pytest.raises(ProviderError) as exc_info:
            create_provider("openai", ProviderType.LLM)  # Missing required api_key
        
        assert "Missing required configuration" in str(exc_info.value)


class TestOpenAIProviders:
    """Test OpenAI provider implementations"""
    
    @pytest.mark.asyncio
    async def test_openai_llm_provider_initialization(self):
        """Test OpenAI LLM provider initialization"""
        provider = OpenAILLMProvider(
            model="gpt-4",
            api_key="test-key",
            temperature=0.5
        )
        
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.5
        assert ProviderCapability.STREAMING in provider.capabilities
        assert ProviderCapability.FUNCTION_CALLING in provider.capabilities
    
    @pytest.mark.asyncio
    async def test_openai_llm_validation_no_key(self):
        """Test OpenAI LLM validation with no API key"""
        provider = OpenAILLMProvider(model="gpt-4", api_key="")
        
        with pytest.raises(AuthenticationError):
            await provider.validate_config()
    
    @pytest.mark.asyncio
    async def test_openai_llm_validation_invalid_model(self):
        """Test OpenAI LLM validation with invalid model"""
        provider = OpenAILLMProvider(model="invalid-model", api_key="test-key")
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.validate_config()
        
        assert "Unsupported model" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_openai_stt_provider(self):
        """Test OpenAI STT provider"""
        provider = OpenAISTTProvider(api_key="test-key", language="en")
        
        assert provider.model == "whisper-1"
        assert provider.language == "en"
        assert ProviderCapability.LANGUAGE_DETECTION in provider.capabilities
    
    @pytest.mark.asyncio
    async def test_openai_tts_provider(self):
        """Test OpenAI TTS provider"""
        provider = OpenAITTSProvider(
            api_key="test-key",
            voice="nova",
            model="tts-1-hd"
        )
        
        assert provider.model == "tts-1-hd"
        assert provider.voice == "nova"
        assert ProviderCapability.STREAMING in provider.capabilities


class TestAzureProviders:
    """Test Azure provider implementations"""
    
    @pytest.mark.asyncio
    async def test_azure_llm_provider(self):
        """Test Azure OpenAI LLM provider"""
        provider = AzureOpenAILLMProvider(
            model="gpt-4",
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment_name="test-deployment"
        )
        
        assert provider.endpoint == "https://test.openai.azure.com"
        assert provider.deployment_name == "test-deployment"
        assert ProviderCapability.STREAMING in provider.capabilities
    
    @pytest.mark.asyncio
    async def test_azure_llm_validation_missing_fields(self):
        """Test Azure validation with missing fields"""
        # Missing endpoint
        provider = AzureOpenAILLMProvider(
            model="gpt-4",
            api_key="test-key",
            endpoint="",
            deployment_name="test"
        )
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.validate_config()
        
        assert "endpoint is required" in str(exc_info.value)


class TestLiveKitAdapter:
    """Test LiveKit adapter functionality"""
    
    @pytest.mark.asyncio
    async def test_livekit_adapter_config(self):
        """Test LiveKit adapter configuration"""
        config = LiveKitAgentConfig(
            llm_provider="openai",
            llm_config={"model": "gpt-4", "api_key": "test-key"},
            stt_provider="openai",
            stt_config={"api_key": "test-key"},
            tts_provider="openai",
            tts_config={"api_key": "test-key"},
            agent_name="Test Agent",
            initial_prompt="You are a test assistant"
        )
        
        adapter = LiveKitProviderAdapter(config)
        assert adapter.config.agent_name == "Test Agent"
        assert adapter.config.llm_provider == "openai"
    
    @pytest.mark.asyncio
    async def test_livekit_adapter_initialization(self):
        """Test LiveKit adapter initialization"""
        config = LiveKitAgentConfig(
            llm_provider="openai",
            llm_config={"model": "gpt-4", "api_key": "test-key"},
            stt_provider="openai",
            stt_config={"api_key": "test-key"},
            tts_provider="openai",
            tts_config={"api_key": "test-key"}
        )
        
        adapter = LiveKitProviderAdapter(config)
        
        # Mock the provider creation to avoid actual API calls
        with patch('knova_ai.providers.registry.ProviderRegistry.create_provider') as mock_create:
            mock_llm = AsyncMock()
            mock_stt = AsyncMock()
            mock_tts = AsyncMock()
            
            mock_create.side_effect = [mock_llm, mock_stt, mock_tts]
            
            await adapter.initialize()
            
            assert adapter._llm_provider is not None
            assert adapter._stt_provider is not None
            assert adapter._tts_provider is not None


class TestProviderMetrics:
    """Test provider metrics tracking"""
    
    @pytest.mark.asyncio
    async def test_provider_metrics(self):
        """Test metrics tracking in providers"""
        provider = OpenAILLMProvider(model="gpt-4", api_key="test-key")
        
        # Check initial metrics
        assert provider.metrics.request_count == 0
        assert provider.metrics.error_count == 0
        assert provider.metrics.average_latency == 0.0
        assert provider.metrics.error_rate == 0.0
        
        # Simulate tracking metrics
        await provider._track_metrics(1.0, True, 100)
        
        assert provider.metrics.request_count == 1
        assert provider.metrics.error_count == 0
        assert provider.metrics.total_tokens == 100
        assert provider.metrics.average_latency == 1.0
    
    @pytest.mark.asyncio
    async def test_provider_health_check(self):
        """Test provider health check"""
        provider = OpenAILLMProvider(model="gpt-4", api_key="test-key")
        
        # Mock validate_config to avoid actual API calls
        provider.validate_config = AsyncMock(return_value=True)
        
        health = await provider.health_check()
        
        assert health["provider"] == "openai"
        assert health["type"] == "llm"
        assert health["healthy"] is True
        assert "metrics" in health
        assert "capabilities" in health


class TestBackwardCompatibility:
    """Test backward compatibility with legacy interface"""
    
    def test_legacy_llm_provider_create(self):
        """Test legacy LLMProvider.create method"""
        from knova_ai.providers.llm import LLMProvider
        
        # Should work with warning
        with pytest.warns(DeprecationWarning):
            provider = LLMProvider.create(
                "openai",
                "gpt-4",
                api_key="test-key"
            )
        
        assert hasattr(provider, "model")
        assert provider.model == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_legacy_generate_method(self):
        """Test legacy generate method"""
        from knova_ai.providers.llm import LLMProvider
        
        with pytest.warns(DeprecationWarning):
            provider = LLMProvider.create(
                "openai",
                "gpt-4",
                api_key="test-key"
            )
        
        # Mock the underlying generate method
        provider.provider.generate = AsyncMock(return_value="Test response")
        
        response = await provider.generate(
            prompt="You are a test assistant",
            user_input="Hello"
        )
        
        assert response == "Test response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])