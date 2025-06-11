# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup and Development

```bash
# Initial setup
git clone https://github.com/your-org/knova-ai.git
cd knova-ai
cp .env.example .env
scripts/setup.sh

# Start local development environment
docker-compose -f infrastructure/docker-compose.yml up -d

# Frontend development
cd frontend
npm install
npm run dev          # Start development server on http://localhost:3000
npm run build        # Build for production
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
npm test             # Run tests

# Agent development
cd agent
pip install -r requirements.txt
python src/entrypoint.py        # Start agent worker
pytest                          # Run Python tests
```

### Testing

```bash
# Run all tests
scripts/test.sh

# Individual component tests
cd frontend && npm test
cd agent && pytest

# Local Kubernetes testing
minikube start
kubectl apply -f infrastructure/k8s/
```

### Deployment

```bash
# Deploy to staging/production
scripts/deploy.sh
```

## Architecture

### High-Level System Design

Knova AI is an open source Voice AI Agent platform with four main components:

1. **Frontend (Next.js 14+ with App Router)**
   - TypeScript-based React application
   - Tailwind CSS for styling
   - Supabase Auth integration
   - LiveKit Client SDK for real-time voice communication

2. **Backend Services**
   - Next.js API Routes for main application logic
   - Supabase for database and authentication
   - Redis for caching and pub/sub messaging

3. **Agent Runtime (Python 3.10+)**
   - LiveKit Agents Framework
   - Docker containers orchestrated by Kubernetes
   - Multi-agent collaboration with handoff capabilities
   - Multi-provider LLM support (OpenAI, Google, Azure, AWS, Anthropic, local models)

4. **Infrastructure**
   - Kubernetes-based scalable deployment
   - LiveKit for real-time communication
   - Vector databases (Qdrant/Pinecone) for knowledge bases

### Key Data Flow

1. Users create agents through the Next.js frontend
2. Agent configurations stored in Supabase
3. Python agent runtime containers deployed via Kubernetes
4. Real-time voice communication handled by LiveKit
5. Knowledge base queries processed through vector databases
6. Function calls executed via Composio integration

### Directory Structure

```
knova-ai/
├── frontend/          # Next.js application
├── backend/           # Backend services
├── agent/             # Python agent runtime
├── infrastructure/    # Kubernetes & Docker configs
├── scripts/          # Development and deployment scripts
└── docs/             # Technical documentation
```

### Database Schema (Supabase)

Core tables: Users, Agents, Knowledge_Bases, Documents, Functions, Sessions, Analytics
- JWT-based authentication with role-based access control
- Agent configurations include provider settings, prompts, and function registrations
- Knowledge bases support vector embeddings for document retrieval

### Agent Wrapper Design

The Python agent wrapper provides:
- Simplified agent creation and configuration
- License validation and telemetry collection
- Multi-provider LLM integration
- SQLite-based local configuration storage
- Webhook support for external integrations

### Communication Channels

- **Web**: LiveKit WebRTC for browser-based voice communication
- **Telephony**: SIP integration for phone-based interactions
- **Future**: Video and avatar support planned

### Security Architecture

- Data encryption: AES-256 at rest, TLS 1.3 in transit
- GDPR/CCPA compliance frameworks
- Comprehensive audit logging
- API rate limiting and input validation

## Development Guidelines

### Code Architecture Patterns

- **Frontend**: React components with TypeScript, state management via React hooks
- **Backend**: RESTful API design with Next.js API routes
- **Agent**: Event-driven architecture with LiveKit Agents Framework
- **Infrastructure**: GitOps-style Kubernetes deployments

### Testing Strategy

- Frontend: Jest and React Testing Library
- Backend: API integration tests
- Agent: pytest with mocking for external services
- End-to-end: Playwright for full user workflows

### Deployment Strategy

- Blue/green deployments for zero downtime
- Canary releases for gradual rollouts
- Kubernetes horizontal pod autoscaling
- Automated rollbacks for failed deployments

### Environment Configuration

- **Development**: Local Docker Compose setup
- **Staging**: Minikube or cloud Kubernetes
- **Production**: Full Kubernetes cluster with LiveKit Cloud

### Monitoring and Observability

- Prometheus metrics collection
- Grafana dashboards
- Structured JSON logging with OpenTelemetry
- Alert conditions for error rates, latency, and resource usage

## Agent Development

### Basic Agent Creation

```python
from knova_ai import KnovaAI

knova = KnovaAI(license_key="your-key")
agent_id = knova.create_agent(config)
deployment = await knova.deploy_agent(agent_id)
```

### Multi-Agent Collaboration

Agents can collaborate through:
- Session handoffs between specialized agents
- Shared context and knowledge bases
- Function calling between agents
- Real-time communication coordination

### Knowledge Base Integration

- Vector database support for document retrieval
- Supported formats: PDF, DOCX, TXT, HTML, JSON, CSV
- Document processing pipeline with chunking and embedding
- LangChain/LlamaIndex integration for document ingestion