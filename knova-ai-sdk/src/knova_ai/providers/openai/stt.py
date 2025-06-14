"""OpenAI Speech-to-Text (Whisper) provider implementation"""

import asyncio
import aiohttp
import io
from typing import Dict, Any, Optional, AsyncIterator
from pathlib import Path

from ..base import BaseSTTProvider, ProviderCapability, ProviderError, RateLimitError, AuthenticationError


class OpenAISTTProvider(BaseSTTProvider):
    """OpenAI Whisper STT provider"""
    
    PROVIDER_NAME = "openai"
    SUPPORTED_MODELS = ["whisper-1"]
    CAPABILITIES = [
        ProviderCapability.LANGUAGE_DETECTION
    ]
    REQUIRED_CONFIG = ["api_key"]
    OPTIONAL_CONFIG = [
        "model", "language", "prompt", "response_format", 
        "temperature", "organization", "base_url"
    ]
    
    def __init__(self, api_key: str, **config):
        super().__init__("openai", api_key, **config)
        self.model = config.get("model", "whisper-1")
        self.prompt = config.get("prompt")
        self.response_format = config.get("response_format", "json")
        self.temperature = config.get("temperature", 0.0)
        self.organization = config.get("organization")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self._session: Optional[aiohttp.ClientSession] = None
        self._capabilities = self.CAPABILITIES
        
    async def _initialize(self) -> None:
        """Initialize OpenAI STT provider"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for audio uploads
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
        
        if self.response_format not in ["json", "text", "srt", "verbose_json", "vtt"]:
            raise ProviderError(
                f"Invalid response format: {self.response_format}",
                self.provider_name
            )
        
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers
    
    async def transcribe(
        self,
        audio_data: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper"""
        await self.initialize()
        
        async with self._request_context("transcribe") as ctx:
            # Prepare form data
            form_data = aiohttp.FormData()
            
            # Add audio file
            audio_file = io.BytesIO(audio_data)
            form_data.add_field(
                "file",
                audio_file,
                filename="audio.wav",
                content_type="audio/wav"
            )
            
            # Add other parameters
            form_data.add_field("model", self.model)
            
            response_format = kwargs.get("response_format", self.response_format)
            form_data.add_field("response_format", response_format)
            
            if self.language or "language" in kwargs:
                language = kwargs.get("language", self.language)
                if language:
                    form_data.add_field("language", language)
            
            if self.prompt or "prompt" in kwargs:
                prompt = kwargs.get("prompt", self.prompt)
                if prompt:
                    form_data.add_field("prompt", prompt)
            
            temperature = kwargs.get("temperature", self.temperature)
            form_data.add_field("temperature", str(temperature))
            
            # Make request
            async def _request():
                headers = self._get_headers()
                async with self._session.post(
                    f"{self.base_url}/audio/transcriptions",
                    data=form_data,
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
                    
                    # Parse response based on format
                    if response_format == "json" or response_format == "verbose_json":
                        data = await response.json()
                        return {
                            "text": data.get("text", ""),
                            "language": data.get("language"),
                            "duration": data.get("duration"),
                            "segments": data.get("segments", []) if response_format == "verbose_json" else None,
                            "words": data.get("words", []) if response_format == "verbose_json" else None
                        }
                    else:
                        # Text-based formats
                        text = await response.text()
                        return {
                            "text": text,
                            "format": response_format
                        }
            
            return await self._retry_with_backoff(_request)
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        OpenAI Whisper doesn't support real-time streaming.
        This implementation buffers audio and transcribes in chunks.
        """
        await self.initialize()
        
        # Buffer settings
        buffer_duration_ms = kwargs.get("buffer_duration_ms", 5000)  # 5 seconds
        sample_rate = kwargs.get("sample_rate", self.sample_rate)
        bytes_per_second = sample_rate * 2  # 16-bit audio
        buffer_size = int(bytes_per_second * buffer_duration_ms / 1000)
        
        audio_buffer = bytearray()
        
        async for chunk in audio_stream:
            audio_buffer.extend(chunk)
            
            # Process when buffer is full
            if len(audio_buffer) >= buffer_size:
                # Transcribe the buffer
                result = await self.transcribe(bytes(audio_buffer), **kwargs)
                
                # Clear buffer
                audio_buffer.clear()
                
                # Yield result
                yield {
                    "text": result.get("text", ""),
                    "is_final": True,
                    "language": result.get("language"),
                    "timestamp": asyncio.get_event_loop().time()
                }
        
        # Process remaining audio
        if audio_buffer:
            result = await self.transcribe(bytes(audio_buffer), **kwargs)
            yield {
                "text": result.get("text", ""),
                "is_final": True,
                "language": result.get("language"),
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def translate(
        self,
        audio_data: bytes,
        target_language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """Translate audio to English using OpenAI Whisper"""
        if target_language != "en":
            raise ProviderError(
                "OpenAI Whisper only supports translation to English",
                self.provider_name
            )
        
        await self.initialize()
        
        async with self._request_context("translate") as ctx:
            # Prepare form data
            form_data = aiohttp.FormData()
            
            # Add audio file
            audio_file = io.BytesIO(audio_data)
            form_data.add_field(
                "file",
                audio_file,
                filename="audio.wav",
                content_type="audio/wav"
            )
            
            # Add other parameters
            form_data.add_field("model", self.model)
            
            response_format = kwargs.get("response_format", self.response_format)
            form_data.add_field("response_format", response_format)
            
            if self.prompt or "prompt" in kwargs:
                prompt = kwargs.get("prompt", self.prompt)
                if prompt:
                    form_data.add_field("prompt", prompt)
            
            temperature = kwargs.get("temperature", self.temperature)
            form_data.add_field("temperature", str(temperature))
            
            # Make request
            async def _request():
                headers = self._get_headers()
                async with self._session.post(
                    f"{self.base_url}/audio/translations",
                    data=form_data,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise ProviderError(
                            f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
                            self.provider_name
                        )
                    
                    # Parse response
                    if response_format == "json" or response_format == "verbose_json":
                        data = await response.json()
                        return {
                            "text": data.get("text", ""),
                            "source_language": data.get("language"),
                            "target_language": "en"
                        }
                    else:
                        text = await response.text()
                        return {
                            "text": text,
                            "target_language": "en",
                            "format": response_format
                        }
            
            return await self._retry_with_backoff(_request)
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None