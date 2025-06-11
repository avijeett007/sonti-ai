# Knova AI: Architecture Overview

## System Architecture

Knova AI is designed as a modern, extensible platform for creating, managing, and deploying voice AI agents. The system consists of several key components:

1. **Knova AI SDK (PyPI Package)**
   - Core library providing unified interfaces for agent creation
   - License validation and telemetry collection
   - Provider abstraction for LLM, STT, TTS services
   - Released as a separate open-source package
   - Serves as the foundation for the agent layer

2. **Agent Layer**
   - Minimal implementation powered by Knova AI SDK
   - Configurable via database-stored JSON
   - Integration with LiveKit/WebRTC for real-time communication
   - SIP telephony support via multiple providers
   - Hot-reload capability for configuration changes

3. **Frontend**
   - Next.js application with visual workflow builder
   - Infinite design pallet for agent/workflow orchestration
   - Simple and advanced interfaces for different user needs
   - Agent configuration and management
   - Knowledge base management

4. **Backend**
   - API for frontend communication
   - License validation
   - User management
   - Database interactions

5. **Database**
   - Multi-provider support (SQLite3, Supabase, NeonDB, Postgres)
   - Stores agent configurations, workflows, user data
   - Flexible schema for different deployment scenarios

## Component Relationships

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │◄────┤     Backend     │◄────┤  Agent Layer    │
│  (Next.js App)  │     │   (API Server)  │     │ (LiveKit Agent) │
│                 │     │                 │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └─────────────►│    Database     │◄─────────────┘
                        │                 │
                        └─────────────────┘
                                │
                                │
                        ┌───────▼───────┐
                        │               │
                        │  Knova AI SDK │
                        │  (PyPI Pkg)   │
                        │               │
                        └───────────────┘
```

## Licensing Flow

1. User signs up on the Knova AI website
2. User generates a free license key 
3. User installs the open-source Knova AI platform
4. User configures the license key in frontend settings and agent environment
5. System validates license key against Knova AI's API service
6. Platform becomes fully operational once license is validated

## Configuration Management

All configurations for agents, workflows, LLM/STT/TTS providers, and telephony are stored as JSON in the database, which allows:

- Dynamic loading at runtime
- Hot reloading when configurations change
- Centralized management via the frontend
- Easy backup and migration

## Communication Flows

### Agent Creation and Deployment
1. User creates agent configuration via frontend
2. Configuration is stored in database via backend API
3. Agent layer loads configuration when needed
4. LiveKit room is created for the agent
5. Agent uses credentials from configuration to initialize services

### Call Handling
1. Inbound call arrives via configured SIP trunk
2. Agent layer loads appropriate agent configuration
3. LiveKit session is established
4. Agent processes audio via configured STT provider
5. Agent generates responses via configured LLM provider
6. Responses are synthesized via configured TTS provider
7. Audio is streamed back to caller

### Webhook and Telemetry
1. Agent operations generate events
2. Events are processed by the SDK's telemetry module
3. Data is sent to configured webhook endpoints
4. Analytics can be viewed in the frontend dashboard

## Deployment Options

1. **Local Development**
   - Docker Compose for all services
   - SQLite database for persistence
   - Local LiveKit server

2. **Production Self-Hosted**
   - Kubernetes deployment
   - PostgreSQL or Supabase for database
   - Self-hosted or cloud LiveKit server

3. **Cloud-Native Deployment**
   - Managed Kubernetes services
   - Cloud database services
   - LiveKit Cloud for media services
