# Agent Layer Architecture

## Overview

The Agent Layer is the runtime component of Knova AI that powers voice agents and workflows. It is designed to be minimal, dynamic, and configurable, relying on the Knova AI SDK for core functionality while handling the real-time communication aspects of agent interactions.

## Key Principles

1. **Minimal Implementation** - The agent layer contains only the necessary code to coordinate with LiveKit, load configurations from the database, and instantiate agents through the SDK.

2. **Dynamic Configuration** - All agent settings, including LLM, STT, and TTS provider credentials, are loaded from the database at runtime.

3. **Hot Reloading** - The agent layer periodically checks for configuration updates, allowing changes made in the frontend to be applied without restarting.

4. **Stateless Design** - Each agent instance is stateless and acquires all necessary state from the database, enabling horizontal scaling.

5. **License Verification** - The agent layer validates the license key against the Knova AI licensing service.

## Component Architecture

```
┌─────────────────────────────────────────┐
│              Agent Layer                │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐      ┌─────────────┐   │
│  │   Worker    │      │  Database   │   │
│  │  Manager    │◄────►│  Connector  │   │
│  └─────────────┘      └─────────────┘   │
│         │                    │          │
│         ▼                    ▼          │
│  ┌─────────────┐      ┌─────────────┐   │
│  │  LiveKit    │      │ Config      │   │
│  │  Client     │      │ Manager     │   │
│  └─────────────┘      └─────────────┘   │
│         │                    │          │
│         └────────┬───────────┘          │
│                  │                      │
│                  ▼                      │
│  ┌─────────────────────────────────┐    │
│  │        Knova AI SDK             │    │
│  │  (Agent Creation & Execution)   │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

## Key Components

### Worker Manager

The Worker Manager is responsible for:
- Creating and managing LiveKit agent workers
- Handling room events (participant joining/leaving)
- Coordinating agent lifecycle (start, stop, pause)
- Managing concurrency and resource allocation

### Database Connector

The Database Connector:
- Provides an abstraction over different database backends (SQLite, Postgres, etc.)
- Loads agent configurations, workflows, and credentials
- Caches frequently accessed data for performance
- Monitors database for changes to support hot reloading

### Configuration Manager

The Configuration Manager:
- Parses and validates JSON configurations
- Handles versioning of configurations
- Supplies configuration to the SDK components
- Manages environment-specific overrides

### LiveKit Client

The LiveKit Client:
- Manages LiveKit room connections
- Handles media track publishing/subscribing
- Processes room events
- Implements WebRTC communication

## Configuration Flow

1. **Startup**
   - Agent layer loads license key from environment variables
   - Validates license with Knova AI licensing service
   - Connects to configured database
   - Initializes the Knova AI SDK

2. **Agent Loading**
   - When a participant joins a room, the agent ID is extracted
   - Configuration for that agent is loaded from database
   - Agent instance is created via the SDK with loaded configuration
   - Agent joins the LiveKit room

3. **Hot Reloading**
   - Periodic checks for configuration changes
   - If changes detected, agent is gracefully restarted
   - New configuration applied without service interruption

## SIP Integration

The agent layer integrates with SIP providers (Twilio, Telnyx, Plivo) to enable telephone connectivity:

1. **Inbound Calls**
   - SIP provider forwards call to LiveKit SIP connector
   - Agent layer matches incoming number to configured agent
   - Call is connected to appropriate LiveKit room
   - Agent loads configuration and handles the call

2. **Outbound Calls**
   - Agent initiates call via SDK
   - SIP configuration loaded from database
   - Call routed through configured SIP trunk
   - Called party connected to LiveKit room

## Webhook Support

The agent layer supports webhooks for:

1. **Telemetry**
   - Usage statistics and metrics
   - Error reporting
   - License validation events

2. **Call Events**
   - Call start/end events
   - Transcription events
   - Agent state changes

3. **External Integration**
   - Third-party system notifications
   - Custom event triggers
   - Analytics integration

## Deployment Options

The agent layer can be deployed in various ways:

1. **Docker Container**
   - Bundled with all dependencies
   - Environment variables for configuration
   - Volume mounts for persistent storage
   - Designed for container orchestration

2. **Kubernetes Pod**
   - Horizontally scalable deployment
   - Configured via ConfigMaps and Secrets
   - Health probes for reliability
   - Resource limits for performance

3. **Virtual Machine**
   - Systemd service for process management
   - Log rotation and monitoring
   - Manual scaling as needed

## Configuration Requirements

The agent layer requires these minimum configuration items:

1. **License Key**
   - Valid Knova AI license key

2. **Database Connection**
   - Connection string for supported database

3. **LiveKit Configuration**
   - API Key, API Secret
   - LiveKit server URL

4. **Environment Settings**
   - Log level
   - Performance tuning parameters
   - Webhook endpoints
