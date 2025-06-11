# Knova AI: Agent Wrapper Design

## Overview

The Knova AI Agent Wrapper is a Python package that simplifies the creation and management of voice AI agents while providing telemetry, license validation, and a consistent interface for the open source community. This document outlines the design and implementation of this wrapper.

## Design Goals

1. **Simplicity**: Make it easy for developers to create and deploy voice AI agents
2. **License Management**: Implement a license key system for tracking and telemetry
3. **Extensibility**: Support various LLM, STT, and TTS providers
4. **Consistency**: Provide a unified interface for agent creation and management
5. **Telemetry**: Collect anonymous usage data for platform improvement

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Knova AI Agent Wrapper                  │
├─────────────────┬──────────────────────┬───────────────────┤
│  Configuration  │   Agent Management   │    Telemetry      │
│    Management   │                      │                   │
├─────────────────┼──────────────────────┼───────────────────┤
│   License       │   Provider           │    Webhook        │
│   Validation    │   Integration        │    Support        │
├─────────────────┴──────────────────────┴───────────────────┤
│                    LiveKit Integration                     │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Configuration Management

Handles loading, validating, and persisting agent configurations from local storage or database.

```python
class ConfigManager:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser("~/.knova")
        os.makedirs(self.storage_path, exist_ok=True)
        self.db_path = os.path.join(self.storage_path, "knova.db")
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for configuration storage."""
        # Create tables for agents, workflows, providers, etc.
        
    def load_agent_config(self, agent_id: str) -> dict:
        """Load agent configuration from database."""
        
    def save_agent_config(self, agent_config: dict) -> str:
        """Save agent configuration to database and return agent_id."""
        
    def list_agents(self) -> list[dict]:
        """List all available agents."""
```

#### 2. License Validation

Validates license keys and enforces usage restrictions.

```python
class LicenseManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
    async def validate_license(self, license_key: str) -> bool:
        """Validate license key against Knova AI license server."""
        # Make API call to license server
        # Store validation result locally
        
    async def check_license_status(self) -> dict:
        """Check current license status."""
        
    def is_license_valid(self) -> bool:
        """Check if current license is valid."""
```

#### 3. Agent Management

Provides a simplified interface for creating and managing agents.

```python
class KnovaAgent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        knowledge_base_id: str = None,
        stt_provider: str = "openai",
        llm_provider: str = "openai",
        tts_provider: str = "openai",
        stt_config: dict = None,
        llm_config: dict = None,
        tts_config: dict = None,
        tools: list = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.knowledge_base_id = knowledge_base_id
        self.stt_provider = stt_provider
        self.llm_provider = llm_provider
        self.tts_provider = tts_provider
        self.stt_config = stt_config or {}
        self.llm_config = llm_config or {}
        self.tts_config = tts_config or {}
        self.tools = tools or []
        
    def add_tool(self, tool: dict):
        """Add a tool to the agent."""
        self.tools.append(tool)
        
    def add_knowledge_base(self, knowledge_base_id: str):
        """Set the knowledge base for the agent."""
        self.knowledge_base_id = knowledge_base_id
        
    def to_dict(self) -> dict:
        """Convert agent configuration to dictionary."""
        
    @classmethod
    def from_dict(cls, config: dict) -> "KnovaAgent":
        """Create agent from configuration dictionary."""
```

#### 4. Provider Integration

Manages integration with various LLM, STT, and TTS providers.

```python
class ProviderManager:
    def __init__(self):
        self.providers = {
            "stt": {
                "openai": OpenAISTTProvider,
                "deepgram": DeepgramSTTProvider,
                "google": GoogleSTTProvider,
                "azure": AzureSTTProvider,
                # Add more providers
            },
            "llm": {
                "openai": OpenAILLMProvider,
                "anthropic": AnthropicLLMProvider,
                "google": GoogleLLMProvider,
                "azure": AzureLLMProvider,
                # Add more providers
            },
            "tts": {
                "openai": OpenAITTSProvider,
                "elevenlabs": ElevenLabsTTSProvider,
                "google": GoogleTTSProvider,
                "azure": AzureTTSProvider,
                # Add more providers
            }
        }
    
    def get_stt_provider(self, provider_name: str, config: dict):
        """Get STT provider instance."""
        provider_class = self.providers["stt"].get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown STT provider: {provider_name}")
        return provider_class(**config)
    
    def get_llm_provider(self, provider_name: str, config: dict):
        """Get LLM provider instance."""
        provider_class = self.providers["llm"].get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown LLM provider: {provider_name}")
        return provider_class(**config)
    
    def get_tts_provider(self, provider_name: str, config: dict):
        """Get TTS provider instance."""
        provider_class = self.providers["tts"].get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown TTS provider: {provider_name}")
        return provider_class(**config)
```

#### 5. Telemetry

Collects anonymous usage data for platform improvement.

```python
class TelemetryManager:
    def __init__(self, config_manager: ConfigManager, license_manager: LicenseManager):
        self.config_manager = config_manager
        self.license_manager = license_manager
        self.telemetry_enabled = True
        
    async def send_telemetry(self, event_type: str, data: dict):
        """Send telemetry data to Knova AI telemetry server."""
        if not self.telemetry_enabled or not self.license_manager.is_license_valid():
            return
            
        # Add license key and anonymize data
        data = self._anonymize_data(data)
        data["license_key"] = self.license_manager.get_license_key()
        
        # Send telemetry data
        try:
            # Make API call to telemetry server
            pass
        except Exception:
            # Silently fail if telemetry fails
            pass
    
    def _anonymize_data(self, data: dict) -> dict:
        """Anonymize sensitive data."""
        # Remove API keys, PII, etc.
        return data
    
    def disable_telemetry(self):
        """Disable telemetry collection."""
        self.telemetry_enabled = False
    
    def enable_telemetry(self):
        """Enable telemetry collection."""
        self.telemetry_enabled = True
```

#### 6. Webhook Support

Manages webhook registration and event handling.

```python
class WebhookManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
    def register_webhook(self, agent_id: str, event_type: str, url: str, headers: dict = None):
        """Register a webhook for an agent."""
        
    def unregister_webhook(self, agent_id: str, event_type: str, url: str):
        """Unregister a webhook for an agent."""
        
    def list_webhooks(self, agent_id: str) -> list[dict]:
        """List all webhooks for an agent."""
        
    async def trigger_webhook(self, agent_id: str, event_type: str, data: dict):
        """Trigger a webhook for an agent."""
        webhooks = self._get_webhooks(agent_id, event_type)
        for webhook in webhooks:
            try:
                # Make HTTP request to webhook URL
                pass
            except Exception:
                # Log error and continue
                pass
```

#### 7. LiveKit Integration

Manages integration with LiveKit for agent dispatch and communication.

```python
class LiveKitManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
    async def create_agent_dispatch(self, agent_id: str, room_name: str, metadata: dict = None):
        """Create agent dispatch request."""
        # Convert metadata to JSON string
        metadata_str = json.dumps(metadata or {})
        
        # Get LiveKit API client
        lkapi = api.LiveKitAPI()
        
        # Create dispatch request
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_id,
                room=room_name,
                metadata=metadata_str
            )
        )
        
        return dispatch
    
    async def list_dispatches(self, room_name: str) -> list:
        """List all dispatches for a room."""
        lkapi = api.LiveKitAPI()
        dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
        return dispatches
    
    async def create_room(self, room_name: str, metadata: dict = None) -> dict:
        """Create a LiveKit room."""
        # Convert metadata to JSON string
        metadata_str = json.dumps(metadata or {})
        
        # Get LiveKit API client
        lkapi = api.LiveKitAPI()
        
        # Create room
        room = await lkapi.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=metadata_str
            )
        )
        
        return room
```

## Main Wrapper Class

The main wrapper class that ties everything together:

```python
class KnovaAI:
    def __init__(self, license_key: str = None, storage_path: str = None):
        self.config_manager = ConfigManager(storage_path)
        self.license_manager = LicenseManager(self.config_manager)
        self.provider_manager = ProviderManager()
        self.telemetry_manager = TelemetryManager(self.config_manager, self.license_manager)
        self.webhook_manager = WebhookManager(self.config_manager)
        self.livekit_manager = LiveKitManager(self.config_manager)
        
        if license_key:
            self.set_license_key(license_key)
    
    async def set_license_key(self, license_key: str) -> bool:
        """Set and validate license key."""
        is_valid = await self.license_manager.validate_license(license_key)
        if is_valid:
            await self.telemetry_manager.send_telemetry("license_activated", {})
        return is_valid
    
    def create_agent(self, agent_config: dict) -> str:
        """Create a new agent from configuration."""
        # Validate license
        if not self.license_manager.is_license_valid():
            raise ValueError("Invalid license key")
        
        # Save agent configuration
        agent_id = self.config_manager.save_agent_config(agent_config)
        
        # Send telemetry
        self.telemetry_manager.send_telemetry("agent_created", {
            "agent_id": agent_id,
            "stt_provider": agent_config.get("stt_provider"),
            "llm_provider": agent_config.get("llm_provider"),
            "tts_provider": agent_config.get("tts_provider"),
        })
        
        return agent_id
    
    async def deploy_agent(self, agent_id: str, room_name: str = None) -> dict:
        """Deploy an agent to a LiveKit room."""
        # Validate license
        if not self.license_manager.is_license_valid():
            raise ValueError("Invalid license key")
        
        # Load agent configuration
        agent_config = self.config_manager.load_agent_config(agent_id)
        
        # Generate room name if not provided
        if not room_name:
            room_name = f"knova-{agent_id}-{uuid.uuid4()}"
        
        # Create room
        room = await self.livekit_manager.create_room(room_name, {
            "agent_id": agent_id
        })
        
        # Create agent dispatch
        dispatch = await self.livekit_manager.create_agent_dispatch(agent_id, room_name, {
            "agent_id": agent_id,
            "agent_config": agent_config
        })
        
        # Send telemetry
        await self.telemetry_manager.send_telemetry("agent_deployed", {
            "agent_id": agent_id,
            "room_name": room_name
        })
        
        return {
            "agent_id": agent_id,
            "room_name": room_name,
            "dispatch_id": dispatch.id
        }
```

## Usage Examples

### Basic Agent Creation and Deployment

```python
from knova_ai import KnovaAI

# Initialize KnovaAI with license key
knova = KnovaAI(license_key="your-license-key")

# Create an agent
agent_id = knova.create_agent({
    "name": "Customer Support Agent",
    "system_prompt": "You are a helpful customer support agent.",
    "stt_provider": "deepgram",
    "llm_provider": "openai",
    "tts_provider": "elevenlabs",
    "stt_config": {
        "model": "nova-2",
        "language": "en"
    },
    "llm_config": {
        "model": "gpt-4o"
    },
    "tts_config": {
        "voice_id": "Rachel"
    }
})

# Deploy the agent
deployment = await knova.deploy_agent(agent_id)
print(f"Agent deployed to room: {deployment['room_name']}")
```

### Creating a Workflow with Multiple Agents

```python
# Create consent collection agent
consent_agent_id = knova.create_agent({
    "name": "Consent Collector",
    "system_prompt": "Your task is to collect recording consent from the user.",
    "llm_provider": "openai",
    "llm_config": {
        "model": "gpt-4o"
    }
})

# Create main support agent
support_agent_id = knova.create_agent({
    "name": "Support Agent",
    "system_prompt": "You are a helpful customer support agent.",
    "llm_provider": "openai",
    "llm_config": {
        "model": "gpt-4o"
    }
})

# Create workflow
workflow_id = knova.create_workflow({
    "name": "Support Workflow",
    "agents": [consent_agent_id, support_agent_id],
    "transitions": [
        {
            "from_agent": consent_agent_id,
            "to_agent": support_agent_id,
            "condition": "consent_given"
        }
    ]
})

# Deploy workflow
deployment = await knova.deploy_workflow(workflow_id)
```

## PyPI Package Structure

```
knova-ai/
├── knova_ai/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── license.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── stt.py
│   │   ├── llm.py
│   │   └── tts.py
│   ├── telemetry.py
│   ├── webhook.py
│   └── livekit_integration.py
├── setup.py
├── README.md
└── LICENSE
```

## License Key Activation Flow

1. User installs the package: `pip install knova-ai`
2. User signs up on Knova AI website and obtains a license key
3. User initializes KnovaAI with the license key
4. License key is validated against the Knova AI license server
5. If valid, the license key is stored locally for future use
6. Anonymous telemetry data is collected during usage (can be disabled)

## Telemetry Data Collection

The following telemetry data is collected:

1. **License Activation**: When a license key is activated
2. **Agent Creation**: When a new agent is created
3. **Agent Deployment**: When an agent is deployed
4. **Agent Usage**: Basic usage statistics (call duration, success/failure)
5. **Provider Usage**: Which providers are being used (not API keys)

All telemetry data is anonymized and does not contain sensitive information such as API keys, conversation content, or personally identifiable information.

## Conclusion

The Knova AI Agent Wrapper provides a simple, consistent interface for creating and managing voice AI agents while enforcing license validation and collecting anonymous telemetry data. This design allows for easy extension with new providers and features while maintaining backward compatibility.
