"""OpenAI LLM provider implementation"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, AsyncIterator
from dataclasses import dataclass

from ..base import BaseLLMProvider, ProviderCapability, ProviderError, RateLimitError, AuthenticationError
from ...telemetry import TelemetryCollector


@dataclass
class OpenAIResponse:
    """OpenAI API response structure"""
    content: str
    role: str = "assistant"
    function_call: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI LLM provider with full API support"""
    
    PROVIDER_NAME = "openai"
    SUPPORTED_MODELS = [
        "gpt-4-turbo-preview", "gpt-4", "gpt-4-32k",
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
        "gpt-4-vision-preview"  # Multimodal support
    ]
    CAPABILITIES = [
        ProviderCapability.STREAMING,
        ProviderCapability.FUNCTION_CALLING,
        ProviderCapability.MULTIMODAL
    ]
    REQUIRED_CONFIG = ["api_key", "model"]
    OPTIONAL_CONFIG = [
        "temperature", "max_tokens", "top_p", "frequency_penalty",
        "presence_penalty", "stop_sequences", "organization", "base_url"
    ]
    
    def __init__(self, model: str, api_key: str, **config):
        super().__init__("openai", model, api_key, **config)
        self.organization = config.get("organization")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self._session: Optional[aiohttp.ClientSession] = None
        self._capabilities = self.CAPABILITIES
        
    async def _initialize(self) -> None:
        """Initialize OpenAI provider"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def validate_config(self) -> bool:
        """Validate OpenAI configuration"""
        if not self.api_key:
            raise AuthenticationError("OpenAI API key is required", self.provider_name)
        
        if self.model not in self.SUPPORTED_MODELS:
            raise ProviderError(
                f"Unsupported model: {self.model}. Supported models: {', '.join(self.SUPPORTED_MODELS)}",
                self.provider_name
            )
        
        # Test API connection
        try:
            headers = self._get_headers()
            async with self._session.get(f"{self.base_url}/models", headers=headers) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid OpenAI API key", self.provider_name)
                elif response.status != 200:
                    raise ProviderError(f"OpenAI API error: {response.status}", self.provider_name)
                return True
        except aiohttp.ClientError as e:
            raise ProviderError(f"Failed to connect to OpenAI API: {e}", self.provider_name)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[str, AsyncIterator[str]]:
        """Generate response from OpenAI"""
        await self.initialize()
        
        stream = kwargs.get("stream", False)
        
        async with self._request_context("generate") as ctx:
            if stream:
                return self._generate_stream(messages, **kwargs)
            else:
                response = await self._generate_complete(messages, **kwargs)
                # Update context with token usage
                if response.usage:
                    ctx['tokens'] = response.usage.get('total_tokens', 0)
                return response.content
    
    async def _generate_complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> OpenAIResponse:
        """Generate complete response"""
        payload = self._build_payload(messages, **kwargs)
        payload["stream"] = False
        
        async def _request():
            headers = self._get_headers()
            async with self._session.post(
                f"{self.base_url}/chat/completions",
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
                
                data = await response.json()
                choice = data["choices"][0]
                message = choice["message"]
                
                return OpenAIResponse(
                    content=message.get("content", ""),
                    role=message.get("role", "assistant"),
                    function_call=message.get("function_call"),
                    finish_reason=choice.get("finish_reason"),
                    usage=data.get("usage")
                )
        
        return await self._retry_with_backoff(_request)
    
    async def _generate_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming response"""
        payload = self._build_payload(messages, **kwargs)
        payload["stream"] = True
        
        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"
        
        async with self._session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        ) as response:
            if response.status != 200:
                error_data = await response.json()
                raise ProviderError(
                    f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
                    self.provider_name
                )
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        choice = data["choices"][0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    
    async def generate_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response with function calling"""
        await self.initialize()
        
        async with self._request_context("generate_with_functions") as ctx:
            payload = self._build_payload(messages, **kwargs)
            payload["functions"] = functions
            if "function_call" in kwargs:
                payload["function_call"] = kwargs["function_call"]
            
            headers = self._get_headers()
            
            async def _request():
                async with self._session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise ProviderError(
                            f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
                            self.provider_name
                        )
                    
                    data = await response.json()
                    choice = data["choices"][0]
                    message = choice["message"]
                    
                    # Update token usage
                    if "usage" in data:
                        ctx['tokens'] = data["usage"].get("total_tokens", 0)
                    
                    return {
                        "content": message.get("content"),
                        "function_call": message.get("function_call"),
                        "role": message.get("role", "assistant"),
                        "finish_reason": choice.get("finish_reason"),
                        "usage": data.get("usage")
                    }
            
            return await self._retry_with_backoff(_request)
    
    def _build_payload(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Build request payload"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "top_p": kwargs.get("top_p", self.top_p),
            "frequency_penalty": kwargs.get("frequency_penalty", self.frequency_penalty),
            "presence_penalty": kwargs.get("presence_penalty", self.presence_penalty)
        }
        
        if self.stop_sequences or kwargs.get("stop_sequences"):
            payload["stop"] = kwargs.get("stop_sequences", self.stop_sequences)
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in payload and key not in ["stream", "functions", "function_call"]:
                payload[key] = value
        
        return payload
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except ImportError:
            # Fallback to approximation
            return len(text.split()) * 1.3  # Rough approximation
        except Exception:
            # Model not found in tiktoken, use approximation
            return len(text.split()) * 1.3
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None