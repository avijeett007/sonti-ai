# Knova AI

Open-source Voice AI Agent platform with multi-provider support, visual workflows, and enterprise-ready features.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![Node](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

## Features

- 🎯 **Simple Python SDK** - Create voice agents with just a few lines of code
- 🔧 **Multi-Provider Support** - OpenAI, Google, Azure, AWS, Anthropic, and local models
- 🎙️ **Advanced Voice Capabilities** - STT/TTS with multiple providers
- 📱 **SIP Telephony** - Built-in support for Twilio, Telnyx, and Plivo
- 🔄 **Visual Workflow Builder** - Drag-and-drop multi-agent orchestration
- 📊 **Knowledge Bases** - Vector database integration for document retrieval
- 🔑 **License Management** - Free tier with optional enterprise features
- 🚀 **Kubernetes Ready** - Scalable deployment with auto-scaling

## Quick Start

### Using the Python SDK

```python
from knova_ai import KnovaAI

# Initialize with your license key
knova = KnovaAI(license_key="your-free-tier-key")

# Create a voice agent
agent = knova.create_agent(
    name="Customer Support",
    llm_provider="openai",
    llm_model="gpt-4",
    stt_provider="deepgram",
    tts_provider="elevenlabs"
)

# Deploy the agent
deployment = await knova.deploy_agent(agent)
print(f"Agent deployed at: {deployment['endpoint']}")
```

## Architecture

Knova AI is designed as a modern, cloud-native application with a clear separation of concerns between its components:

1. **Frontend Application (Next.js)**: Provides the user interface for creating, managing, and monitoring voice AI agents
2. **Backend Services**: Handle business logic, authentication, and communication with external services
3. **Agent Runtime (Python-based)**: Executes the voice AI agents in a scalable, containerized environment
4. **Infrastructure Layer**: Provides the foundation for running the entire system

For more details, see the [architecture document](docs/architecture.md).

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- Docker and Docker Compose
- Kubernetes (for production deployment)
- LiveKit account (or self-hosted LiveKit server)
- Supabase account (or self-hosted Supabase)

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/avijeett007/knova-ai.git
cd knova-ai
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the setup script:
```bash
./scripts/setup.sh
```

4. Start the development environment:
```bash
# Using Docker Compose
cd infrastructure
docker-compose up

# Or run components individually:
# Frontend
cd frontend && npm run dev

# Agent worker
cd agent && python src/main.py
```

5. Access the application at http://localhost:3000

## Testing

Run all tests:
```bash
./scripts/test.sh
```

## Deployment

### Docker Compose (Development)
```bash
cd infrastructure
docker-compose up
```

### Kubernetes (Production)
```bash
./scripts/deploy.sh
```

### Documentation

- [Project Requirements](docs/project_requirements.md)
- [Architecture](docs/architecture.md)
- [Technical Specification](docs/technical_specification_part1.md)
- [Project Structure](docs/project_structure.md)

## Contributing

We welcome contributions to Knova AI! Please see our [contributing guidelines](CONTRIBUTING.md) for more information.

## Support

- Documentation: https://docs.knova.ai
- Issues: https://github.com/avijeett007/knova-ai/issues
- Discord: https://discord.gg/knova-ai

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgements

- [LiveKit](https://livekit.io/) for their excellent real-time communication infrastructure
- [Supabase](https://supabase.io/) for database and authentication
- [Next.js](https://nextjs.org/) for the frontend framework
- [Composio](https://composio.dev/) for function integration capabilities
