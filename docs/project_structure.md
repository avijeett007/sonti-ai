# Knova AI: Project Structure

This document outlines the directory structure and key files for the Knova AI platform.

## Repository Structure

```
knova-ai/
├── .github/                      # GitHub workflows and templates
│   └── workflows/                # CI/CD workflows
├── docs/                         # Documentation
│   ├── project_requirements.md   # Project requirements
│   ├── architecture.md           # Architecture document
│   ├── technical_specification_*.md # Technical specifications
│   └── project_structure.md      # This document
├── frontend/                     # Next.js frontend application
│   ├── app/                      # Next.js App Router
│   ├── components/               # React components
│   ├── lib/                      # Utility functions and helpers
│   ├── public/                   # Static assets
│   ├── styles/                   # Global styles
│   ├── next.config.js            # Next.js configuration
│   ├── package.json              # Frontend dependencies
│   └── tsconfig.json             # TypeScript configuration
├── backend/                      # Backend services
│   ├── api/                      # API routes (if not using Next.js API routes)
│   ├── services/                 # Backend services
│   ├── models/                   # Data models
│   ├── utils/                    # Utility functions
│   ├── package.json              # Backend dependencies
│   └── tsconfig.json             # TypeScript configuration
├── agent/                        # Agent runtime
│   ├── src/                      # Agent source code
│   │   ├── agent.py              # Agent implementation
│   │   ├── knowledge_base.py     # Knowledge base connector
│   │   ├── function_registry.py  # Function registry
│   │   ├── tools/                # Tool implementations
│   │   ├── providers/            # Provider implementations
│   │   └── utils/                # Utility functions
│   ├── Dockerfile                # Agent container definition
│   ├── requirements.txt          # Python dependencies
│   └── tests/                    # Agent tests
├── infrastructure/               # Infrastructure as Code
│   ├── kubernetes/               # Kubernetes manifests
│   │   ├── frontend/             # Frontend deployment
│   │   ├── backend/              # Backend deployment
│   │   ├── agent/                # Agent deployment
│   │   └── databases/            # Database deployments
│   ├── terraform/                # Terraform configurations
│   │   ├── aws/                  # AWS infrastructure
│   │   ├── gcp/                  # GCP infrastructure
│   │   └── azure/                # Azure infrastructure
│   └── docker-compose.yml        # Local development setup
├── scripts/                      # Utility scripts
│   ├── setup.sh                  # Setup script
│   ├── deploy.sh                 # Deployment script
│   └── test.sh                   # Test script
├── .env.example                  # Example environment variables
├── README.md                     # Project README
└── LICENSE                       # Open source license
```

## Key Components

### Frontend Application

The frontend application is built with Next.js and provides the user interface for creating, managing, and monitoring voice AI agents.

#### Key Files

- `frontend/app/layout.tsx`: Root layout component
- `frontend/app/page.tsx`: Landing page
- `frontend/app/auth/login/page.tsx`: Login page
- `frontend/app/auth/register/page.tsx`: Registration page
- `frontend/app/dashboard/page.tsx`: User dashboard
- `frontend/app/agents/page.tsx`: Agent listing page
- `frontend/app/agents/[agent_id]/page.tsx`: Agent details page
- `frontend/app/agents/[agent_id]/edit/page.tsx`: Agent editing page
- `frontend/app/agents/[agent_id]/test/page.tsx`: Agent testing interface
- `frontend/components/AgentBuilder.tsx`: Agent configuration component
- `frontend/components/KnowledgeBaseUploader.tsx`: Knowledge base management component
- `frontend/components/FunctionRegistry.tsx`: Function configuration component
- `frontend/lib/api.ts`: API client
- `frontend/lib/livekit.ts`: LiveKit client utilities

### Backend Services

The backend services handle business logic, authentication, and communication with external services.

#### Key Files

- `backend/api/auth.ts`: Authentication endpoints
- `backend/api/agents.ts`: Agent management endpoints
- `backend/api/knowledge-base.ts`: Knowledge base endpoints
- `backend/api/functions.ts`: Function registry endpoints
- `backend/api/livekit.ts`: LiveKit integration endpoints
- `backend/services/AgentService.ts`: Agent management service
- `backend/services/KnowledgeBaseService.ts`: Knowledge base service
- `backend/services/FunctionService.ts`: Function registry service
- `backend/models/Agent.ts`: Agent data model
- `backend/models/KnowledgeBase.ts`: Knowledge base data model
- `backend/models/Function.ts`: Function data model
- `backend/utils/supabase.ts`: Supabase client utilities

### Agent Runtime

The agent runtime is responsible for executing the voice AI agents in a scalable, containerized environment.

#### Key Files

- `agent/src/agent.py`: Main agent implementation
- `agent/src/entrypoint.py`: Agent entrypoint
- `agent/src/knowledge_base.py`: Knowledge base connector
- `agent/src/function_registry.py`: Function registry
- `agent/src/providers/stt_provider.py`: Speech-to-text provider implementations
- `agent/src/providers/llm_provider.py`: LLM provider implementations
- `agent/src/providers/tts_provider.py`: Text-to-speech provider implementations
- `agent/src/tools/knowledge_base_tools.py`: Knowledge base tool implementations
- `agent/src/tools/function_tools.py`: Function execution tools
- `agent/src/utils/logging.py`: Logging utilities
- `agent/Dockerfile`: Agent container definition

### Infrastructure

The infrastructure code defines the deployment configuration for the Knova AI platform.

#### Key Files

- `infrastructure/kubernetes/frontend/deployment.yaml`: Frontend deployment
- `infrastructure/kubernetes/backend/deployment.yaml`: Backend deployment
- `infrastructure/kubernetes/agent/deployment.yaml`: Agent deployment
- `infrastructure/kubernetes/databases/supabase.yaml`: Supabase deployment
- `infrastructure/kubernetes/databases/redis.yaml`: Redis deployment
- `infrastructure/terraform/main.tf`: Main Terraform configuration
- `infrastructure/docker-compose.yml`: Local development setup

## Development Setup

To set up the development environment:

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in the required values
3. Run `scripts/setup.sh` to install dependencies
4. Run `docker-compose -f infrastructure/docker-compose.yml up` to start local services
5. Run `cd frontend && npm run dev` to start the frontend application

## Deployment

To deploy the Knova AI platform:

1. Set up a Kubernetes cluster
2. Configure the necessary secrets and environment variables
3. Run `scripts/deploy.sh` to deploy the application

## Testing

To run tests:

1. Run `scripts/test.sh` to run all tests
2. Run `cd frontend && npm test` to run frontend tests
3. Run `cd agent && pytest` to run agent tests
