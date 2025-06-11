# Backend API Reference

## Overview

The Knova AI backend provides a RESTful API for the frontend and SDK to interact with the platform. It handles license validation, user management, agent configuration, workflow management, and database operations.

## Authentication

All API endpoints except for health checks and public endpoints require authentication:

```
Authorization: Bearer {api_token}
```

API tokens are generated during setup and can be refreshed through the admin interface.

## Base URL

```
https://your-instance-url/api/v1
```

## Endpoints

### Authentication

#### Login

```
POST /auth/login
```

Request:
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response:
```json
{
  "token": "jwt-token-here",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

### License Management

#### Validate License

```
POST /license/validate
```

Request:
```json
{
  "license_key": "KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-A7F4E"
}
```

Response:
```json
{
  "valid": true,
  "tier": "free",
  "expires_at": "2025-12-31T23:59:59Z",
  "features": ["voice_agents", "workflows", "knowledge_base"]
}
```

### Agent Management

#### List Agents

```
GET /agents
```

Response:
```json
{
  "agents": [
    {
      "id": "agent-uuid-1",
      "name": "Customer Support",
      "type": "voice",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-02T15:30:00Z",
      "is_active": true
    },
    {
      "id": "agent-uuid-2",
      "name": "Sales Assistant",
      "type": "voice",
      "created_at": "2025-01-03T10:00:00Z",
      "updated_at": "2025-01-03T10:00:00Z",
      "is_active": true
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

#### Get Agent

```
GET /agents/{agent_id}
```

Response:
```json
{
  "id": "agent-uuid-1",
  "name": "Customer Support",
  "description": "Handles customer inquiries and support tickets",
  "type": "voice",
  "config": {
    "llm": {
      "provider": "openai",
      "model": "gpt-4",
      "settings": {
        "temperature": 0.7
      }
    },
    "stt": {
      "provider": "deepgram",
      "settings": {
        "model": "nova-2"
      }
    },
    "tts": {
      "provider": "elevenlabs",
      "settings": {
        "voice_id": "voice-id-here"
      }
    },
    "prompt": "You are a helpful customer support agent...",
    "tools": ["search", "ticket_lookup"],
    "knowledge_base_id": "kb-uuid-here"
  },
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-02T15:30:00Z",
  "is_active": true
}
```

#### Create Agent

```
POST /agents
```

Request:
```json
{
  "name": "New Agent",
  "description": "Description of the new agent",
  "type": "voice",
  "config": {
    "llm": {
      "provider": "openai",
      "model": "gpt-4"
    },
    "stt": {
      "provider": "deepgram"
    },
    "tts": {
      "provider": "elevenlabs",
      "settings": {
        "voice_id": "voice-id-here"
      }
    },
    "prompt": "You are a helpful assistant..."
  }
}
```

Response:
```json
{
  "id": "new-agent-uuid",
  "name": "New Agent",
  "description": "Description of the new agent",
  "type": "voice",
  "config": {
    "llm": {
      "provider": "openai",
      "model": "gpt-4",
      "settings": {}
    },
    "stt": {
      "provider": "deepgram",
      "settings": {}
    },
    "tts": {
      "provider": "elevenlabs",
      "settings": {
        "voice_id": "voice-id-here"
      }
    },
    "prompt": "You are a helpful assistant..."
  },
  "created_at": "2025-06-11T10:30:00Z",
  "updated_at": "2025-06-11T10:30:00Z",
  "is_active": true
}
```

#### Update Agent

```
PUT /agents/{agent_id}
```

Request:
```json
{
  "name": "Updated Agent Name",
  "description": "Updated description",
  "config": {
    "llm": {
      "provider": "anthropic",
      "model": "claude-3"
    }
  }
}
```

Response: Same as Get Agent

#### Delete Agent

```
DELETE /agents/{agent_id}
```

Response:
```json
{
  "success": true,
  "message": "Agent deleted successfully"
}
```

### Workflow Management

#### List Workflows

```
GET /workflows
```

Response:
```json
{
  "workflows": [
    {
      "id": "workflow-uuid-1",
      "name": "Customer Onboarding",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-02T15:30:00Z",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

#### Get Workflow

```
GET /workflows/{workflow_id}
```

Response:
```json
{
  "id": "workflow-uuid-1",
  "name": "Customer Onboarding",
  "description": "Workflow for new customer onboarding",
  "nodes": [
    {
      "id": "node1",
      "type": "agent",
      "data": {
        "agent_id": "agent-uuid-1",
        "position": {"x": 100, "y": 100}
      }
    },
    {
      "id": "node2",
      "type": "condition",
      "data": {
        "condition_type": "intent",
        "position": {"x": 300, "y": 100}
      }
    }
  ],
  "edges": [
    {
      "source": "node1",
      "target": "node2"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-02T15:30:00Z",
  "is_active": true
}
```

#### Create Workflow

```
POST /workflows
```

Request:
```json
{
  "name": "New Workflow",
  "description": "Description of new workflow",
  "nodes": [
    {
      "id": "start",
      "type": "agent",
      "data": {
        "agent_id": "agent-uuid-1",
        "position": {"x": 100, "y": 100}
      }
    }
  ],
  "edges": []
}
```

Response: Similar to Get Workflow with a new ID

### Knowledge Base Management

#### List Knowledge Bases

```
GET /knowledge-bases
```

Response:
```json
{
  "knowledge_bases": [
    {
      "id": "kb-uuid-1",
      "name": "Product Documentation",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-02T15:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

#### Upload Document

```
POST /knowledge-bases/{kb_id}/documents
```

Request:
```
Content-Type: multipart/form-data

file: [binary data]
metadata: {"title": "Product Manual", "tags": ["manual", "product"]}
```

Response:
```json
{
  "id": "doc-uuid-1",
  "filename": "product_manual.pdf",
  "file_type": "application/pdf",
  "file_size": 1024567,
  "status": "processing",
  "created_at": "2025-06-11T10:35:00Z"
}
```

### SIP Trunk Management

#### List SIP Trunks

```
GET /sip-trunks
```

Response:
```json
{
  "sip_trunks": [
    {
      "id": "trunk-uuid-1",
      "name": "Twilio Main",
      "provider": "twilio",
      "direction": "both",
      "created_at": "2025-01-01T12:00:00Z",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

#### Create Phone Number Mapping

```
POST /phone-numbers
```

Request:
```json
{
  "phone_number": "+15551234567",
  "trunk_id": "trunk-uuid-1",
  "agent_id": "agent-uuid-1"
}
```

Response:
```json
{
  "id": "pn-uuid-1",
  "phone_number": "+15551234567",
  "trunk_id": "trunk-uuid-1",
  "agent_id": "agent-uuid-1",
  "created_at": "2025-06-11T10:40:00Z",
  "is_active": true
}
```

### Webhook Management

#### Register Webhook

```
POST /webhooks
```

Request:
```json
{
  "name": "Call Events",
  "url": "https://your-server.com/webhook",
  "events": ["call.started", "call.ended", "transcription"],
  "secret": "webhook-secret-for-signing"
}
```

Response:
```json
{
  "id": "webhook-uuid-1",
  "name": "Call Events",
  "url": "https://your-server.com/webhook",
  "events": ["call.started", "call.ended", "transcription"],
  "created_at": "2025-06-11T10:45:00Z",
  "is_active": true
}
```

### Call Logs

#### List Call Logs

```
GET /call-logs
```

Response:
```json
{
  "call_logs": [
    {
      "id": "call-uuid-1",
      "call_sid": "CA12345",
      "direction": "inbound",
      "from_number": "+15551234567",
      "to_number": "+15557654321",
      "status": "completed",
      "duration": 125,
      "started_at": "2025-06-11T10:00:00Z",
      "ended_at": "2025-06-11T10:02:05Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

### Health Check

#### Get Health Status

```
GET /health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "db_connected": true,
  "license_valid": true
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes and structured error responses:

```json
{
  "error": true,
  "code": "invalid_license",
  "message": "The provided license key is invalid or has expired",
  "details": {
    "license_key": "KNOVA-FREE-invalid-key"
  }
}
```

Common error codes:

- `unauthorized`: Authentication failed
- `invalid_license`: License validation failed
- `not_found`: Requested resource not found
- `validation_error`: Request validation failed
- `db_error`: Database operation failed
- `api_error`: General API error

## Rate Limiting

API endpoints are rate-limited based on the license tier. Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623417600
```

## Versioning

The API uses URL versioning (v1, v2, etc.). Breaking changes will only be introduced with version increments.

## WebSocket API

In addition to the REST API, the backend provides WebSocket endpoints for real-time communication:

```
wss://your-instance-url/ws/v1/{feature}
```

Available WebSocket features:

- `agent-logs`: Real-time agent execution logs
- `call-events`: Real-time call events
- `metrics`: Real-time usage metrics

Authentication is performed using a query parameter:

```
wss://your-instance-url/ws/v1/agent-logs?token=jwt-token-here
```
