"""Plivo SIP provider implementation"""

import plivo
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import xml.etree.ElementTree as ET

from .base import SIPProvider, SIPConfig, InboundCall, OutboundCall

logger = logging.getLogger(__name__)


class PlivoProvider(SIPProvider):
    """Plivo SIP provider implementation"""
    
    def __init__(self, config: SIPConfig):
        super().__init__(config)
        self.client = plivo.RestClient(config.account_sid, config.auth_token)
        self.session = None
        
    async def initialize(self):
        """Initialize Plivo connection"""
        # Verify account credentials
        try:
            account = self.client.accounts.get()
            logger.info(f"Plivo account verified: {account['name']}")
        except Exception as e:
            logger.error(f"Failed to initialize Plivo: {e}")
            raise
            
    async def create_trunk(self, trunk_config: Dict[str, Any]) -> str:
        """Create a SIP endpoint in Plivo"""
        endpoint = self.client.endpoints.create(
            username=trunk_config.get("username", "knova_ai_endpoint"),
            password=trunk_config.get("password"),
            alias=trunk_config.get("alias", "Knova AI Endpoint")
        )
        return endpoint['endpoint_id']
        
    async def handle_inbound_call(self, call: InboundCall) -> Dict[str, Any]:
        """Handle an inbound call from Plivo"""
        # Get the agent mapped to this number
        agent_id = self.get_agent_for_number(call.to_number)
        
        # Emit call event
        await self.emit_call_event("inbound_call", {
            "call_id": call.call_id,
            "from": call.from_number,
            "to": call.to_number,
            "agent_id": agent_id
        })
        
        # Generate Plivo XML response
        xml_response = self._generate_plivo_xml("answer", {
            "agent_id": agent_id,
            "call_id": call.call_id
        })
        
        return {"xml": xml_response, "agent_id": agent_id}
        
    async def make_call(self, to_number: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> OutboundCall:
        """Make an outbound call"""
        from_number = self.config.phone_numbers[0] if self.config.phone_numbers else None
        if not from_number:
            raise ValueError("No phone numbers configured")
            
        call_params = {
            "from": from_number,
            "to": to_number,
            "answer_url": f"{self.config.webhook_base_url}/plivo/answer/{agent_id}",
            "answer_method": "POST",
            "hangup_url": f"{self.config.webhook_base_url}/plivo/hangup",
            "hangup_method": "POST",
            "machine_detection": "hangup" if metadata and metadata.get("detect_voicemail") else None,
            "machine_detection_time": 5000,
            "machine_detection_url": f"{self.config.webhook_base_url}/plivo/machine"
        }
        
        response = self.client.calls.create(**call_params)
        
        outbound_call = OutboundCall(
            call_id=response['request_uuid'],
            to_number=to_number,
            from_number=from_number,
            agent_id=agent_id,
            status="initiated",
            started_at=datetime.utcnow(),
            metadata=metadata
        )
        
        await self.emit_call_event("outbound_call_initiated", {
            "call": outbound_call,
            "plivo_uuid": response['request_uuid']
        })
        
        return outbound_call
        
    async def end_call(self, call_id: str) -> bool:
        """End an active call"""
        try:
            self.client.calls.delete(call_id)
            await self.emit_call_event("call_ended", {"call_id": call_id})
            return True
        except Exception as e:
            logger.error(f"Failed to end call {call_id}: {e}")
            return False
            
    async def transfer_call(self, call_id: str, to_number: str) -> bool:
        """Transfer a call to another number"""
        try:
            self.client.calls.update(
                call_id,
                legs="aleg",
                aleg_url=f"{self.config.webhook_base_url}/plivo/transfer?to={to_number}"
            )
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
            self.client.calls.send_digits(call_id, digits=digits)
            return True
        except Exception as e:
            logger.error(f"Failed to send DTMF: {e}")
            return False
            
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get current call status"""
        try:
            call = self.client.calls.get(call_id)
            return {
                "call_id": call['call_uuid'],
                "status": call['call_status'],
                "duration": call['call_duration'],
                "direction": call['call_direction'],
                "from": call['from_number'],
                "to": call['to_number'],
                "start_time": call['initiation_time'],
                "end_time": call['end_time'],
                "total_amount": call['total_amount'],
                "total_rate": call['total_rate']
            }
        except Exception as e:
            logger.error(f"Failed to get call status: {e}")
            return {"error": str(e)}
            
    async def start_recording(self, call_id: str) -> str:
        """Start call recording"""
        try:
            response = self.client.calls.record(
                call_id,
                time_limit=3600,  # 1 hour max
                file_format="mp3",
                transcription_type="auto",
                callback_url=f"{self.config.webhook_base_url}/plivo/recording",
                callback_method="POST"
            )
            recording_id = response.get('recording_id')
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
            self.client.calls.stop_recording(call_id)
            await self.emit_call_event("recording_stopped", {
                "call_id": call_id,
                "recording_id": recording_id
            })
            return True
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
            
    def generate_webhook_response(self, action: str, params: Dict[str, Any]) -> str:
        """Generate Plivo XML response"""
        return self._generate_plivo_xml(action, params)
        
    def _generate_plivo_xml(self, action: str, params: Dict[str, Any]) -> str:
        """Generate Plivo XML markup"""
        response = ET.Element("Response")
        
        if action == "answer":
            if params.get("agent_id"):
                # For LiveKit integration, we would use Stream element
                # but Plivo doesn't have native WebSocket streaming
                # So we'll use a conference bridge approach
                conference = ET.SubElement(response, "Conference")
                conference.set("callbackUrl", f"{self.config.webhook_base_url}/plivo/conference")
                conference.set("callbackMethod", "POST")
                conference.set("waitSound", f"{self.config.webhook_base_url}/plivo/wait-music")
                conference.text = f"knova-agent-{params['agent_id']}"
        elif action == "say":
            speak = ET.SubElement(response, "Speak")
            speak.set("voice", params.get("voice", "WOMAN"))
            speak.set("language", params.get("language", "en-US"))
            speak.text = params.get("text", "")
        elif action == "play":
            play = ET.SubElement(response, "Play")
            play.text = params.get("url", "")
        elif action == "gather":
            get_digits = ET.SubElement(response, "GetDigits")
            get_digits.set("numDigits", str(params.get("num_digits", 1)))
            get_digits.set("timeout", str(params.get("timeout", 5)))
            get_digits.set("action", params.get("action_url", ""))
            if params.get("say_text"):
                speak = ET.SubElement(get_digits, "Speak")
                speak.text = params.get("say_text")
        elif action == "pause":
            wait = ET.SubElement(response, "Wait")
            wait.set("length", str(params.get("length", 1)))
        elif action == "hangup":
            ET.SubElement(response, "Hangup")
        elif action == "redirect":
            redirect = ET.SubElement(response, "Redirect")
            redirect.text = params.get("url", "")
        elif action == "dial":
            dial = ET.SubElement(response, "Dial")
            dial.set("callbackUrl", f"{self.config.webhook_base_url}/plivo/dial-callback")
            number = ET.SubElement(dial, "Number")
            number.text = params.get("number", "")
            
        return ET.tostring(response, encoding='unicode')
        
    async def handle_webhook(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhooks from Plivo"""
        if event_type == "answer":
            call = InboundCall(
                call_id=data.get("CallUUID"),
                from_number=data.get("From"),
                to_number=data.get("To"),
                direction=data.get("Direction"),
                status=data.get("CallStatus"),
                metadata=data
            )
            return await self.handle_inbound_call(call)
        elif event_type == "hangup":
            await self.emit_call_event("call_hangup", {
                "call_id": data.get("CallUUID"),
                "duration": data.get("Duration"),
                "end_time": data.get("EndTime")
            })
            return {"success": True}
        elif event_type == "digits":
            call_id = data.get("CallUUID")
            digits = data.get("Digits", "")
            await self.handle_dtmf_input(call_id, digits)
            # Return continuation XML
            return {"xml": self._generate_plivo_xml("say", {"text": "Thank you"})}
        elif event_type == "recording":
            await self.emit_call_event("recording_complete", {
                "call_id": data.get("CallUUID"),
                "recording_url": data.get("RecordingUrl"),
                "recording_duration": data.get("RecordingDuration")
            })
            return {"success": True}
        elif event_type == "machine":
            # Machine detection result
            machine_detected = data.get("Machine") == "true"
            await self.emit_call_event("machine_detection", {
                "call_id": data.get("CallUUID"),
                "is_machine": machine_detected
            })
            if machine_detected:
                return {"xml": self._generate_plivo_xml("hangup", {})}
            else:
                return {"xml": self._generate_plivo_xml("redirect", {
                    "url": f"{self.config.webhook_base_url}/plivo/continue"
                })}
        else:
            logger.warning(f"Unknown Plivo webhook event: {event_type}")
            return {"error": "Unknown event type"}