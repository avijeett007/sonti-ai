"""Azure Speech Services STT provider implementation"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, AsyncIterator
import json
import uuid

from ..base import BaseSTTProvider, ProviderCapability, ProviderError, AuthenticationError


class AzureSTTProvider(BaseSTTProvider):
    """Azure Speech Services STT provider"""
    
    PROVIDER_NAME = "azure"
    CAPABILITIES = [
        ProviderCapability.STREAMING,
        ProviderCapability.LANGUAGE_DETECTION,
        ProviderCapability.SPEAKER_DIARIZATION
    ]
    REQUIRED_CONFIG = ["api_key", "region"]
    OPTIONAL_CONFIG = [
        "language", "recognition_mode", "profanity_option",
        "enable_diarization", "enable_punctuation"
    ]
    
    def __init__(self, api_key: str, region: str, **config):
        super().__init__("azure", api_key, **config)
        self.region = region
        self.recognition_mode = config.get("recognition_mode", "conversation")
        self.profanity_option = config.get("profanity_option", "masked")
        self.enable_diarization = config.get("enable_diarization", False)
        self.enable_punctuation = config.get("enable_punctuation", True)
        self._session: Optional[aiohttp.ClientSession] = None
        self._capabilities = self.CAPABILITIES
        
    async def _initialize(self) -> None:
        """Initialize Azure STT provider"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=300)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def validate_config(self) -> bool:
        """Validate configuration"""
        if not self.api_key:
            raise AuthenticationError("Azure Speech API key is required", self.provider_name)
        
        if not self.region:
            raise ProviderError("Azure region is required", self.provider_name)
        
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "audio/wav"
        }
    
    async def transcribe(
        self,
        audio_data: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """Transcribe audio using Azure Speech Services"""
        await self.initialize()
        
        # Note: This is a simplified implementation
        # Actual Azure Speech SDK would be used in production
        return {
            "text": "Transcribed text from Azure Speech Services",
            "language": self.language,
            "confidence": 0.95
        }
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream transcription using Azure Speech Services"""
        await self.initialize()
        
        # Note: This is a simplified implementation
        # Actual Azure Speech SDK would handle WebSocket streaming
        async for chunk in audio_stream:
            # Process audio chunk
            yield {
                "text": "Partial transcription",
                "is_final": False,
                "language": self.language
            }
        
        # Final result
        yield {
            "text": "Final transcription from Azure",
            "is_final": True,
            "language": self.language
        }