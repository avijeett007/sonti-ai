# Knova AI SDK

Open-source Voice AI Agent platform SDK for Python.

## Installation

```bash
pip install knova-ai
```

## Quick Start

```python
from knova_ai import KnovaAI

# Initialize with license key
knova = KnovaAI(license_key="your-free-tier-key")

# Create a simple agent
agent = knova.create_agent(
    name="Customer Support",
    llm_provider="openai",
    llm_model="gpt-4",
    stt_provider="deepgram",
    tts_provider="elevenlabs"
)

# Deploy agent
deployment = await knova.deploy_agent(agent)
```

## Features

- 🎯 Simple agent creation API
- 🔑 License key enforcement (free tier available)
- 📊 Built-in telemetry collection
- 🔧 Multi-provider support (OpenAI, Google, Azure, AWS, Anthropic)
- 🎙️ STT/TTS configuration
- 🔄 LiveKit integration for real-time communication
- 📱 SIP telephony support (Twilio, Telnyx, Plivo)

## Documentation

For full documentation, visit [https://docs.knova.ai](https://docs.knova.ai)

## License

MIT License - see LICENSE file for details.