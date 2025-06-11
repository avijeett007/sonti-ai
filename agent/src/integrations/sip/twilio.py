"""Twilio SIP provider implementation"""

import aiohttp
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .base import SIPProvider, SIPConfig, InboundCall, OutboundCall

logger = logging.getLogger(__name__)


class TwilioProvider(SIPProvider):
    """Twilio SIP provider implementation"""
    
    def __init__(self, config: SIPConfig):
        super().__init__(config)
        self.client = Client(config.account_sid, config.auth_token)
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.account_sid}"
        
    async def initialize(self):
        """Initialize Twilio connection"""
        # Verify account credentials
        try:
            account = self.client.api.accounts(self.config.account_sid).fetch()
            logger.info(f"Twilio account verified: {account.friendly_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}")
            raise
            
    async def create_trunk(self, trunk_config: Dict[str, Any]) -> str:
        """Create a SIP trunk in Twilio"""
        trunk = self.client.trunking.trunks.create(
            friendly_name=trunk_config.get("name", "Knova AI Trunk"),
            domain_name=trunk_config.get("domain"),
            disaster_recovery_url=trunk_config.get("disaster_recovery_url"),
            disaster_recovery_method=trunk_config.get("disaster_recovery_method", "POST"),
            secure=trunk_config.get("secure", True)
        )
        return trunk.sid
        
    async def handle_inbound_call(self, call: InboundCall) -> Dict[str, Any]:
        """Handle an inbound call from Twilio"""
        # Get the agent mapped to this number
        agent_id = self.get_agent_for_number(call.to_number)
        if not agent_id:
            # Return a default response if no agent is mapped
            response = VoiceResponse()
            response.say("Thank you for calling. Please wait while we connect you.")
            response.pause(length=1)
            response.redirect(url=f"{self.config.webhook_base_url}/twilio/connect/{call.call_id}")
            return {"twiml": str(response), "agent_id": None}
            
        # Emit call event
        await self.emit_call_event("inbound_call", {
            "call_id": call.call_id,
            "from": call.from_number,
            "to": call.to_number,
            "agent_id": agent_id
        })
        
        # Generate TwiML to connect to LiveKit
        response = VoiceResponse()
        response.connect().stream(
            url=f"wss://livekit-server/twilio-stream/{agent_id}",
            parameters={
                "agent_id": agent_id,
                "call_id": call.call_id
            }
        )
        
        return {"twiml": str(response), "agent_id": agent_id}
        
    async def make_call(self, to_number: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> OutboundCall:
        """Make an outbound call"""
        # Select from number from available numbers
        from_number = self.config.phone_numbers[0] if self.config.phone_numbers else None
        if not from_number:
            raise ValueError("No phone numbers configured")
            
        call = self.client.calls.create(
            to=to_number,
            from_=from_number,
            url=f"{self.config.webhook_base_url}/twilio/outbound/{agent_id}",
            status_callback=f"{self.config.webhook_base_url}/twilio/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            machine_detection="DetectMessageEnd" if metadata and metadata.get("detect_voicemail") else None
        )
        
        outbound_call = OutboundCall(
            call_id=call.sid,
            to_number=to_number,
            from_number=from_number,
            agent_id=agent_id,
            status="initiated",
            started_at=datetime.utcnow(),
            metadata=metadata
        )
        
        await self.emit_call_event("outbound_call_initiated", {
            "call": outbound_call,
            "twilio_sid": call.sid
        })
        
        return outbound_call
        
    async def end_call(self, call_id: str) -> bool:
        """End an active call"""
        try:
            call = self.client.calls(call_id).update(status="completed")
            await self.emit_call_event("call_ended", {"call_id": call_id})
            return True
        except Exception as e:
            logger.error(f"Failed to end call {call_id}: {e}")
            return False
            
    async def transfer_call(self, call_id: str, to_number: str) -> bool:
        """Transfer a call to another number"""
        try:
            call = self.client.calls(call_id).update(
                url=f"{self.config.webhook_base_url}/twilio/transfer",
                method="POST"
            )
            # The webhook will handle the actual transfer logic
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
            # Twilio doesn't support sending DTMF to an active call
            # This would typically be handled by the media stream
            logger.warning("DTMF sending not supported for active calls in Twilio")
            return False
        except Exception as e:
            logger.error(f"Failed to send DTMF: {e}")
            return False
            
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get current call status"""
        try:
            call = self.client.calls(call_id).fetch()
            return {
                "call_id": call.sid,
                "status": call.status,
                "duration": call.duration,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "price": call.price,
                "price_unit": call.price_unit
            }
        except Exception as e:
            logger.error(f"Failed to get call status: {e}")
            return {"error": str(e)}
            
    async def start_recording(self, call_id: str) -> str:
        """Start call recording"""
        try:
            recording = self.client.calls(call_id).recordings.create(
                recording_status_callback=f"{self.config.webhook_base_url}/twilio/recording-status"
            )
            await self.emit_call_event("recording_started", {
                "call_id": call_id,
                "recording_id": recording.sid
            })
            return recording.sid
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise
            
    async def stop_recording(self, call_id: str, recording_id: str) -> bool:
        """Stop call recording"""
        try:
            recording = self.client.calls(call_id).recordings(recording_id).update(
                status="stopped"
            )
            await self.emit_call_event("recording_stopped", {
                "call_id": call_id,
                "recording_id": recording_id
            })
            return True
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
            
    def generate_webhook_response(self, action: str, params: Dict[str, Any]) -> str:
        """Generate TwiML response"""
        response = VoiceResponse()
        
        if action == "say":
            response.say(
                params.get("text", ""),
                voice=params.get("voice", "Polly.Joanna"),
                language=params.get("language", "en-US")
            )
        elif action == "play":
            response.play(params.get("url", ""))
        elif action == "gather":
            gather = response.gather(
                num_digits=params.get("num_digits", 1),
                timeout=params.get("timeout", 5),
                action=params.get("action_url", "")
            )
            if params.get("say_text"):
                gather.say(params.get("say_text"))
        elif action == "pause":
            response.pause(length=params.get("length", 1))
        elif action == "hangup":
            response.hangup()
        elif action == "redirect":
            response.redirect(url=params.get("url", ""))
        elif action == "connect":
            connect = response.connect()
            if params.get("stream_url"):
                connect.stream(url=params.get("stream_url"))
                
        return str(response)
        
    async def handle_webhook(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhooks from Twilio"""
        if event_type == "voice":
            # Handle voice webhook
            call = InboundCall(
                call_id=data.get("CallSid"),
                from_number=data.get("From"),
                to_number=data.get("To"),
                status=data.get("CallStatus"),
                metadata=data
            )
            return await self.handle_inbound_call(call)
        elif event_type == "status":
            # Handle status callback
            await self.emit_call_event("call_status_update", {
                "call_id": data.get("CallSid"),
                "status": data.get("CallStatus"),
                "duration": data.get("CallDuration")
            })
            return {"success": True}
        elif event_type == "gather":
            # Handle DTMF gathering
            digits = data.get("Digits", "")
            call_id = data.get("CallSid")
            await self.handle_dtmf_input(call_id, digits)
            return {"success": True}
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
            return {"error": "Unknown event type"}