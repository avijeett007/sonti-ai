"""LiveKit adapter for integrating Knova AI providers with LiveKit agents"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, AsyncIterator, Callable
from dataclasses import dataclass
import json

from livekit import agents
from livekit.agents import llm as livekit_llm
from livekit.agents import stt as livekit_stt
from livekit.agents import tts as livekit_tts
from livekit.agents import JobContext, WorkerOptions

from ..base import BaseLLMProvider, BaseSTTProvider, BaseTTSProvider, ProviderType
from ..registry import ProviderRegistry


logger = logging.getLogger("knova.providers.adapters.livekit")


@dataclass
class LiveKitAgentConfig:
    """Configuration for LiveKit agent with Knova AI providers"""
    llm_provider: str
    llm_config: Dict[str, Any]
    stt_provider: str
    stt_config: Dict[str, Any]
    tts_provider: str
    tts_config: Dict[str, Any]
    agent_name: str = "Knova AI Agent"
    initial_prompt: str = "You are a helpful assistant."
    functions: Optional[List[Dict[str, Any]]] = None
    temperature: float = 0.7
    enable_interruptions: bool = True


class LiveKitLLMAdapter(livekit_llm.LLM):
    """Adapter to make Knova AI LLM providers work with LiveKit"""
    
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self._temperature = provider.temperature
        
    async def chat(
        self,
        messages: List[livekit_llm.ChatMessage],
        **kwargs
    ) -> livekit_llm.ChatResponse:
        """Adapt LiveKit chat interface to Knova AI provider"""
        # Convert LiveKit messages to provider format
        provider_messages = []
        for msg in messages:
            provider_msg = {"role": msg.role, "content": msg.content}
            if hasattr(msg, "function_call") and msg.function_call:
                provider_msg["function_call"] = msg.function_call
            provider_messages.append(provider_msg)
        
        # Call provider
        if kwargs.get("functions") and self.provider.has_capability("function_calling"):
            result = await self.provider.generate_with_functions(
                provider_messages,
                kwargs["functions"],
                **kwargs
            )
            
            # Convert to LiveKit response
            return livekit_llm.ChatResponse(
                content=result.get("content", ""),
                function_call=result.get("function_call"),
                usage=livekit_llm.Usage(
                    prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
                    completion_tokens=result.get("usage", {}).get("completion_tokens", 0),
                    total_tokens=result.get("usage", {}).get("total_tokens", 0)
                ) if result.get("usage") else None
            )
        else:
            # Regular generation
            content = await self.provider.generate(provider_messages, **kwargs)
            
            # Handle streaming
            if isinstance(content, AsyncIterator):
                # Collect stream for LiveKit
                full_content = ""
                async for chunk in content:
                    full_content += chunk
                content = full_content
            
            return livekit_llm.ChatResponse(content=content)
    
    async def stream(
        self,
        messages: List[livekit_llm.ChatMessage],
        **kwargs
    ) -> AsyncIterator[livekit_llm.ChatChunk]:
        """Stream responses from provider"""
        # Convert messages
        provider_messages = []
        for msg in messages:
            provider_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Get streaming response
        stream = await self.provider.generate(
            provider_messages,
            stream=True,
            **kwargs
        )
        
        # Adapt stream to LiveKit format
        if isinstance(stream, AsyncIterator):
            async for chunk in stream:
                yield livekit_llm.ChatChunk(
                    content=chunk,
                    usage=None  # Usage typically comes at the end
                )
        else:
            # Provider doesn't support streaming, yield as single chunk
            yield livekit_llm.ChatChunk(content=str(stream))


class LiveKitSTTAdapter(livekit_stt.STT):
    """Adapter to make Knova AI STT providers work with LiveKit"""
    
    def __init__(self, provider: BaseSTTProvider):
        self.provider = provider
        self._sample_rate = provider.sample_rate
        
    async def recognize(
        self,
        audio: Union[bytes, AsyncIterator[bytes]],
        **kwargs
    ) -> livekit_stt.RecognitionResult:
        """Adapt LiveKit STT interface to Knova AI provider"""
        if isinstance(audio, bytes):
            # Single audio buffer
            result = await self.provider.transcribe(audio, **kwargs)
            
            return livekit_stt.RecognitionResult(
                text=result.get("text", ""),
                language=result.get("language"),
                confidence=result.get("confidence", 1.0)
            )
        else:
            # Streaming audio
            # Collect final result from stream
            final_text = ""
            final_language = None
            
            async for result in self.provider.transcribe_stream(audio, **kwargs):
                if result.get("is_final"):
                    final_text = result.get("text", "")
                    final_language = result.get("language")
            
            return livekit_stt.RecognitionResult(
                text=final_text,
                language=final_language,
                confidence=1.0
            )
    
    async def stream(
        self,
        audio_stream: AsyncIterator[bytes],
        **kwargs
    ) -> AsyncIterator[livekit_stt.RecognitionEvent]:
        """Stream recognition results"""
        async for result in self.provider.transcribe_stream(audio_stream, **kwargs):
            yield livekit_stt.RecognitionEvent(
                text=result.get("text", ""),
                is_final=result.get("is_final", False),
                language=result.get("language"),
                confidence=result.get("confidence", 1.0)
            )


class LiveKitTTSAdapter(livekit_tts.TTS):
    """Adapter to make Knova AI TTS providers work with LiveKit"""
    
    def __init__(self, provider: BaseTTSProvider):
        self.provider = provider
        self._sample_rate = provider.sample_rate
        
    async def synthesize(
        self,
        text: str,
        **kwargs
    ) -> livekit_tts.SynthesisResult:
        """Adapt LiveKit TTS interface to Knova AI provider"""
        audio_data = await self.provider.synthesize(text, **kwargs)
        
        return livekit_tts.SynthesisResult(
            audio=audio_data,
            sample_rate=self._sample_rate,
            num_channels=1  # Mono by default
        )
    
    async def stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncIterator[livekit_tts.SynthesisEvent]:
        """Stream synthesis results"""
        if self.provider.has_capability("streaming"):
            async for chunk in self.provider.synthesize_stream(text, **kwargs):
                yield livekit_tts.SynthesisEvent(
                    audio=chunk,
                    is_final=False
                )
            
            # Send final event
            yield livekit_tts.SynthesisEvent(
                audio=b"",
                is_final=True
            )
        else:
            # Provider doesn't support streaming, synthesize and yield as single event
            audio_data = await self.provider.synthesize(text, **kwargs)
            yield livekit_tts.SynthesisEvent(
                audio=audio_data,
                is_final=True
            )


class LiveKitProviderAdapter:
    """Main adapter class for integrating Knova AI providers with LiveKit"""
    
    def __init__(self, config: LiveKitAgentConfig):
        self.config = config
        self.registry = ProviderRegistry.get_instance()
        self._llm_provider: Optional[BaseLLMProvider] = None
        self._stt_provider: Optional[BaseSTTProvider] = None
        self._tts_provider: Optional[BaseTTSProvider] = None
        
    async def initialize(self):
        """Initialize all providers"""
        # Create LLM provider
        self._llm_provider = self.registry.create_provider(
            self.config.llm_provider,
            ProviderType.LLM,
            **self.config.llm_config
        )
        await self._llm_provider.initialize()
        
        # Create STT provider
        self._stt_provider = self.registry.create_provider(
            self.config.stt_provider,
            ProviderType.STT,
            **self.config.stt_config
        )
        await self._stt_provider.initialize()
        
        # Create TTS provider
        self._tts_provider = self.registry.create_provider(
            self.config.tts_provider,
            ProviderType.TTS,
            **self.config.tts_config
        )
        await self._tts_provider.initialize()
        
        logger.info(
            f"Initialized LiveKit adapter with providers: "
            f"LLM={self.config.llm_provider}, "
            f"STT={self.config.stt_provider}, "
            f"TTS={self.config.tts_provider}"
        )
    
    def get_llm(self) -> livekit_llm.LLM:
        """Get LiveKit-compatible LLM"""
        if not self._llm_provider:
            raise RuntimeError("Adapter not initialized")
        return LiveKitLLMAdapter(self._llm_provider)
    
    def get_stt(self) -> livekit_stt.STT:
        """Get LiveKit-compatible STT"""
        if not self._stt_provider:
            raise RuntimeError("Adapter not initialized")
        return LiveKitSTTAdapter(self._stt_provider)
    
    def get_tts(self) -> livekit_tts.TTS:
        """Get LiveKit-compatible TTS"""
        if not self._tts_provider:
            raise RuntimeError("Adapter not initialized")
        return LiveKitTTSAdapter(self._tts_provider)
    
    async def create_voice_assistant(self) -> agents.VoiceAssistant:
        """Create a LiveKit VoiceAssistant with Knova AI providers"""
        await self.initialize()
        
        # Create assistant with our providers
        assistant = agents.VoiceAssistant(
            llm=self.get_llm(),
            stt=self.get_stt(),
            tts=self.get_tts(),
            interrupt_min_words=3 if self.config.enable_interruptions else None
        )
        
        # Set initial prompt
        if self.config.initial_prompt:
            assistant.set_system_prompt(self.config.initial_prompt)
        
        # Register functions if provided
        if self.config.functions:
            for func_def in self.config.functions:
                # This is a simplified example - actual function registration
                # would need to handle the function implementation
                pass
        
        return assistant


async def create_livekit_agent(
    job_context: JobContext,
    config: LiveKitAgentConfig
) -> agents.VoiceAssistant:
    """
    Create a LiveKit agent with Knova AI providers.
    
    This is the main entry point for creating agents that work with LiveKit rooms.
    """
    adapter = LiveKitProviderAdapter(config)
    assistant = await adapter.create_voice_assistant()
    
    # Connect to the LiveKit room
    await assistant.start(job_context.room)
    
    logger.info(
        f"Started {config.agent_name} in room {job_context.room.name} "
        f"with participant {job_context.participant.identity}"
    )
    
    return assistant


def create_worker_options(
    config: LiveKitAgentConfig,
    worker_type: agents.WorkerType = agents.WorkerType.ROOM
) -> WorkerOptions:
    """Create LiveKit WorkerOptions with Knova AI configuration"""
    
    async def entrypoint(job_context: JobContext):
        """Worker entrypoint"""
        await create_livekit_agent(job_context, config)
    
    return WorkerOptions(
        entrypoint=entrypoint,
        worker_type=worker_type
    )