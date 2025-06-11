"""Voice agent handler"""

import logging
from typing import Dict, Any, Optional

from livekit import agents
from livekit.agents import JobContext, VoiceAssistant, ChatContext
from livekit.plugins import openai, deepgram, elevenlabs, google, anthropic

logger = logging.getLogger(__name__)


class VoiceHandler:
    """Handles voice agent creation and configuration"""
    
    def __init__(self, ctx: JobContext, config: Dict[str, Any]):
        self.ctx = ctx
        self.config = config
        
    async def create_assistant(self) -> VoiceAssistant:
        """Create and configure voice assistant"""
        # Get provider configurations
        llm_config = self.config.get("llm", {})
        stt_config = self.config.get("stt", {})
        tts_config = self.config.get("tts", {})
        
        # Create LLM
        llm = self._create_llm(llm_config)
        
        # Create STT
        stt = self._create_stt(stt_config)
        
        # Create TTS
        tts = self._create_tts(tts_config)
        
        # Create chat context with system prompt
        chat_ctx = ChatContext()
        system_prompt = self.config.get("prompt", "You are a helpful AI assistant.")
        chat_ctx.append(text=system_prompt, role="system")
        
        # Create assistant
        assistant = VoiceAssistant(
            llm=llm,
            stt=stt,
            tts=tts,
            chat_ctx=chat_ctx,
            allow_interruptions=True,
            interrupt_min_words=3,
        )
        
        # Add function calling if configured
        if "tools" in self.config:
            await self._configure_tools(assistant)
            
        return assistant
        
    def _create_llm(self, config: Dict[str, Any]):
        """Create LLM based on provider"""
        provider = config.get("provider", "openai")
        model = config.get("model", "gpt-4")
        settings = config.get("settings", {})
        
        if provider == "openai":
            return openai.LLM(model=model, **settings)
        elif provider == "google":
            return google.LLM(model=model, **settings)
        elif provider == "anthropic":
            return anthropic.LLM(model=model, **settings)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
            
    def _create_stt(self, config: Dict[str, Any]):
        """Create STT based on provider"""
        provider = config.get("provider", "deepgram")
        settings = config.get("settings", {})
        
        if provider == "deepgram":
            return deepgram.STT(**settings)
        elif provider == "openai":
            return openai.STT(**settings)
        elif provider == "google":
            return google.STT(**settings)
        else:
            raise ValueError(f"Unknown STT provider: {provider}")
            
    def _create_tts(self, config: Dict[str, Any]):
        """Create TTS based on provider"""
        provider = config.get("provider", "elevenlabs")
        settings = config.get("settings", {})
        
        if provider == "elevenlabs":
            return elevenlabs.TTS(**settings)
        elif provider == "openai":
            return openai.TTS(**settings)
        elif provider == "google":
            return google.TTS(**settings)
        else:
            raise ValueError(f"Unknown TTS provider: {provider}")
            
    async def _configure_tools(self, assistant: VoiceAssistant):
        """Configure function calling tools"""
        # TODO: Implement Composio integration
        pass