# Database Schema

## Overview

Knova AI uses a flexible database schema designed to support multiple database backends (SQLite, PostgreSQL, Supabase, NeonDB) while maintaining a consistent data model. The schema is optimized for storing configuration as JSON while still providing structured access to commonly queried fields.

## Core Entities

### Users

The `users` table stores information about platform users:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}'::jsonb
);
```

### ApiKeys

The `api_keys` table stores provider API keys for each user:

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    key_name VARCHAR(100) NOT NULL,
    key_value TEXT NOT NULL,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider, key_name)
);
```

### Agents

The `agents` table stores agent configurations:

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Index for faster JSON queries on common fields
CREATE INDEX agents_config_idx ON agents USING gin (config);
```

### Workflows

The `workflows` table stores workflow configurations:

```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Index for faster JSON queries
CREATE INDEX workflows_nodes_idx ON workflows USING gin (nodes);
CREATE INDEX workflows_edges_idx ON workflows USING gin (edges);
```

### KnowledgeBases

The `knowledge_bases` table stores knowledge base configurations:

```sql
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    vector_store VARCHAR(50) NOT NULL,
    embedding_model VARCHAR(100),
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Documents

The `documents` table stores documents in knowledge bases:

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### SipTrunks

The `sip_trunks` table stores SIP trunk configurations:

```sql
CREATE TABLE sip_trunks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL, -- 'inbound', 'outbound', 'both'
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### PhoneNumbers

The `phone_numbers` table maps phone numbers to agents:

```sql
CREATE TABLE phone_numbers (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    trunk_id UUID REFERENCES sip_trunks(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    -- Ensure only one of agent_id or workflow_id is set
    CHECK ((agent_id IS NULL AND workflow_id IS NOT NULL) OR 
           (agent_id IS NOT NULL AND workflow_id IS NULL))
);
```

### Webhooks

The `webhooks` table stores webhook configurations:

```sql
CREATE TABLE webhooks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    events JSONB NOT NULL, -- Array of event types this webhook subscribes to
    secret VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### CallLogs

The `call_logs` table records telephony activity:

```sql
CREATE TABLE call_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone_number_id UUID REFERENCES phone_numbers(id) ON DELETE SET NULL,
    call_sid VARCHAR(255) UNIQUE,
    direction VARCHAR(20) NOT NULL, -- 'inbound', 'outbound'
    from_number VARCHAR(20) NOT NULL,
    to_number VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    recording_url TEXT,
    transcript TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### UsageLogs

The `usage_logs` table tracks platform usage for telemetry:

```sql
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1,
    token_count INTEGER,
    provider VARCHAR(50),
    model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration JSON Structure

### Agent Configuration

Agent configurations are stored as JSON in the `config` field of the `agents` table:

```json
{
  "type": "voice",
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "settings": {
      "temperature": 0.7,
      "max_tokens": 500
    }
  },
  "stt": {
    "provider": "deepgram",
    "settings": {
      "model": "nova-2",
      "language": "en-US"
    }
  },
  "tts": {
    "provider": "elevenlabs",
    "settings": {
      "voice_id": "voice-id-here",
      "stability": 0.5,
      "similarity_boost": 0.7
    }
  },
  "prompt": "You are a helpful AI assistant...",
  "tools": ["search", "calculator"],
  "knowledge_base_id": "uuid-of-knowledge-base",
  "webhook_events": ["transcription", "response"]
}
```

### Workflow Configuration

Workflow configurations are stored in the `nodes` and `edges` fields of the `workflows` table:

```json
// nodes field
[
  {
    "id": "node1",
    "type": "agent",
    "data": {
      "agent_id": "uuid-of-agent",
      "agent_name": "Greeting Agent",
      "position": {"x": 100, "y": 100}
    }
  },
  {
    "id": "node2",
    "type": "condition",
    "data": {
      "name": "Check Intent",
      "condition_type": "keyword",
      "condition_value": ["account", "balance"],
      "position": {"x": 300, "y": 100}
    }
  }
]

// edges field
[
  {
    "source": "node1",
    "target": "node2",
    "condition": null
  }
]
```

### SIP Trunk Configuration

SIP trunk configurations are stored as JSON in the `config` field of the `sip_trunks` table:

```json
{
  "provider": "twilio",
  "credentials": {
    "account_sid": "sid-here",
    "auth_token": "token-here"
  },
  "sip_domain": "sip-domain-here.twilio.com",
  "inbound": {
    "webhook_url": "https://your-server/webhook/inbound",
    "fallback_url": "https://your-server/webhook/fallback"
  },
  "outbound": {
    "caller_id": "+15551234567",
    "recording": true
  }
}
```

## Database Provider Support

### SQLite

For local development and single-user deployments, SQLite provides a simple file-based database:

```python
# Example connection string
"sqlite:///path/to/knova.db"
```

### PostgreSQL

For production deployments, PostgreSQL offers better performance and concurrency:

```python
# Example connection string
"postgresql://username:password@localhost/knova"
```

### Supabase

For managed database services, Supabase provides PostgreSQL with additional features:

```python
# Example connection string
"postgresql://postgres:password@db.supabase.co:5432/postgres"
```

### NeonDB

Serverless PostgreSQL for scalable deployments:

```python
# Example connection string
"postgresql://user:password@ep-cool-snow-123456.us-east-2.aws.neon.tech/neondb"
```

## Schema Migrations

Database migrations are handled through a migration tool that supports all database backends. Migration scripts are located in the `migrations` directory and are applied in sequence.

To run migrations:

```bash
./scripts/db-migrate.sh
```

## Performance Considerations

1. **Indexing** - JSON fields are indexed using GIN indexes for performant queries
2. **Denormalization** - Common query fields are stored both in structured columns and JSON
3. **Caching** - The agent layer implements caching to reduce database load
4. **Connection Pooling** - For PostgreSQL deployments, connection pooling is recommended
