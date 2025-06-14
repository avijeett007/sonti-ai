"""Provider abstractions for Knova AI"""

# Legacy imports for backward compatibility
from .llm import LLMProvider
from .stt import STTProvider
from .tts import TTSProvider

# New provider system imports
from .base import (
    BaseProvider, BaseLLMProvider, BaseSTTProvider, BaseTTSProvider,
    ProviderType, ProviderCapability, ProviderError, RateLimitError, AuthenticationError
)
from .registry import (
    ProviderRegistry, ProviderInfo, register_provider, create_provider, list_providers
)
from .adapters import LiveKitProviderAdapter, LiveKitAgentConfig, create_livekit_agent

# Import provider implementations
from .openai import OpenAILLMProvider, OpenAISTTProvider, OpenAITTSProvider
from .azure import AzureOpenAILLMProvider, AzureSTTProvider, AzureTTSProvider

__all__ = [
    # Legacy exports
    "LLMProvider", "STTProvider", "TTSProvider",
    
    # Base classes
    "BaseProvider", "BaseLLMProvider", "BaseSTTProvider", "BaseTTSProvider",
    
    # Enums and types
    "ProviderType", "ProviderCapability",
    
    # Exceptions
    "ProviderError", "RateLimitError", "AuthenticationError",
    
    # Registry
    "ProviderRegistry", "ProviderInfo", "register_provider", "create_provider", "list_providers",
    
    # Adapters
    "LiveKitProviderAdapter", "LiveKitAgentConfig", "create_livekit_agent",
    
    # Provider implementations
    "OpenAILLMProvider", "OpenAISTTProvider", "OpenAITTSProvider",
    "AzureOpenAILLMProvider", "AzureSTTProvider", "AzureTTSProvider",
]

# Register built-in providers
def _register_builtin_providers():
    """Register all built-in providers with the registry"""
    registry = ProviderRegistry.get_instance()
    
    # OpenAI providers
    registry.register_provider("openai", ProviderType.LLM, OpenAILLMProvider)
    registry.register_provider("openai", ProviderType.STT, OpenAISTTProvider)
    registry.register_provider("openai", ProviderType.TTS, OpenAITTSProvider)
    
    # Azure providers
    registry.register_provider("azure", ProviderType.LLM, AzureOpenAILLMProvider)
    registry.register_provider("azure", ProviderType.STT, AzureSTTProvider)
    registry.register_provider("azure", ProviderType.TTS, AzureTTSProvider)

# Register providers on import
_register_builtin_providers()