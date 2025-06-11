# Knova AI SDK

## Overview

The Knova AI SDK is a Python library that provides the core functionality for creating, managing, and deploying voice AI agents. It serves as the foundation for the Knova AI platform and is designed to be modular, extensible, and easy to use.

The SDK is distributed as a separate PyPI package (`knova-ai-sdk`) and can be used independently of the main Knova AI platform. This separation allows for easier maintenance, versioning, and integration with other systems.

## Architecture

The SDK is structured around several key components:

### Client

The main entry point for interacting with Knova AI functionality:

```python
from knova_ai import KnovaAI

client = KnovaAI(
    license_key="your-license-key",
    database_config={
        "type": "sqlite",  # or "supabase", "postgres", etc.
        "path": "local.db", # or connection string
    },
    telemetry_options={
        "enabled": True,
        "webhook_url": "https://your-webhook.com/events",
        "metrics": ["api_calls", "agent_runtime"]
    }
)
```

### Agents

The SDK provides various agent types for different use cases:

- `VoiceAgent`: For voice-based interactions
- `WorkflowAgent`: For orchestrating multiple agents and tools
- `TextAgent`: For text-based interactions

Example usage:

```python
# Create a voice agent
agent = client.create_agent(
    name="Customer Support",
    llm_provider="openai",
    llm_model="gpt-4",
    stt_provider="deepgram",
    tts_provider="elevenlabs"
)

# Deploy the agent
deployment = await client.deploy_agent(agent)
```

### Providers

The SDK abstracts various AI service providers:

- LLM providers (OpenAI, Google, Azure, Anthropic, etc.)
- STT providers (Deepgram, Google, Azure, etc.)
- TTS providers (ElevenLabs, Google, Azure, etc.)

Each provider is implemented as a plugin, allowing for easy addition of new providers.

### License Management

The SDK includes license validation and management:

```python
# Validate license manually
is_valid = await client.license_validator.validate()

# Check license status
license_info = await client.get_license_info()
```

### Telemetry

The SDK collects usage telemetry and can send it to configured webhooks:

```python
# Configure webhook for telemetry
client.telemetry.configure_webhook("https://your-webhook.com/events")

# Track custom event
await client.telemetry.track_event("custom_event", {"key": "value"})
```

## Database Integration

The SDK can integrate with various database backends:

```python
# Configure database connection
client.configure_database({
    "type": "sqlite",
    "path": "local.db"
})

# Or with PostgreSQL
client.configure_database({
    "type": "postgres",
    "connection_string": "postgresql://user:password@localhost/knova"
})
```

## LiveKit Integration

The SDK seamlessly integrates with LiveKit for real-time communication:

```python
# Configure LiveKit
client.configure_livekit(
    api_key="your-livekit-api-key",
    api_secret="your-livekit-api-secret",
    url="wss://your-livekit-server.com"
)

# Create LiveKit agent
livekit_agent = agent.create_livekit_agent()
```

## SIP Telephony

The SDK supports SIP telephony integration with various providers:

```python
# Configure SIP provider
client.configure_sip_provider(
    provider="twilio",
    account_sid="your-twilio-sid",
    auth_token="your-twilio-token"
)

# Create phone number mapping
agent.map_to_phone_number("+15551234567")
```

## Extension Points

The SDK is designed to be extensible:

- Custom LLM providers
- Custom STT/TTS providers
- Custom tool implementations
- Custom telemetry handlers
- Custom workflow node types

## License Requirements

The SDK requires a valid license key to operate. This key is validated against the Knova AI licensing server during initialization and periodically during operation. For offline usage, the SDK caches license validation results.

Users can obtain a free license key by signing up on the Knova AI website.

## Installation

```bash
pip install knova-ai-sdk
```

## Examples

See the [examples directory](../examples/) for complete examples of using the SDK in various scenarios.
