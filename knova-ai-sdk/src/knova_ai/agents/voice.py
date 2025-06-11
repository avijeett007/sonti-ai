"""Voice agent implementation for Knova AI"""

from typing import Dict, Any, Optional, List

from livekit import agents
from livekit.agents import JobContext, WorkerOptions

from .base import Agent
from ..providers.llm import LLMProvider
from ..providers.stt import STTProvider
from ..providers.tts import TTSProvider


class VoiceAgent(Agent):
    """Voice agent with STT/TTS capabilities"""
    
    def __init__(self, client, config: Dict[str, Any]):
        config["type"] = "voice"
        super().__init__(client, config)
        
        # Extract voice-specific configuration
        self.llm_provider = config.get("llm_provider", "openai")
        self.llm_model = config.get("llm_model", "gpt-4")
        self.stt_provider = config.get("stt_provider", "deepgram")
        self.tts_provider = config.get("tts_provider", "elevenlabs")
        self.prompt = config.get("prompt", self._default_prompt())
        self.tools = config.get("tools", [])
        self.knowledge_base_id = config.get("knowledge_base_id")
        
        # Provider-specific settings
        self.llm_settings = config.get("llm_settings", {})
        self.stt_settings = config.get("stt_settings", {})
        self.tts_settings = config.get("tts_settings", {})
        
        # Initialize providers
        self._llm = None
        self._stt = None
        self._tts = None
        
    def _default_prompt(self) -> str:
        """Default prompt template"""
        return """You are a helpful AI assistant. 
        Respond naturally and conversationally to the user's questions.
        Keep your responses concise and relevant."""
        
    def to_deployment_config(self) -> Dict[str, Any]:
        """Convert to deployment configuration"""
        return {
            "id": self.id,
            "name": self.name,
            "type": "voice",
            "llm": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "settings": self.llm_settings
            },
            "stt": {
                "provider": self.stt_provider,
                "settings": self.stt_settings
            },
            "tts": {
                "provider": self.tts_provider,
                "settings": self.tts_settings
            },
            "prompt": self.prompt,
            "tools": self.tools,
            "knowledge_base_id": self.knowledge_base_id
        }
        
    async def test(self, input_text: str) -> str:
        """Test the agent with sample input"""
        # Initialize providers if not already done
        if not self._llm:
            self._llm = LLMProvider.create(
                self.llm_provider,
                self.llm_model,
                **self.llm_settings
            )
            
        # Simple test - just get LLM response
        response = await self._llm.generate(
            prompt=self.prompt,
            user_input=input_text
        )
        
        return response
        
    def create_livekit_agent(self) -> agents.JobContext:
        """Create LiveKit agent handler"""
        async def entrypoint(ctx: JobContext):
            # Initialize providers
            llm = LLMProvider.create_livekit_llm(
                self.llm_provider,
                self.llm_model,
                **self.llm_settings
            )
            
            stt = STTProvider.create_livekit_stt(
                self.stt_provider,
                **self.stt_settings
            )
            
            tts = TTSProvider.create_livekit_tts(
                self.tts_provider,
                **self.tts_settings
            )
            
            # Create assistant
            assistant = agents.VoiceAssistant(
                llm=llm,
                stt=stt,
                tts=tts,
                chat_ctx=agents.ChatContext().append(
                    text=self.prompt,
                    role="system"
                )
            )
            
            # Connect to room
            await ctx.connect()
            
            # Start assistant
            assistant.start(ctx.room)
            
            # Handle participant events
            @ctx.room.on("participant_connected")
            def on_participant_connected(participant):
                assistant.start_session(participant)
                
        return entrypoint
        
    def with_knowledge_base(self, knowledge_base_id: str) -> "VoiceAgent":
        """Attach a knowledge base to the agent"""
        self.knowledge_base_id = knowledge_base_id
        return self
        
    def with_tools(self, tools: List[str]) -> "VoiceAgent":
        """Add tools/functions to the agent"""
        self.tools.extend(tools)
        return self
        
    def with_prompt(self, prompt: str) -> "VoiceAgent":
        """Set custom prompt"""
        self.prompt = prompt
        return self
        
    def with_llm_settings(self, **settings) -> "VoiceAgent":
        """Configure LLM settings"""
        self.llm_settings.update(settings)
        return self
        
    def with_stt_settings(self, **settings) -> "VoiceAgent":
        """Configure STT settings"""
        self.stt_settings.update(settings)
        return self
        
    def with_tts_settings(self, **settings) -> "VoiceAgent":
        """Configure TTS settings"""
        self.tts_settings.update(settings)
        return self