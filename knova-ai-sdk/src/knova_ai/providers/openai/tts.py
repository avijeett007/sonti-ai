"""OpenAI Text-to-Speech provider implementation"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, AsyncIterator, List
import json

from ..base import BaseTTSProvider, ProviderCapability, ProviderError, RateLimitError, AuthenticationError


class OpenAITTSProvider(BaseTTSProvider):
    """OpenAI TTS provider"""
    
    PROVIDER_NAME = "openai"
    SUPPORTED_MODELS = ["tts-1", "tts-1-hd"]
    SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    SUPPORTED_FORMATS = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
    CAPABILITIES = [
        ProviderCapability.STREAMING
    ]
    REQUIRED_CONFIG = ["api_key"]
    OPTIONAL_CONFIG = [
        "model", "voice", "speed", "response_format",
        "organization", "base_url"
    ]
    
    def __init__(self, api_key: str, **config):
        super().__init__("openai", api_key, **config)
        self.model = config.get("model", "tts-1")
        self.voice = config.get("voice", "alloy")
        self.speed = config.get("speed", 1.0)
        self.response_format = config.get("response_format", "mp3")
        self.organization = config.get("organization")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self._session: Optional[aiohttp.ClientSession] = None
        self._capabilities = self.CAPABILITIES
        
    async def _initialize(self) -> None:
        """Initialize OpenAI TTS provider"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def validate_config(self) -> bool:
        """Validate configuration"""
        if not self.api_key:
            raise AuthenticationError("OpenAI API key is required", self.provider_name)
        
        if self.model not in self.SUPPORTED_MODELS:
            raise ProviderError(
                f"Unsupported model: {self.model}. Supported models: {', '.join(self.SUPPORTED_MODELS)}",
                self.provider_name
            )
        
        if self.voice not in self.SUPPORTED_VOICES:
            raise ProviderError(
                f"Unsupported voice: {self.voice}. Supported voices: {', '.join(self.SUPPORTED_VOICES)}",
                self.provider_name
            )
        
        if self.response_format not in self.SUPPORTED_FORMATS:
            raise ProviderError(
                f"Unsupported format: {self.response_format}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}",
                self.provider_name
            )
        
        if not 0.25 <= self.speed <= 4.0:
            raise ProviderError(
                f"Speed must be between 0.25 and 4.0, got {self.speed}",
                self.provider_name
            )
        
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers
    
    async def synthesize(
        self,
        text: str,
        **kwargs
    ) -> bytes:
        """Synthesize text to speech"""
        await self.initialize()
        
        async with self._request_context("synthesize") as ctx:
            # Build request payload
            payload = {
                "model": kwargs.get("model", self.model),
                "input": text,
                "voice": kwargs.get("voice", self.voice),
                "response_format": kwargs.get("response_format", self.response_format),
                "speed": kwargs.get("speed", self.speed)
            }
            
            # Make request
            async def _request():
                headers = self._get_headers()
                async with self._session.post(
                    f"{self.base_url}/audio/speech",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", 60)
                        raise RateLimitError(
                            "OpenAI rate limit exceeded",
                            self.provider_name,
                            int(retry_after)
                        )
                    elif response.status == 401:
                        raise AuthenticationError("Invalid OpenAI API key", self.provider_name)
                    elif response.status != 200:
                        error_data = await response.json()
                        raise ProviderError(
                            f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
                            self.provider_name
                        )
                    
                    # Return audio data
                    return await response.read()
            
            return await self._retry_with_backoff(_request)
    
    async def synthesize_stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Synthesize text to speech with streaming"""
        await self.initialize()
        
        # Build request payload
        payload = {
            "model": kwargs.get("model", self.model),
            "input": text,
            "voice": kwargs.get("voice", self.voice),
            "response_format": kwargs.get("response_format", self.response_format),
            "speed": kwargs.get("speed", self.speed)
        }
        
        headers = self._get_headers()
        
        async with self._session.post(
            f"{self.base_url}/audio/speech",
            json=payload,
            headers=headers
        ) as response:
            if response.status == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    "OpenAI rate limit exceeded",
                    self.provider_name,
                    int(retry_after)
                )
            elif response.status == 401:
                raise AuthenticationError("Invalid OpenAI API key", self.provider_name)
            elif response.status != 200:
                error_data = await response.json()
                raise ProviderError(
                    f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
                    self.provider_name
                )
            
            # Stream audio chunks
            async for chunk in response.content.iter_chunked(1024):
                yield chunk
    
    async def synthesize_segments(
        self,
        segments: List[Dict[str, Any]],
        **kwargs
    ) -> bytes:
        """
        Synthesize multiple text segments with different parameters.
        Each segment can have its own voice and speed settings.
        """
        await self.initialize()
        
        audio_chunks = []
        
        for segment in segments:
            text = segment.get("text", "")
            if not text:
                continue
            
            # Override parameters for this segment
            segment_kwargs = kwargs.copy()
            if "voice" in segment:
                segment_kwargs["voice"] = segment["voice"]
            if "speed" in segment:
                segment_kwargs["speed"] = segment["speed"]
            
            # Synthesize segment
            audio_data = await self.synthesize(text, **segment_kwargs)
            audio_chunks.append(audio_data)
        
        # Concatenate audio chunks
        # Note: This simple concatenation works for formats like WAV and PCM
        # For compressed formats like MP3, proper audio processing would be needed
        return b"".join(audio_chunks)
    
    def estimate_duration(self, text: str, speed: Optional[float] = None) -> float:
        """Estimate audio duration based on text length and speed"""
        # Rough estimation: ~150 words per minute at normal speed
        words = len(text.split())
        wpm = 150 * (speed or self.speed)
        return (words / wpm) * 60  # Duration in seconds
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices with descriptions"""
        return [
            {"id": "alloy", "name": "Alloy", "gender": "neutral", "description": "Neutral and balanced"},
            {"id": "echo", "name": "Echo", "gender": "male", "description": "Smooth and articulate"},
            {"id": "fable", "name": "Fable", "gender": "neutral", "description": "Expressive and dynamic"},
            {"id": "onyx", "name": "Onyx", "gender": "male", "description": "Deep and authoritative"},
            {"id": "nova", "name": "Nova", "gender": "female", "description": "Warm and friendly"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female", "description": "Clear and energetic"}
        ]
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None