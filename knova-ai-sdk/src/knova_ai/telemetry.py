"""Telemetry collection for Knova AI SDK"""

import asyncio
import platform
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

import aiohttp
from pydantic import BaseModel


class TelemetryEvent(BaseModel):
    """Telemetry event model"""
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    sdk_version: str
    python_version: str
    platform: str
    

class TelemetryCollector:
    """Handles telemetry collection and submission"""
    
    def __init__(self, api_url: str, license_key: str):
        self.api_url = api_url
        self.license_key = license_key
        self.enabled = True
        self._queue: List[TelemetryEvent] = []
        self._background_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Start telemetry collection"""
        if not self.enabled:
            return
            
        self._session = aiohttp.ClientSession()
        self._background_task = asyncio.create_task(self._submit_loop())
        
    async def stop(self):
        """Stop telemetry collection and flush remaining events"""
        if self._background_task:
            self._background_task.cancel()
            
        # Flush remaining events
        if self._queue:
            await self._submit_batch()
            
        if self._session:
            await self._session.close()
            
    async def track_event(self, event_type: str, data: Dict[str, Any]):
        """Track a telemetry event"""
        if not self.enabled:
            return
            
        event = TelemetryEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data,
            sdk_version="0.1.0",  # TODO: Get from package version
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            platform=platform.system()
        )
        
        self._queue.append(event)
        
        # Submit immediately if queue is getting large
        if len(self._queue) >= 50:
            await self._submit_batch()
            
    async def _submit_loop(self):
        """Background loop to submit telemetry batches"""
        while True:
            try:
                await asyncio.sleep(60)  # Submit every minute
                if self._queue:
                    await self._submit_batch()
            except asyncio.CancelledError:
                break
            except Exception:
                # Silently ignore telemetry errors
                pass
                
    async def _submit_batch(self):
        """Submit a batch of telemetry events"""
        if not self._queue or not self._session:
            return
            
        # Take current queue and reset
        events = self._queue
        self._queue = []
        
        try:
            async with self._session.post(
                f"{self.api_url}/v1/telemetry",
                json={
                    "events": [event.model_dump() for event in events]
                },
                headers={"Authorization": f"Bearer {self.license_key}"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                # We don't care about the response for telemetry
                pass
        except Exception:
            # Silently ignore telemetry errors
            pass
            
    def disable(self):
        """Disable telemetry collection"""
        self.enabled = False