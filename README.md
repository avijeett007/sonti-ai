# Knova AI: Open Source Voice AI Agent Platform

Knova AI is the world's first open source Voice AI Agent platform, providing a comprehensive solution for creating, managing, and deploying voice AI agents. Built on top of LiveKit's real-time communication infrastructure, Knova AI enables users to create single or multi-agent voice AI systems with support for knowledge bases, function calling, and multi-provider integration.

## Features

- **User Management System**: Registration/login functionality, user profile management, and API key management for various providers
- **Agent Creation & Management**: Create single and multi-prompt agents, enable multi-agent collaboration, integrate knowledge bases, and support function calling
- **Communication Channels**: Web-based voice communication, telephony integration, and future support for video and avatars
- **Infrastructure**: Kubernetes-based scalable architecture, independent agent containers, LiveKit integration, and Supabase for data management
- **Integration Capabilities**: Composio for tool/function integration, and support for multiple STT, TTS, and LLM providers

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

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/knova-ai.git
   cd knova-ai
   ```

2. Copy the example environment file and fill in your values:
   ```bash
   cp .env.example .env
   ```

3. Start the local development environment:
   ```bash
   docker-compose -f infrastructure/docker-compose.yml up -d
   ```

4. Install frontend dependencies and start the development server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. In a new terminal, install agent dependencies:
   ```bash
   cd agent
   pip install -r requirements.txt
   ```

6. Start the agent worker:
   ```bash
   cd agent
   python src/entrypoint.py
   ```

7. Open your browser and navigate to `http://localhost:3000`

### Documentation

- [Project Requirements](docs/project_requirements.md)
- [Architecture](docs/architecture.md)
- [Technical Specification](docs/technical_specification_part1.md)
- [Project Structure](docs/project_structure.md)

## Contributing

We welcome contributions to Knova AI! Please see our [contributing guidelines](CONTRIBUTING.md) for more information.

## License

Knova AI is open source software licensed under the [Apache 2.0 License](LICENSE).

## Acknowledgements

- [LiveKit](https://livekit.io/) for their excellent real-time communication infrastructure
- [Supabase](https://supabase.io/) for database and authentication
- [Next.js](https://nextjs.org/) for the frontend framework
- [Composio](https://composio.dev/) for function integration capabilities
