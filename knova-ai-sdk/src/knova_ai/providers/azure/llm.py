"""Azure OpenAI LLM provider implementation"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, AsyncIterator
from urllib.parse import urljoin

from ..base import BaseLLMProvider, ProviderCapability, ProviderError, RateLimitError, AuthenticationError


class AzureOpenAILLMProvider(BaseLLMProvider):
    """Azure OpenAI LLM provider with full API support"""
    
    PROVIDER_NAME = "azure"
    SUPPORTED_MODELS = [
        "gpt-4", "gpt-4-32k", "gpt-4-turbo",
        "gpt-35-turbo", "gpt-35-turbo-16k"
    ]
    CAPABILITIES = [
        ProviderCapability.STREAMING,
        ProviderCapability.FUNCTION_CALLING
    ]
    REQUIRED_CONFIG = ["api_key", "endpoint", "deployment_name"]
    OPTIONAL_CONFIG = [
        "api_version", "temperature", "max_tokens", "top_p",
        "frequency_penalty", "presence_penalty", "stop_sequences"
    ]
    
    def __init__(
        self,
        model: str,
        api_key: str,
        endpoint: str,
        deployment_name: str,
        **config
    ):
        super().__init__("azure", model, api_key, **config)
        self.endpoint = endpoint.rstrip("/")
        self.deployment_name = deployment_name
        self.api_version = config.get("api_version", "2023-12-01-preview")
        self._session: Optional[aiohttp.ClientSession] = None
        self._capabilities = self.CAPABILITIES
        
    async def _initialize(self) -> None:
        """Initialize Azure OpenAI provider"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def validate_config(self) -> bool:
        """Validate Azure OpenAI configuration"""
        if not self.api_key:
            raise AuthenticationError("Azure OpenAI API key is required", self.provider_name)
        
        if not self.endpoint:
            raise ProviderError("Azure OpenAI endpoint is required", self.provider_name)
        
        if not self.deployment_name:
            raise ProviderError("Azure OpenAI deployment name is required", self.provider_name)
        
        # Test API connection
        try:
            headers = self._get_headers()
            url = f"{self.endpoint}/openai/deployments?api-version={self.api_version}"
            
            async with self._session.get(url, headers=headers) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid Azure OpenAI API key", self.provider_name)
                elif response.status == 404:
                    # Endpoint might not support listing deployments, but that's okay
                    return True
                elif response.status >= 400:
                    raise ProviderError(f"Azure OpenAI API error: {response.status}", self.provider_name)
                return True
        except aiohttp.ClientError as e:
            raise ProviderError(f"Failed to connect to Azure OpenAI API: {e}", self.provider_name)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for Azure"""
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _build_url(self, path: str) -> str:
        """Build full URL for Azure OpenAI API"""
        base = f"{self.endpoint}/openai/deployments/{self.deployment_name}"
        return f"{base}/{path}?api-version={self.api_version}"
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[str, AsyncIterator[str]]:
        """Generate response from Azure OpenAI"""
        await self.initialize()
        
        stream = kwargs.get("stream", False)
        
        async with self._request_context("generate") as ctx:
            if stream:
                return self._generate_stream(messages, **kwargs)
            else:
                response = await self._generate_complete(messages, **kwargs)
                # Update context with token usage
                if response.get("usage"):
                    ctx['tokens'] = response["usage"].get('total_tokens', 0)
                return response["content"]
    
    async def _generate_complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate complete response"""
        payload = self._build_payload(messages, **kwargs)
        payload["stream"] = False
        
        async def _request():
            headers = self._get_headers()
            url = self._build_url("chat/completions")
            
            async with self._session.post(url, json=payload, headers=headers) as response:
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", 60)
                    raise RateLimitError(
                        "Azure OpenAI rate limit exceeded",
                        self.provider_name,
                        int(retry_after)
                    )
                elif response.status == 401:
                    raise AuthenticationError("Invalid Azure OpenAI API key", self.provider_name)
                elif response.status != 200:
                    error_data = await response.json()
                    raise ProviderError(
                        f"Azure OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
                        self.provider_name
                    )
                
                data = await response.json()
                choice = data["choices"][0]
                message = choice["message"]
                
                return {
                    "content": message.get("content", ""),
                    "role": message.get("role", "assistant"),
                    "function_call": message.get("function_call"),
                    "finish_reason": choice.get("finish_reason"),
                    "usage": data.get("usage")
                }
        
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
        url = self._build_url("chat/completions")
        
        async with self._session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                error_data = await response.json()
                raise ProviderError(
                    f"Azure OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
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
                        if "choices" in data and len(data["choices"]) > 0:
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
            url = self._build_url("chat/completions")
            
            async def _request():
                async with self._session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise ProviderError(
                            f"Azure OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
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
        """Build request payload for Azure OpenAI"""
        payload = {
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
    
    async def get_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """Get embeddings for texts using Azure OpenAI"""
        await self.initialize()
        
        async with self._request_context("embeddings") as ctx:
            headers = self._get_headers()
            url = self._build_url("embeddings")
            
            payload = {
                "input": texts,
                "encoding_format": kwargs.get("encoding_format", "float")
            }
            
            async def _request():
                async with self._session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise ProviderError(
                            f"Azure OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}",
                            self.provider_name
                        )
                    
                    data = await response.json()
                    embeddings = [item["embedding"] for item in data["data"]]
                    
                    # Update token usage
                    if "usage" in data:
                        ctx['tokens'] = data["usage"].get("total_tokens", 0)
                    
                    return embeddings
            
            return await self._retry_with_backoff(_request)
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        try:
            import tiktoken
            # Map Azure model names to OpenAI model names for tiktoken
            model_map = {
                "gpt-35-turbo": "gpt-3.5-turbo",
                "gpt-35-turbo-16k": "gpt-3.5-turbo-16k"
            }
            tiktoken_model = model_map.get(self.model, self.model)
            encoding = tiktoken.encoding_for_model(tiktoken_model)
            return len(encoding.encode(text))
        except ImportError:
            # Fallback to approximation
            return len(text.split()) * 1.3
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