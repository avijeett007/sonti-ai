"""LLM provider abstraction for Knova AI - Legacy interface for backward compatibility"""

from typing import Dict, Any, Optional, List, Union, AsyncIterator
import warnings

from .base import ProviderType
from .registry import ProviderRegistry, create_provider
from .adapters import LiveKitProviderAdapter, LiveKitAgentConfig


class LLMProvider:
    """
    Legacy LLM provider interface for backward compatibility.
    New code should use the provider registry directly.
    """
    
    def __init__(self):
        warnings.warn(
            "Direct use of LLMProvider is deprecated. Use ProviderRegistry instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    async def generate(self, prompt: str, user_input: str, **kwargs) -> str:
        """Generate response from LLM"""
        # Convert to new message format
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
        return await self.generate_messages(messages, **kwargs)
    
    async def generate_messages(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response from messages - to be implemented by subclasses"""
        raise NotImplementedError
        
    @staticmethod
    def create(provider: str, model: str, **kwargs) -> "LLMProvider":
        """
        Factory method to create LLM provider.
        Legacy interface - new code should use ProviderRegistry.
        """
        # Add model to kwargs for new provider system
        kwargs["model"] = model
        
        # Create provider using registry
        provider_instance = create_provider(provider, ProviderType.LLM, **kwargs)
        
        # Wrap in legacy adapter
        return LegacyLLMAdapter(provider_instance)
            
    @staticmethod
    def create_livekit_llm(provider: str, model: str, **kwargs):
        """
        Create LiveKit-compatible LLM.
        Uses the new adapter system.
        """
        config = LiveKitAgentConfig(
            llm_provider=provider,
            llm_config={"model": model, **kwargs},
            stt_provider="openai",  # Default STT
            stt_config={"api_key": kwargs.get("api_key", "")},
            tts_provider="openai",  # Default TTS
            tts_config={"api_key": kwargs.get("api_key", "")}
        )
        
        adapter = LiveKitProviderAdapter(config)
        return adapter.get_llm()


class LegacyLLMAdapter(LLMProvider):
    """Adapter to make new providers work with legacy interface"""
    
    def __init__(self, provider):
        self.provider = provider
        self.model = provider.model
        
    async def generate(self, prompt: str, user_input: str, **kwargs) -> str:
        """Generate using legacy interface"""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
        return await self.generate_messages(messages, **kwargs)
    
    async def generate_messages(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate from messages"""
        result = await self.provider.generate(messages, **kwargs)
        
        # Handle streaming results
        if isinstance(result, AsyncIterator):
            chunks = []
            async for chunk in result:
                chunks.append(chunk)
            return "".join(chunks)
        
        return result


# Legacy provider classes for backward compatibility
class OpenAIProvider(LegacyLLMAdapter):
    """Legacy OpenAI provider"""
    def __init__(self, model: str, **kwargs):
        provider = create_provider("openai", ProviderType.LLM, model=model, **kwargs)
        super().__init__(provider)
        

class GoogleProvider(LegacyLLMAdapter):
    """Legacy Google provider"""
    def __init__(self, model: str, **kwargs):
        provider = create_provider("google", ProviderType.LLM, model=model, **kwargs)
        super().__init__(provider)
        

class AnthropicProvider(LegacyLLMAdapter):
    """Legacy Anthropic provider"""
    def __init__(self, model: str, **kwargs):
        provider = create_provider("anthropic", ProviderType.LLM, model=model, **kwargs)
        super().__init__(provider)
        

class AzureProvider(LegacyLLMAdapter):
    """Legacy Azure provider"""
    def __init__(self, model: str, **kwargs):
        provider = create_provider("azure", ProviderType.LLM, model=model, **kwargs)
        super().__init__(provider)
        

class AWSProvider(LegacyLLMAdapter):
    """Legacy AWS provider"""
    def __init__(self, model: str, **kwargs):
        provider = create_provider("aws", ProviderType.LLM, model=model, **kwargs)
        super().__init__(provider)