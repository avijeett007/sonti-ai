# Knova AI: Architecture Document

## System Architecture Overview

Knova AI is designed as a modern, cloud-native application with a clear separation of concerns between its components. The architecture follows microservices principles to ensure scalability, maintainability, and flexibility.

![Knova AI Architecture](../assets/architecture_diagram.png)

## Core Components

### 1. Frontend Application (Next.js)

The frontend application provides the user interface for creating, managing, and monitoring voice AI agents.

**Key Technologies:**
- Next.js 14+ (React framework)
- TypeScript
- Tailwind CSS for styling
- LiveKit Client SDK for real-time communication
- Authentication via Supabase Auth

**Key Features:**
- User authentication and profile management
- Agent creation and configuration interface
- Knowledge base management
- Function/tool integration interface
- Agent monitoring and analytics dashboard
- Testing interface for agents

### 2. Backend Services (Next.js API Routes + Dedicated Services)

The backend handles business logic, authentication, and communication with external services.

**Key Technologies:**
- Next.js API Routes for main application backend
- Node.js for dedicated services
- TypeScript
- Supabase for database and authentication
- Redis for caching and pub/sub

**Key Services:**
- **Authentication Service**: Handles user registration, login, and session management
- **Agent Management Service**: Manages agent configurations, versions, and deployments
- **Knowledge Base Service**: Handles document ingestion, processing, and retrieval
- **Function Registry Service**: Manages available functions and their configurations
- **Analytics Service**: Collects and processes usage and performance data

### 3. Agent Runtime (Python-based)

The agent runtime is responsible for executing the voice AI agents in a scalable, containerized environment.

**Key Technologies:**
- Python 3.10+
- LiveKit Agents Framework
- Docker for containerization
- Kubernetes for orchestration

**Components:**
- **Agent Worker**: Manages the lifecycle of agent instances
- **Speech Pipeline**: Handles STT, LLM processing, and TTS
- **Function Execution Engine**: Executes tools and functions
- **Knowledge Base Connector**: Retrieves relevant information from knowledge bases
- **Monitoring & Logging**: Captures performance metrics and logs

### 4. Infrastructure Layer

The infrastructure layer provides the foundation for running the entire system.

**Key Technologies:**
- Kubernetes for container orchestration
- LiveKit for real-time communication
- Supabase for database and authentication
- Redis for caching and messaging
- Object Storage (S3-compatible) for file storage

## Data Flow

### Agent Creation Flow

1. User authenticates via the Next.js frontend
2. User creates a new agent through the UI, configuring:
   - Agent name and description
   - System prompts and behavior parameters
   - Knowledge base connections
   - Function/tool integrations
   - STT and TTS provider selections
3. Configuration is saved to Supabase
4. Agent is ready for deployment

### Agent Deployment Flow

1. User initiates agent deployment from the UI
2. Backend validates the configuration
3. Kubernetes creates a new agent container with the specified configuration
4. Agent container registers with the LiveKit server
5. Agent is now ready to accept connections

### Communication Flow

1. Client connects to a LiveKit room with the agent_id as metadata
2. LiveKit server routes the connection to the appropriate agent
3. Agent container:
   - Loads configuration based on agent_id
   - Initializes STT, LLM, and TTS components
   - Establishes connection with the client
4. Real-time communication begins:
   - Audio from client is processed by STT
   - Transcribed text is sent to LLM
   - LLM response is processed by TTS
   - Generated speech is sent back to client
5. Function calls and knowledge base queries happen as needed during the conversation

## Scalability Considerations

### Horizontal Scaling

- Agent containers can scale horizontally based on demand
- LiveKit servers can be distributed across regions for global coverage
- Backend services are stateless and can scale independently

### Resource Optimization

- Agents are containerized and only consume resources when active
- Knowledge bases use vector databases for efficient retrieval
- Caching layers for frequently accessed data

## Security Architecture

### Authentication & Authorization

- JWT-based authentication for users and services
- Role-based access control for agent management
- API key management for external service integration

### Data Protection

- Encryption at rest for all stored data
- Encryption in transit for all communications
- Secure storage of API keys and credentials

### Compliance

- Privacy-by-design principles
- Data minimization and purpose limitation
- Audit logging for security-relevant events

## Integration Points

### AI Provider Integrations

- OpenAI (GPT models, Whisper STT, TTS)
- Google (Gemini models, Speech-to-Text, Text-to-Speech)
- Azure (Azure OpenAI, Azure Speech Services)
- AWS (Bedrock, Transcribe, Polly)
- Anthropic (Claude models)
- Local models via Ollama

### Tool & Function Integrations

- Composio for simplified tool integration
- Custom function registry
- Webhook support for external service integration

### Communication Integrations

- WebRTC for web-based communication
- SIP/telephony integration via LiveKit
- Future: Video and avatar support

## Monitoring & Observability

- Prometheus for metrics collection
- Grafana for visualization
- Distributed tracing with OpenTelemetry
- Centralized logging

## Deployment Architecture

### Development Environment

- Local Docker Compose setup
- Minikube for local Kubernetes testing
- Supabase local development

### Production Environment

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- LiveKit Cloud or self-hosted LiveKit
- Supabase or PostgreSQL + Auth solution
- Redis cluster
- Object storage (S3, GCS, etc.)

## Disaster Recovery & High Availability

- Multi-region deployment capability
- Database replication and backups
- Stateless services for easy recovery
- Automated failover mechanisms
