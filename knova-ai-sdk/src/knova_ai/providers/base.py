"""Base provider classes with enhanced functionality for Knova AI"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, AsyncIterator
import time
from contextlib import asynccontextmanager

from ..telemetry import TelemetryCollector
from ..config import Settings


class ProviderType(Enum):
    """Types of AI providers"""
    LLM = "llm"
    STT = "stt"
    TTS = "tts"


class ProviderCapability(Enum):
    """Provider capabilities"""
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    MULTIMODAL = "multimodal"
    CUSTOM_VOCABULARY = "custom_vocabulary"
    VOICE_CLONING = "voice_cloning"
    EMOTION_CONTROL = "emotion_control"
    LANGUAGE_DETECTION = "language_detection"
    SPEAKER_DIARIZATION = "speaker_diarization"


@dataclass
class ProviderMetrics:
    """Metrics for provider performance tracking"""
    request_count: int = 0
    error_count: int = 0
    total_latency: float = 0.0
    total_tokens: int = 0
    last_request_time: Optional[datetime] = None
    
    @property
    def average_latency(self) -> float:
        """Calculate average latency"""
        if self.request_count == 0:
            return 0.0
        return self.total_latency / self.request_count
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


class ProviderError(Exception):
    """Base exception for provider errors"""
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.timestamp = datetime.now()


class RateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded"""
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        super().__init__(message, provider, "RATE_LIMIT")
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Raised when provider authentication fails"""
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider, "AUTH_ERROR")


class BaseProvider(ABC):
    """Enhanced base class for all AI providers"""
    
    def __init__(
        self,
        provider_name: str,
        provider_type: ProviderType,
        api_key: Optional[str] = None,
        **config
    ):
        self.provider_name = provider_name
        self.provider_type = provider_type
        self.api_key = api_key
        self.config = config
        self.logger = logging.getLogger(f"knova.providers.{provider_name}")
        self.telemetry = TelemetryCollector.get_instance()
        self.metrics = ProviderMetrics()
        self._capabilities: List[ProviderCapability] = []
        self._is_initialized = False
        self._retry_config = {
            "max_retries": config.get("max_retries", 3),
            "retry_delay": config.get("retry_delay", 1.0),
            "exponential_backoff": config.get("exponential_backoff", True)
        }
        
    async def initialize(self) -> None:
        """Initialize the provider (async setup)"""
        if self._is_initialized:
            return
            
        try:
            await self._initialize()
            self._is_initialized = True
            self.logger.info(f"Provider {self.provider_name} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize provider {self.provider_name}: {e}")
            raise ProviderError(f"Initialization failed: {e}", self.provider_name)
    
    @abstractmethod
    async def _initialize(self) -> None:
        """Provider-specific initialization logic"""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass
    
    @property
    def capabilities(self) -> List[ProviderCapability]:
        """Get provider capabilities"""
        return self._capabilities
    
    def has_capability(self, capability: ProviderCapability) -> bool:
        """Check if provider has a specific capability"""
        return capability in self._capabilities
    
    async def _track_metrics(self, start_time: float, success: bool, tokens: int = 0) -> None:
        """Track provider metrics"""
        elapsed = time.time() - start_time
        self.metrics.request_count += 1
        self.metrics.total_latency += elapsed
        self.metrics.total_tokens += tokens
        self.metrics.last_request_time = datetime.now()
        
        if not success:
            self.metrics.error_count += 1
            
        # Send telemetry
        await self.telemetry.track_event(
            event_type="provider_request",
            properties={
                "provider": self.provider_name,
                "provider_type": self.provider_type.value,
                "success": success,
                "latency": elapsed,
                "tokens": tokens,
                "error_rate": self.metrics.error_rate
            }
        )
    
    async def _retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry and exponential backoff"""
        last_error = None
        
        for attempt in range(self._retry_config["max_retries"]):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                # Use provider-specific retry after if available
                delay = e.retry_after or self._retry_config["retry_delay"]
                if self._retry_config["exponential_backoff"]:
                    delay *= (2 ** attempt)
                
                self.logger.warning(
                    f"Rate limit hit for {self.provider_name}, "
                    f"retrying after {delay}s (attempt {attempt + 1})"
                )
                await asyncio.sleep(delay)
                last_error = e
            except AuthenticationError:
                # Don't retry authentication errors
                raise
            except Exception as e:
                delay = self._retry_config["retry_delay"]
                if self._retry_config["exponential_backoff"]:
                    delay *= (2 ** attempt)
                    
                self.logger.warning(
                    f"Error in {self.provider_name}: {e}, "
                    f"retrying after {delay}s (attempt {attempt + 1})"
                )
                await asyncio.sleep(delay)
                last_error = e
        
        # All retries exhausted
        if last_error:
            raise last_error
        raise ProviderError("All retries exhausted", self.provider_name)
    
    @asynccontextmanager
    async def _request_context(self, operation: str):
        """Context manager for provider requests"""
        start_time = time.time()
        success = False
        tokens = 0
        
        try:
            self.logger.debug(f"Starting {operation} for {self.provider_name}")
            yield locals()  # Pass context variables to the caller
            success = True
        except Exception as e:
            self.logger.error(f"Error in {operation} for {self.provider_name}: {e}")
            raise
        finally:
            # Extract tokens if set by the operation
            if 'tokens' in locals():
                tokens = locals()['tokens']
            await self._track_metrics(start_time, success, tokens)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and status"""
        try:
            is_healthy = await self.validate_config()
            return {
                "provider": self.provider_name,
                "type": self.provider_type.value,
                "healthy": is_healthy,
                "metrics": {
                    "request_count": self.metrics.request_count,
                    "error_rate": self.metrics.error_rate,
                    "average_latency": self.metrics.average_latency,
                    "last_request": self.metrics.last_request_time.isoformat() 
                        if self.metrics.last_request_time else None
                },
                "capabilities": [cap.value for cap in self.capabilities]
            }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "type": self.provider_type.value,
                "healthy": False,
                "error": str(e)
            }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name}, type={self.provider_type.value})"


class BaseLLMProvider(BaseProvider):
    """Enhanced base class for LLM providers"""
    
    def __init__(self, provider_name: str, model: str, api_key: Optional[str] = None, **config):
        super().__init__(provider_name, ProviderType.LLM, api_key, **config)
        self.model = model
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.top_p = config.get("top_p", 1.0)
        self.frequency_penalty = config.get("frequency_penalty", 0.0)
        self.presence_penalty = config.get("presence_penalty", 0.0)
        self.stop_sequences = config.get("stop_sequences", [])
        
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[str, AsyncIterator[str]]:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    async def generate_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response with function calling support"""
        pass
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text (provider-specific implementation)"""
        # Default implementation - can be overridden
        return len(text.split())


class BaseSTTProvider(BaseProvider):
    """Enhanced base class for STT providers"""
    
    def __init__(self, provider_name: str, api_key: Optional[str] = None, **config):
        super().__init__(provider_name, ProviderType.STT, api_key, **config)
        self.language = config.get("language", "en")
        self.model = config.get("model")
        self.sample_rate = config.get("sample_rate", 16000)
        self.encoding = config.get("encoding", "linear16")
        
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """Transcribe audio to text"""
        pass
    
    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Transcribe streaming audio"""
        pass


class BaseTTSProvider(BaseProvider):
    """Enhanced base class for TTS providers"""
    
    def __init__(self, provider_name: str, api_key: Optional[str] = None, **config):
        super().__init__(provider_name, ProviderType.TTS, api_key, **config)
        self.voice = config.get("voice")
        self.model = config.get("model")
        self.sample_rate = config.get("sample_rate", 24000)
        self.audio_format = config.get("audio_format", "mp3")
        self.speed = config.get("speed", 1.0)
        
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        **kwargs
    ) -> bytes:
        """Synthesize text to speech"""
        pass
    
    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Synthesize text to speech with streaming"""
        pass