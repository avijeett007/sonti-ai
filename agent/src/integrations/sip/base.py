"""Base SIP provider interface"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import asyncio


@dataclass
class SIPConfig:
    """Base configuration for SIP providers"""
    provider: str
    account_sid: str
    auth_token: str
    webhook_base_url: str
    phone_numbers: list[str]
    extra_config: Dict[str, Any] = None


@dataclass
class InboundCall:
    """Inbound call information"""
    call_id: str
    from_number: str
    to_number: str
    direction: str = "inbound"
    status: str = "ringing"
    started_at: datetime = None
    metadata: Dict[str, Any] = None


@dataclass
class OutboundCall:
    """Outbound call information"""
    call_id: str
    to_number: str
    from_number: str
    agent_id: str
    direction: str = "outbound"
    status: str = "initiated"
    started_at: datetime = None
    metadata: Dict[str, Any] = None


class SIPProvider(ABC):
    """Abstract base class for SIP providers"""
    
    def __init__(self, config: SIPConfig):
        self.config = config
        self._call_handlers: Dict[str, Callable] = {}
        self._dtmf_handlers: Dict[str, Callable] = {}
        
    @abstractmethod
    async def initialize(self):
        """Initialize the provider connection"""
        pass
        
    @abstractmethod
    async def create_trunk(self, trunk_config: Dict[str, Any]) -> str:
        """Create a SIP trunk"""
        pass
        
    @abstractmethod
    async def handle_inbound_call(self, call: InboundCall) -> Dict[str, Any]:
        """Handle an inbound call"""
        pass
        
    @abstractmethod
    async def make_call(self, to_number: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> OutboundCall:
        """Initiate an outbound call"""
        pass
        
    @abstractmethod
    async def end_call(self, call_id: str) -> bool:
        """End an active call"""
        pass
        
    @abstractmethod
    async def transfer_call(self, call_id: str, to_number: str) -> bool:
        """Transfer a call to another number"""
        pass
        
    @abstractmethod
    async def send_dtmf(self, call_id: str, digits: str) -> bool:
        """Send DTMF tones"""
        pass
        
    @abstractmethod
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get current call status"""
        pass
        
    @abstractmethod
    async def start_recording(self, call_id: str) -> str:
        """Start call recording"""
        pass
        
    @abstractmethod
    async def stop_recording(self, call_id: str, recording_id: str) -> bool:
        """Stop call recording"""
        pass
        
    @abstractmethod
    def generate_webhook_response(self, action: str, params: Dict[str, Any]) -> str:
        """Generate provider-specific webhook response (TwiML, TeXML, etc.)"""
        pass
        
    def register_call_handler(self, event: str, handler: Callable):
        """Register a handler for call events"""
        self._call_handlers[event] = handler
        
    def register_dtmf_handler(self, handler: Callable):
        """Register a handler for DTMF input"""
        self._dtmf_handlers['dtmf'] = handler
        
    async def emit_call_event(self, event: str, data: Dict[str, Any]):
        """Emit a call event to registered handlers"""
        if event in self._call_handlers:
            handler = self._call_handlers[event]
            if asyncio.iscoroutinefunction(handler):
                await handler(data)
            else:
                handler(data)
                
    async def handle_dtmf_input(self, call_id: str, digits: str):
        """Handle DTMF input from the caller"""
        if 'dtmf' in self._dtmf_handlers:
            handler = self._dtmf_handlers['dtmf']
            if asyncio.iscoroutinefunction(handler):
                await handler(call_id, digits)
            else:
                handler(call_id, digits)
                
    def map_agent_to_number(self, phone_number: str, agent_id: str):
        """Map a phone number to a specific agent"""
        # This would typically update a mapping in the database
        # For now, we'll store it in memory
        if not hasattr(self, '_number_mappings'):
            self._number_mappings = {}
        self._number_mappings[phone_number] = agent_id
        
    def get_agent_for_number(self, phone_number: str) -> Optional[str]:
        """Get the agent ID mapped to a phone number"""
        if hasattr(self, '_number_mappings'):
            return self._number_mappings.get(phone_number)
        return None