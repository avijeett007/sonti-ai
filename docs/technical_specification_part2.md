# Knova AI: Technical Specification (Part 2)

## 3. Agent Runtime

### 3.1 Agent Container Architecture

#### 3.1.1 Technology Stack
- **Language**: Python 3.10+
- **Framework**: LiveKit Agents Framework
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Messaging**: Redis Pub/Sub

#### 3.1.2 Agent Container Components
- **Worker Process**: Manages agent lifecycle and LiveKit connection
- **Speech Pipeline**: Handles audio processing and transcription
- **LLM Integration**: Manages communication with language models
- **TTS Engine**: Converts text responses to speech
- **Function Execution Engine**: Executes tools and functions
- **Knowledge Base Connector**: Retrieves information from vector databases

#### 3.1.3 Agent Configuration
Based on LiveKit Agents framework, each agent will be configured with:

```python
class KnovaAgent(Agent):
    def __init__(self, config: AgentConfig) -> None:
        super().__init__(
            instructions=config.system_prompt,
            chat_ctx=config.initial_context
        )
        self.config = config
        self.knowledge_base = self._init_knowledge_base(config.knowledge_base_id)
        self._register_tools()

    def _register_tools(self):
        # Register dynamic tools based on configuration
        for tool_config in self.config.tools:
            self._register_tool(tool_config)

    @function_tool()
    async def search_knowledge_base(
        self,
        context: RunContext,
        query: str,
    ) -> dict[str, Any]:
        """Search the knowledge base for relevant information.
        
        Args:
            query: The search query to find information in the knowledge base.
        """
        results = await self.knowledge_base.search(query)
        return {"results": results}

    # Additional function tools will be registered dynamically
```

### 3.2 Agent Dispatch System

#### 3.2.1 Dispatch Mechanism
Knova AI will use LiveKit's explicit agent dispatch mechanism to ensure the correct agent is assigned to each room:

```python
async def entrypoint(ctx: agents.JobContext):
    # Extract agent_id from metadata
    metadata = json.loads(ctx.job.metadata)
    agent_id = metadata.get("agent_id")
    
    if not agent_id:
        logger.error("No agent_id provided in metadata")
        return
    
    # Load agent configuration from database
    agent_config = await load_agent_config(agent_id)
    
    # Initialize appropriate providers based on configuration
    stt_provider = initialize_stt_provider(agent_config.stt_config)
    llm_provider = initialize_llm_provider(agent_config.llm_config)
    tts_provider = initialize_tts_provider(agent_config.tts_config)
    
    # Create agent session
    session = AgentSession(
        stt=stt_provider,
        llm=llm_provider,
        tts=tts_provider,
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    
    # Start agent session
    await session.start(
        room=ctx.room,
        agent=KnovaAgent(agent_config),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await ctx.connect()
    
    # Initial greeting
    await session.generate_reply(
        instructions=agent_config.greeting_instructions
    )
```

#### 3.2.2 Worker Deployment
- Each worker will be deployed as a Kubernetes pod
- Horizontal Pod Autoscaler will manage scaling based on demand
- Workers will register with LiveKit server for job assignment

### 3.3 Multi-Agent Collaboration

#### 3.3.1 Agent Handoff Mechanism
Knova AI will support agent handoff for complex workflows:

```python
@function_tool()
async def handoff_to_specialist(
    self,
    context: RunContext,
    specialist_type: str,
    handoff_context: dict,
) -> dict[str, Any]:
    """Hand off the conversation to a specialist agent.
    
    Args:
        specialist_type: The type of specialist agent to hand off to.
        handoff_context: Context information to pass to the specialist.
    """
    # Get the appropriate specialist agent ID
    specialist_id = await get_specialist_id(specialist_type)
    
    # Create handoff metadata
    handoff_metadata = {
        "previous_agent_id": self.config.agent_id,
        "handoff_context": handoff_context,
        "conversation_history": context.chat_history,
    }
    
    # Trigger agent handoff
    await trigger_agent_handoff(context.room_name, specialist_id, handoff_metadata)
    
    return {"status": "handoff_initiated", "specialist_id": specialist_id}
```
