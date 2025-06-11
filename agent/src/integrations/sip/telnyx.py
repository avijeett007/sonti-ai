"""Telnyx SIP provider implementation"""

import aiohttp
import telnyx
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json

from .base import SIPProvider, SIPConfig, InboundCall, OutboundCall

logger = logging.getLogger(__name__)


class TelnyxProvider(SIPProvider):
    """Telnyx SIP provider implementation"""
    
    def __init__(self, config: SIPConfig):
        super().__init__(config)
        telnyx.api_key = config.auth_token
        self.session = None
        
    async def initialize(self):
        """Initialize Telnyx connection"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.config.auth_token}",
                "Content-Type": "application/json"
            }
        )
        
        # Verify API key
        try:
            async with self.session.get("https://api.telnyx.com/v2/phone_numbers") as resp:
                if resp.status == 200:
                    logger.info("Telnyx API key verified")
                else:
                    raise ValueError("Invalid Telnyx API key")
        except Exception as e:
            logger.error(f"Failed to initialize Telnyx: {e}")
            raise
            
    async def create_trunk(self, trunk_config: Dict[str, Any]) -> str:
        """Create a SIP connection in Telnyx"""
        connection_data = {
            "connection_name": trunk_config.get("name", "Knova AI Connection"),
            "active": True,
            "anchorsite_override": trunk_config.get("region", "Latency"),
            "webhook_event_url": f"{self.config.webhook_base_url}/telnyx/events",
            "webhook_event_failover_url": trunk_config.get("failover_url"),
            "webhook_api_version": "2",
            "webhook_timeout_secs": trunk_config.get("timeout", 30)
        }
        
        connection = telnyx.SIPConnection.create(**connection_data)
        return connection.id
        
    async def handle_inbound_call(self, call: InboundCall) -> Dict[str, Any]:
        """Handle an inbound call from Telnyx"""
        # Get the agent mapped to this number
        agent_id = self.get_agent_for_number(call.to_number)
        
        # Emit call event
        await self.emit_call_event("inbound_call", {
            "call_id": call.call_id,
            "from": call.from_number,
            "to": call.to_number,
            "agent_id": agent_id
        })
        
        # Generate TeXML response
        texml = self._generate_texml("answer", {
            "agent_id": agent_id,
            "call_id": call.call_id
        })
        
        return {"texml": texml, "agent_id": agent_id}
        
    async def make_call(self, to_number: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> OutboundCall:
        """Make an outbound call"""
        from_number = self.config.phone_numbers[0] if self.config.phone_numbers else None
        if not from_number:
            raise ValueError("No phone numbers configured")
            
        call_data = {
            "connection_id": self.config.extra_config.get("connection_id"),
            "to": to_number,
            "from": from_number,
            "answering_machine_detection": "detect" if metadata and metadata.get("detect_voicemail") else None,
            "webhook_url": f"{self.config.webhook_base_url}/telnyx/answer/{agent_id}",
            "webhook_failover_url": f"{self.config.webhook_base_url}/telnyx/failover"
        }
        
        call = telnyx.Call.create(**call_data)
        
        outbound_call = OutboundCall(
            call_id=call.call_control_id,
            to_number=to_number,
            from_number=from_number,
            agent_id=agent_id,
            status="initiated",
            started_at=datetime.utcnow(),
            metadata=metadata
        )
        
        await self.emit_call_event("outbound_call_initiated", {
            "call": outbound_call,
            "telnyx_id": call.call_control_id
        })
        
        return outbound_call
        
    async def end_call(self, call_id: str) -> bool:
        """End an active call"""
        try:
            call = telnyx.Call.retrieve(call_id)
            call.hangup()
            await self.emit_call_event("call_ended", {"call_id": call_id})
            return True
        except Exception as e:
            logger.error(f"Failed to end call {call_id}: {e}")
            return False
            
    async def transfer_call(self, call_id: str, to_number: str) -> bool:
        """Transfer a call to another number"""
        try:
            call = telnyx.Call.retrieve(call_id)
            call.transfer(to=to_number)
            await self.emit_call_event("call_transfer_initiated", {
                "call_id": call_id,
                "to_number": to_number
            })
            return True
        except Exception as e:
            logger.error(f"Failed to transfer call {call_id}: {e}")
            return False
            
    async def send_dtmf(self, call_id: str, digits: str) -> bool:
        """Send DTMF tones"""
        try:
            call = telnyx.Call.retrieve(call_id)
            call.send_dtmf(digits=digits)
            return True
        except Exception as e:
            logger.error(f"Failed to send DTMF: {e}")
            return False
            
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get current call status"""
        try:
            async with self.session.get(f"https://api.telnyx.com/v2/calls/{call_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    call_data = data.get("data", {})
                    return {
                        "call_id": call_data.get("call_control_id"),
                        "status": call_data.get("call_leg_state"),
                        "duration": call_data.get("call_duration_secs"),
                        "direction": call_data.get("direction"),
                        "from": call_data.get("from"),
                        "to": call_data.get("to"),
                        "start_time": call_data.get("start_time"),
                        "end_time": call_data.get("end_time")
                    }
                else:
                    return {"error": f"Status code: {resp.status}"}
        except Exception as e:
            logger.error(f"Failed to get call status: {e}")
            return {"error": str(e)}
            
    async def start_recording(self, call_id: str) -> str:
        """Start call recording"""
        try:
            call = telnyx.Call.retrieve(call_id)
            recording = call.start_recording(
                format="mp3",
                channels="dual"
            )
            recording_id = recording.get("result", {}).get("recording_id")
            await self.emit_call_event("recording_started", {
                "call_id": call_id,
                "recording_id": recording_id
            })
            return recording_id
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise
            
    async def stop_recording(self, call_id: str, recording_id: str) -> bool:
        """Stop call recording"""
        try:
            call = telnyx.Call.retrieve(call_id)
            call.stop_recording()
            await self.emit_call_event("recording_stopped", {
                "call_id": call_id,
                "recording_id": recording_id
            })
            return True
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
            
    def generate_webhook_response(self, action: str, params: Dict[str, Any]) -> str:
        """Generate TeXML response"""
        return self._generate_texml(action, params)
        
    def _generate_texml(self, action: str, params: Dict[str, Any]) -> str:
        """Generate TeXML markup"""
        texml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<Response>']
        
        if action == "answer":
            texml_parts.append('<Answer/>')
            if params.get("agent_id"):
                # Connect to LiveKit stream
                texml_parts.append(
                    f'<Stream url="wss://livekit-server/telnyx-stream/{params["agent_id"]}" '
                    f'bidirectional_mode="true"/>'
                )
        elif action == "say":
            text = params.get("text", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            voice = params.get("voice", "female")
            texml_parts.append(f'<Say voice="{voice}">{text}</Say>')
        elif action == "play":
            texml_parts.append(f'<Play>{params.get("url", "")}</Play>')
        elif action == "gather":
            texml_parts.append(
                f'<Gather numDigits="{params.get("num_digits", 1)}" '
                f'timeout="{params.get("timeout", 5)}" '
                f'action="{params.get("action_url", "")}">'
            )
            if params.get("say_text"):
                text = params["say_text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                texml_parts.append(f'<Say>{text}</Say>')
            texml_parts.append('</Gather>')
        elif action == "pause":
            texml_parts.append(f'<Pause length="{params.get("length", 1)}"/>')
        elif action == "hangup":
            texml_parts.append('<Hangup/>')
        elif action == "redirect":
            texml_parts.append(f'<Redirect>{params.get("url", "")}</Redirect>')
            
        texml_parts.append('</Response>')
        return '\n'.join(texml_parts)
        
    async def handle_webhook(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhooks from Telnyx"""
        event_data = data.get("data", {})
        event_name = event_data.get("event_type", "")
        
        if event_name == "call.initiated":
            call = InboundCall(
                call_id=event_data.get("call_control_id"),
                from_number=event_data.get("from"),
                to_number=event_data.get("to"),
                status="initiated",
                metadata=event_data
            )
            return await self.handle_inbound_call(call)
        elif event_name == "call.answered":
            await self.emit_call_event("call_answered", {
                "call_id": event_data.get("call_control_id"),
                "direction": event_data.get("direction")
            })
            return {"success": True}
        elif event_name == "call.hangup":
            await self.emit_call_event("call_hangup", {
                "call_id": event_data.get("call_control_id"),
                "cause": event_data.get("hangup_cause")
            })
            return {"success": True}
        elif event_name == "call.dtmf.received":
            call_id = event_data.get("call_control_id")
            digit = event_data.get("digit")
            await self.handle_dtmf_input(call_id, digit)
            return {"success": True}
        else:
            logger.warning(f"Unknown Telnyx event: {event_name}")
            return {"error": "Unknown event type"}
            
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup session on exit"""
        if self.session:
            await self.session.close()