# Knova AI SDK API Reference

## Core Classes

### KnovaAI

The main client class for interacting with the Knova AI platform.

```python
from knova_ai import KnovaAI

client = KnovaAI(
    license_key="your-license-key",
    database_config={
        "type": "sqlite",  # or "supabase", "postgres", "neondb"
        "path": "local.db", # for sqlite
        # OR
        "connection_string": "postgresql://..." # for other DB types
    },
    telemetry_options={
        "enabled": True,
        "webhook_url": "https://your-webhook.com/events",
        "metrics": ["api_calls", "agent_runtime", "transcription"]
    }
)
```

#### Methods

##### `__init__`

```python
def __init__(
    self,
    license_key: str,
    database_config: Optional[Dict[str, Any]] = None,
    telemetry_options: Optional[Dict[str, Any]] = None,
    api_url: Optional[str] = None
) -> None
```

Creates a new KnovaAI client instance.

- `license_key`: Your Knova AI license key
- `database_config`: Configuration for database connection
- `telemetry_options`: Configuration for telemetry collection
- `api_url`: Optional override for the API URL

##### `create_agent`

```python
def create_agent(
    self,
    name: str,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4",
    stt_provider: str = "deepgram",
    tts_provider: str = "elevenlabs",
    prompt: Optional[str] = None,
    tools: Optional[List[str]] = None,
    knowledge_base_id: Optional[str] = None,
    **kwargs
) -> VoiceAgent
```

Creates a new voice agent.

- `name`: Name of the agent
- `llm_provider`: LLM provider name
- `llm_model`: LLM model name
- `stt_provider`: Speech-to-Text provider
- `tts_provider`: Text-to-Speech provider
- `prompt`: Optional custom prompt
- `tools`: Optional list of tool names
- `knowledge_base_id`: Optional knowledge base ID
- `**kwargs`: Additional provider-specific settings

##### `create_workflow`

```python
def create_workflow(
    self,
    name: str,
    description: Optional[str] = None,
    **kwargs
) -> WorkflowAgent
```

Creates a new workflow.

- `name`: Name of the workflow
- `description`: Optional description
- `**kwargs`: Additional workflow settings

##### `deploy_agent`

```python
async def deploy_agent(
    self,
    agent: VoiceAgent
) -> Dict[str, Any]
```

Deploys a voice agent.

- `agent`: The agent to deploy
- Returns a dictionary with deployment details

##### `deploy_workflow`

```python
async def deploy_workflow(
    self,
    workflow: WorkflowAgent
) -> Dict[str, Any]
```

Deploys a workflow.

- `workflow`: The workflow to deploy
- Returns a dictionary with deployment details

##### `list_agents`

```python
async def list_agents(
    self,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]
```

Lists all agents.

- `page`: Page number for pagination
- `page_size`: Number of items per page
- Returns a dictionary with agent list and pagination info

##### `get_agent`

```python
async def get_agent(
    self,
    agent_id: str
) -> Dict[str, Any]
```

Gets a specific agent by ID.

- `agent_id`: ID of the agent to retrieve
- Returns a dictionary with agent details

##### `delete_agent`

```python
async def delete_agent(
    self,
    agent_id: str
) -> Dict[str, Any]
```

Deletes an agent.

- `agent_id`: ID of the agent to delete
- Returns a dictionary with operation result

##### `create_knowledge_base`

```python
async def create_knowledge_base(
    self,
    name: str,
    vector_store: str = "supabase",
    embedding_model: str = "text-embedding-ada-002",
    **kwargs
) -> Dict[str, Any]
```

Creates a new knowledge base.

- `name`: Name of the knowledge base
- `vector_store`: Vector store provider
- `embedding_model`: Embedding model name
- `**kwargs`: Additional knowledge base settings
- Returns a dictionary with knowledge base details

##### `upload_document`

```python
async def upload_document(
    self,
    knowledge_base_id: str,
    file_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

Uploads a document to a knowledge base.

- `knowledge_base_id`: ID of the target knowledge base
- `file_path`: Path to the document file
- `metadata`: Optional document metadata
- Returns a dictionary with upload details

##### `get_license_info`

```python
async def get_license_info(self) -> Dict[str, Any]
```

Gets information about the current license.

- Returns a dictionary with license details

##### `configure_database`

```python
def configure_database(
    self,
    config: Dict[str, Any]
) -> None
```

Configures the database connection.

- `config`: Database configuration dictionary

##### `configure_livekit`

```python
def configure_livekit(
    self,
    api_key: str,
    api_secret: str,
    url: str
) -> None
```

Configures the LiveKit integration.

- `api_key`: LiveKit API key
- `api_secret`: LiveKit API secret
- `url`: LiveKit server URL

##### `configure_sip_provider`

```python
def configure_sip_provider(
    self,
    provider: str,
    **credentials
) -> Dict[str, Any]
```

Configures a SIP provider.

- `provider`: Provider name (e.g., "twilio")
- `**credentials`: Provider-specific credentials
- Returns a dictionary with the provider configuration

##### `map_phone_number`

```python
async def map_phone_number(
    self,
    phone_number: str,
    agent_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    trunk_id: str = None
) -> Dict[str, Any]
```

Maps a phone number to an agent or workflow.

- `phone_number`: The phone number to map
- `agent_id`: Optional agent ID (mutually exclusive with workflow_id)
- `workflow_id`: Optional workflow ID (mutually exclusive with agent_id)
- `trunk_id`: SIP trunk ID
- Returns a dictionary with the mapping details

### VoiceAgent

Represents a voice agent with LLM, STT, and TTS capabilities.

```python
from knova_ai import VoiceAgent
```

#### Methods

##### `__init__`

```python
def __init__(
    self,
    client: KnovaAI,
    config: Dict[str, Any]
) -> None
```

Creates a new voice agent instance.

- `client`: KnovaAI client instance
- `config`: Agent configuration dictionary

##### `create_livekit_agent`

```python
async def create_livekit_agent(
    self,
    room_name: Optional[str] = None
) -> Any
```

Creates a LiveKit agent for this voice agent.

- `room_name`: Optional LiveKit room name
- Returns a LiveKit agent object

##### `to_dict`

```python
def to_dict(self) -> Dict[str, Any]
```

Converts the agent to a dictionary representation.

- Returns a dictionary with the agent configuration

##### `map_to_phone_number`

```python
async def map_to_phone_number(
    self,
    phone_number: str,
    trunk_id: str
) -> Dict[str, Any]
```

Maps this agent to a phone number.

- `phone_number`: The phone number to map
- `trunk_id`: SIP trunk ID
- Returns a dictionary with the mapping details

##### `update_config`

```python
async def update_config(
    self,
    **kwargs
) -> None
```

Updates the agent configuration.

- `**kwargs`: Configuration fields to update

### WorkflowAgent

Represents a workflow with multiple agents and logic nodes.

```python
from knova_ai import WorkflowAgent
```

#### Methods

##### `__init__`

```python
def __init__(
    self,
    client: KnovaAI,
    name: str,
    description: Optional[str] = None,
    **kwargs
) -> None
```

Creates a new workflow agent instance.

- `client`: KnovaAI client instance
- `name`: Workflow name
- `description`: Optional workflow description
- `**kwargs`: Additional workflow settings

##### `add_node`

```python
def add_node(
    self,
    type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]
```

Adds a node to the workflow.

- `type`: Node type (e.g., "agent", "condition")
- `data`: Node data
- Returns the created node dictionary

##### `add_edge`

```python
def add_edge(
    self,
    source: str,
    target: str,
    condition: Optional[str] = None
) -> Dict[str, Any]
```

Adds an edge between nodes.

- `source`: Source node ID
- `target`: Target node ID
- `condition`: Optional edge condition
- Returns the created edge dictionary

##### `validate`

```python
def validate(self) -> bool
```

Validates the workflow structure.

- Returns True if the workflow is valid, False otherwise

##### `to_dict`

```python
def to_dict(self) -> Dict[str, Any]
```

Converts the workflow to a dictionary representation.

- Returns a dictionary with the workflow configuration

##### `to_deployment_config`

```python
def to_deployment_config(self) -> Dict[str, Any]
```

Converts the workflow to a deployment configuration.

- Returns a dictionary with the deployment configuration

##### `to_react_flow_format`

```python
def to_react_flow_format(self) -> Dict[str, Any]
```

Converts the workflow to React Flow format for visualization.

- Returns a dictionary in React Flow format

## Provider Classes

### LLMProvider

Base class for LLM providers.

```python
from knova_ai.providers import LLMProvider

class CustomLLMProvider(LLMProvider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def generate_response(self, prompt, **kwargs):
        # Implementation for custom provider
        pass
```

### STTProvider

Base class for Speech-to-Text providers.

```python
from knova_ai.providers import STTProvider

class CustomSTTProvider(STTProvider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def transcribe(self, audio_data, **kwargs):
        # Implementation for custom provider
        pass
```

### TTSProvider

Base class for Text-to-Speech providers.

```python
from knova_ai.providers import TTSProvider

class CustomTTSProvider(TTSProvider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def synthesize(self, text, **kwargs):
        # Implementation for custom provider
        pass
```

## Database Classes

### DatabaseConnector

Base class for database connectors.

```python
from knova_ai.db import DatabaseConnector

class CustomDatabaseConnector(DatabaseConnector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def connect(self):
        # Implementation for connection
        pass
    
    async def disconnect(self):
        # Implementation for disconnection
        pass
    
    async def execute(self, query, params=None):
        # Implementation for query execution
        pass
```

### Entity Classes

Base classes for database entities.

```python
from knova_ai.db.entities import BaseEntity

class CustomEntity(BaseEntity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @classmethod
    def from_dict(cls, data):
        # Implementation for conversion from dict
        pass
    
    def to_dict(self):
        # Implementation for conversion to dict
        pass
```

## Tool Classes

### BaseTool

Base class for agent tools.

```python
from knova_ai.tools import BaseTool

class CustomTool(BaseTool):
    def __init__(self, **kwargs):
        super().__init__(name="custom_tool", **kwargs)
    
    async def execute(self, params):
        # Implementation for tool execution
        pass
    
    def get_schema(self):
        # Return JSON schema for the tool
        return {
            "name": self.name,
            "description": "A custom tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        }
```

## License Classes

### LicenseValidator

Class for license validation.

```python
from knova_ai.license import LicenseValidator

validator = LicenseValidator(license_key="your-license-key")
is_valid = await validator.validate()
```

### License

Class representing a license.

```python
from knova_ai.license import License

license = License(
    key="your-license-key",
    tier="free",
    expires_at="2025-12-31T23:59:59Z",
    features=["voice_agents", "workflows"]
)

license_dict = license.to_dict()
```

## Telemetry Classes

### TelemetryManager

Class for managing telemetry collection and reporting.

```python
from knova_ai.telemetry import TelemetryManager

telemetry = TelemetryManager(
    enabled=True,
    webhook_url="https://your-webhook.com/events",
    metrics=["api_calls", "agent_runtime"]
)

await telemetry.track_event("agent_created", {"agent_id": "agent-uuid"})
```

## Exception Classes

### KnovaAIException

Base exception class for Knova AI.

```python
from knova_ai.exceptions import KnovaAIException

try:
    # Some operation
    pass
except KnovaAIException as e:
    print(f"Error: {e}")
```

### LicenseException

Exception for license-related errors.

```python
from knova_ai.exceptions import LicenseException

try:
    # License operation
    pass
except LicenseException as e:
    print(f"License error: {e}")
```

### APIException

Exception for API-related errors.

```python
from knova_ai.exceptions import APIException

try:
    # API operation
    pass
except APIException as e:
    print(f"API error: {e.status_code}: {e.message}")
```
