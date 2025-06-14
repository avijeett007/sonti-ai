# AI Provider Abstraction Framework

The Knova AI SDK includes a comprehensive provider abstraction framework that allows seamless integration with multiple AI providers while maintaining a consistent interface. This framework is designed to work with LiveKit agents while abstracting away the implementation details.

## Overview

The provider abstraction framework provides:

- **Unified Interface**: Consistent API across different AI providers
- **Provider Registry**: Dynamic provider loading and management
- **LiveKit Integration**: Seamless adapter layer for LiveKit agents
- **Error Handling**: Built-in retry logic and error management
- **Telemetry**: Performance tracking and monitoring
- **Extensibility**: Easy addition of new providers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Application Layer                      │
│                    (Your Knova AI Agent)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    LiveKit Adapter Layer                      │
│              (LiveKitProviderAdapter)                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    Provider Registry                          │
│              (Dynamic Provider Management)                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    Provider Implementations                   │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│   │ OpenAI  │  │  Azure  │  │ Google  │  │   AWS   │       │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│   │Anthropic│  │Deepgram │  │ElevenLabs│ │ Custom  │       │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Using the Provider Registry

```python
from knova_ai.providers import create_provider, ProviderType

# Create an LLM provider
llm = create_provider(
    "openai",
    ProviderType.LLM,
    model="gpt-4",
    api_key="your-api-key",
    temperature=0.7
)

# Use the provider
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
]
response = await llm.generate(messages)
```

### Creating a Voice Agent with Custom Providers

```python
from knova_ai import KnovaAI

knova = KnovaAI(license_key="your-license-key")

# Create agent with specific providers
agent = knova.create_agent({
    "name": "Customer Support Agent",
    "type": "voice",
    "llm_provider": "azure",
    "llm_model": "gpt-4",
    "llm_settings": {
        "api_key": "your-azure-key",
        "endpoint": "https://your-resource.openai.azure.com",
        "deployment_name": "gpt-4-deployment"
    },
    "stt_provider": "deepgram",
    "stt_settings": {
        "api_key": "your-deepgram-key",
        "model": "nova-2"
    },
    "tts_provider": "elevenlabs",
    "tts_settings": {
        "api_key": "your-elevenlabs-key",
        "voice_id": "your-voice-id"
    }
})
```

## Supported Providers

### LLM Providers

| Provider | Models | Capabilities |
|----------|--------|--------------|
| OpenAI | gpt-4, gpt-4-turbo, gpt-3.5-turbo | Streaming, Function Calling, Multimodal |
| Azure OpenAI | gpt-4, gpt-35-turbo | Streaming, Function Calling |
| Google | gemini-pro, gemini-pro-vision | Streaming, Multimodal |
| Anthropic | claude-3-opus, claude-3-sonnet | Streaming, Function Calling |
| AWS Bedrock | Various | Streaming |

### STT Providers

| Provider | Features | Capabilities |
|----------|----------|--------------|
| OpenAI Whisper | High accuracy, Multiple languages | Language Detection |
| Deepgram | Real-time, Low latency | Streaming, Custom Vocabulary |
| Google Cloud STT | High accuracy | Streaming, Speaker Diarization |
| Azure Speech | Enterprise features | Streaming, Language Detection |
| AWS Transcribe | Medical/Custom vocabularies | Streaming |

### TTS Providers

| Provider | Features | Capabilities |
|----------|----------|--------------|
| OpenAI | Natural voices | Streaming |
| ElevenLabs | Voice cloning, Emotions | Streaming, Voice Cloning |
| Google Cloud TTS | Multiple languages | SSML Support |
| Azure Speech | Neural voices | Streaming, Emotion Control |
| AWS Polly | Neural/Standard voices | SSML Support |

## Provider Configuration

### Common Configuration Options

All providers support common configuration options:

```python
# LLM Providers
llm_config = {
    "api_key": "your-api-key",
    "model": "model-name",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "stop_sequences": ["\\n\\n"],
    
    # Retry configuration
    "max_retries": 3,
    "retry_delay": 1.0,
    "exponential_backoff": True
}

# STT Providers
stt_config = {
    "api_key": "your-api-key",
    "language": "en",
    "model": "model-name",
    "sample_rate": 16000,
    "encoding": "linear16"
}

# TTS Providers
tts_config = {
    "api_key": "your-api-key",
    "voice": "voice-id",
    "model": "model-name",
    "sample_rate": 24000,
    "audio_format": "mp3",
    "speed": 1.0
}
```

### Provider-Specific Configuration

#### Azure OpenAI
```python
azure_config = {
    "api_key": "your-api-key",
    "endpoint": "https://your-resource.openai.azure.com",
    "deployment_name": "your-deployment",
    "api_version": "2023-12-01-preview"
}
```

#### Deepgram STT
```python
deepgram_config = {
    "api_key": "your-api-key",
    "model": "nova-2",
    "punctuate": True,
    "diarize": True,
    "language": "en",
    "custom_vocabulary": ["knova", "livekit"]
}
```

#### ElevenLabs TTS
```python
elevenlabs_config = {
    "api_key": "your-api-key",
    "voice_id": "your-voice-id",
    "model": "eleven_multilingual_v2",
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.5,
    "use_speaker_boost": True
}
```

## LiveKit Integration

The framework includes a seamless adapter layer for LiveKit:

```python
from knova_ai.providers import LiveKitProviderAdapter, LiveKitAgentConfig

# Configure the agent
config = LiveKitAgentConfig(
    llm_provider="openai",
    llm_config={"model": "gpt-4", "api_key": "key"},
    stt_provider="deepgram",
    stt_config={"api_key": "key"},
    tts_provider="elevenlabs",
    tts_config={"api_key": "key", "voice_id": "voice"},
    agent_name="Support Agent",
    initial_prompt="You are a helpful customer support agent.",
    enable_interruptions=True
)

# Create LiveKit adapter
adapter = LiveKitProviderAdapter(config)

# Create voice assistant
assistant = await adapter.create_voice_assistant()
```

## Advanced Features

### Provider Capabilities

Check provider capabilities before using features:

```python
from knova_ai.providers import ProviderCapability

if provider.has_capability(ProviderCapability.STREAMING):
    # Use streaming
    async for chunk in await provider.generate(messages, stream=True):
        print(chunk, end="")

if provider.has_capability(ProviderCapability.FUNCTION_CALLING):
    # Use function calling
    result = await provider.generate_with_functions(
        messages,
        functions=[{"name": "get_weather", "parameters": {...}}]
    )
```

### Error Handling

The framework includes comprehensive error handling:

```python
from knova_ai.providers import ProviderError, RateLimitError, AuthenticationError

try:
    response = await provider.generate(messages)
except RateLimitError as e:
    print(f"Rate limit hit, retry after {e.retry_after} seconds")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except ProviderError as e:
    print(f"Provider error: {e}")
```

### Performance Monitoring

Track provider performance:

```python
# Get provider health status
health = await provider.health_check()
print(f"Provider: {health['provider']}")
print(f"Healthy: {health['healthy']}")
print(f"Average latency: {health['metrics']['average_latency']}ms")
print(f"Error rate: {health['metrics']['error_rate']}")

# Access detailed metrics
print(f"Total requests: {provider.metrics.request_count}")
print(f"Total tokens: {provider.metrics.total_tokens}")
```

### Custom Providers

Create custom providers by extending base classes:

```python
from knova_ai.providers import BaseLLMProvider, ProviderCapability

class CustomLLMProvider(BaseLLMProvider):
    PROVIDER_NAME = "custom"
    SUPPORTED_MODELS = ["custom-model"]
    CAPABILITIES = [ProviderCapability.STREAMING]
    REQUIRED_CONFIG = ["api_key", "endpoint"]
    
    async def _initialize(self):
        # Initialize your provider
        pass
    
    async def validate_config(self):
        # Validate configuration
        return True
    
    async def generate(self, messages, **kwargs):
        # Implement generation logic
        return "Response from custom provider"

# Register the provider
from knova_ai.providers import register_provider, ProviderType

register_provider("custom", ProviderType.LLM, CustomLLMProvider)
```

## Migration Guide

### From Direct LiveKit Plugins

Before:
```python
from livekit.plugins import openai

llm = openai.LLM(model="gpt-4", api_key="key")
```

After:
```python
from knova_ai.providers import create_provider, ProviderType

llm = create_provider(
    "openai",
    ProviderType.LLM,
    model="gpt-4",
    api_key="key"
)
```

### From Legacy Provider Interface

The legacy interface is still supported but deprecated:

```python
# Legacy (deprecated)
from knova_ai.providers import LLMProvider
llm = LLMProvider.create("openai", "gpt-4", api_key="key")

# New approach
from knova_ai.providers import create_provider, ProviderType
llm = create_provider("openai", ProviderType.LLM, model="gpt-4", api_key="key")
```

## Best Practices

1. **Always Initialize Providers**: Call `await provider.initialize()` before use
2. **Handle Errors Gracefully**: Use try-except blocks for provider operations
3. **Monitor Performance**: Check health status and metrics regularly
4. **Use Appropriate Timeouts**: Configure timeouts based on your use case
5. **Validate Configuration**: Always validate provider config before deployment
6. **Use Streaming When Possible**: For better user experience with LLM/TTS
7. **Cache Provider Instances**: Reuse providers instead of creating new ones

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API keys are correct
   - Check if keys have required permissions
   - Ensure endpoints are accessible

2. **Rate Limiting**
   - Implement exponential backoff
   - Use provider retry configuration
   - Monitor usage with metrics

3. **Timeout Errors**
   - Increase timeout values for slow providers
   - Use streaming for long responses
   - Check network connectivity

4. **Model Not Found**
   - Verify model name is correct
   - Check provider documentation for supported models
   - Ensure model is available in your region/deployment

### Debug Mode

Enable debug logging:

```python
import logging

logging.getLogger("knova.providers").setLevel(logging.DEBUG)
```

## Future Enhancements

- Local model support (Ollama, LlamaCPP)
- Multi-provider failover
- Cost optimization routing
- A/B testing framework
- Provider response caching
- Advanced load balancing