"""STT provider abstraction for Knova AI"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class STTProvider(ABC):
    """Base class for STT providers"""
    
    @abstractmethod
    async def transcribe(self, audio_data: bytes, **kwargs) -> str:
        """Transcribe audio to text"""
        pass
        
    @staticmethod
    def create(provider: str, **kwargs) -> "STTProvider":
        """Factory method to create STT provider"""
        if provider == "deepgram":
            return DeepgramProvider(**kwargs)
        elif provider == "openai":
            return OpenAISTTProvider(**kwargs)
        elif provider == "google":
            return GoogleSTTProvider(**kwargs)
        elif provider == "azure":
            return AzureSTTProvider(**kwargs)
        else:
            raise ValueError(f"Unknown STT provider: {provider}")
            
    @staticmethod
    def create_livekit_stt(provider: str, **kwargs):
        """Create LiveKit-compatible STT"""
        if provider == "deepgram":
            from livekit.plugins import deepgram
            return deepgram.STT(**kwargs)
        elif provider == "openai":
            from livekit.plugins import openai
            return openai.STT(**kwargs)
        elif provider == "google":
            from livekit.plugins import google
            return google.STT(**kwargs)
        else:
            raise ValueError(f"Provider {provider} not yet supported for LiveKit STT")
            

class DeepgramProvider(STTProvider):
    """Deepgram STT provider"""
    
    def __init__(self, **kwargs):
        self.api_key = kwargs.get("api_key")
        self.model = kwargs.get("model", "nova-2")
        self.language = kwargs.get("language", "en")
        
    async def transcribe(self, audio_data: bytes, **kwargs) -> str:
        # Simplified for now
        return "Transcribed text from Deepgram"
        

class OpenAISTTProvider(STTProvider):
    """OpenAI Whisper STT provider"""
    
    def __init__(self, **kwargs):
        self.api_key = kwargs.get("api_key")
        self.model = kwargs.get("model", "whisper-1")
        
    async def transcribe(self, audio_data: bytes, **kwargs) -> str:
        # Simplified for now
        return "Transcribed text from OpenAI Whisper"
        

class GoogleSTTProvider(STTProvider):
    """Google Cloud STT provider"""
    
    def __init__(self, **kwargs):
        self.credentials = kwargs.get("credentials")
        self.language_code = kwargs.get("language_code", "en-US")
        
    async def transcribe(self, audio_data: bytes, **kwargs) -> str:
        # Simplified for now
        return "Transcribed text from Google Cloud STT"
        

class AzureSTTProvider(STTProvider):
    """Azure Speech STT provider"""
    
    def __init__(self, **kwargs):
        self.api_key = kwargs.get("api_key")
        self.region = kwargs.get("region")
        self.language = kwargs.get("language", "en-US")
        
    async def transcribe(self, audio_data: bytes, **kwargs) -> str:
        # Simplified for now
        return "Transcribed text from Azure Speech"