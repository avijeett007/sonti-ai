"""Agent worker implementation"""

import logging
from typing import Dict, Any, Optional

from livekit import agents
from livekit.agents import JobContext, VoiceAssistant

from .handlers.voice import VoiceHandler
from .handlers.sip import SIPHandler
from .orchestrator.workflow import WorkflowOrchestrator

logger = logging.getLogger(__name__)


class AgentWorker:
    """Main agent worker class"""
    
    def __init__(self, ctx: JobContext, config: Dict[str, Any]):
        self.ctx = ctx
        self.config = config
        self.agent_type = config.get("type", "voice")
        self.assistant: Optional[VoiceAssistant] = None
        
    async def start(self):
        """Start the agent worker"""
        logger.info(f"Starting {self.agent_type} agent")
        
        # Connect to the room
        await self.ctx.connect()
        
        if self.agent_type == "voice":
            await self._start_voice_agent()
        elif self.agent_type == "workflow":
            await self._start_workflow_agent()
        else:
            logger.error(f"Unknown agent type: {self.agent_type}")
            
    async def _start_voice_agent(self):
        """Start a voice agent"""
        handler = VoiceHandler(self.ctx, self.config)
        self.assistant = await handler.create_assistant()
        
        # Start the assistant
        self.assistant.start(self.ctx.room)
        
        # Handle participant events
        @self.ctx.room.on("participant_connected")
        def on_participant_connected(participant):
            logger.info(f"Participant connected: {participant.sid}")
            if not participant.kind == "AGENT":
                self.assistant.start_session(participant)
                
    async def _start_workflow_agent(self):
        """Start a workflow agent"""
        orchestrator = WorkflowOrchestrator(self.ctx, self.config)
        await orchestrator.start()
        
    async def stop(self):
        """Stop the agent worker"""
        logger.info("Stopping agent worker")
        if self.assistant:
            # Clean up assistant resources
            pass