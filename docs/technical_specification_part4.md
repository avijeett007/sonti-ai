# Knova AI: Technical Specification (Part 4)

## 6. Communication Channels

### 6.1 Web-based Communication

#### 6.1.1 LiveKit Integration
Web-based communication will be implemented using LiveKit's WebRTC infrastructure:

```typescript
// Frontend code for connecting to a LiveKit room with an agent
import { Room, RoomEvent, LocalParticipant, RemoteParticipant } from 'livekit-client';

export async function connectToAgent(agentId: string, userName: string): Promise<Room> {
  // Get token from backend
  const response = await fetch('/api/livekit/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      agentId, 
      userName,
      metadata: JSON.stringify({ agent_id: agentId })
    }),
  });
  
  const { token, url } = await response.json();
  
  // Connect to LiveKit room
  const room = new Room({
    adaptiveStream: true,
    dynacast: true,
    audioOutput: { deviceId: 'default' },
  });
  
  await room.connect(url, token);
  
  // Publish local audio track
  await room.localParticipant.enableAudio();
  
  return room;
}
```

#### 6.1.2 Room Management
- Each agent instance will be assigned to a unique LiveKit room
- Room names will follow the pattern: `knova-{agent_id}-{session_id}`
- Room metadata will include agent configuration details

### 6.2 Telephony Integration

#### 6.2.1 SIP Integration
Telephony integration will leverage LiveKit's SIP capabilities:

```python
# Backend code for handling inbound calls
from fastapi import FastAPI, Request
from livekit_server_sdk import WebhookReceiver

app = FastAPI()
webhook_receiver = WebhookReceiver("<api-key>", "<api-secret>")

@app.post("/webhooks/sip/inbound")
async def handle_inbound_call(request: Request):
    body = await request.json()
    event = webhook_receiver.receive(await request.body(), request.headers)
    
    if event.event_type == "sip.inbound_call":
        # Extract caller information
        caller_id = event.inbound_call.from_number
        
        # Determine which agent to route to based on the dialed number
        dialed_number = event.inbound_call.to_number
        agent_id = await get_agent_id_for_number(dialed_number)
        
        # Create room for the call
        room_name = f"knova-{agent_id}-{uuid.uuid4()}"
        
        # Create room with SIP participant
        await create_room_with_sip(
            room_name=room_name,
            sip_participant={
                "call_id": event.inbound_call.call_id,
                "from_number": caller_id
            },
            metadata=json.dumps({"agent_id": agent_id})
        )
        
        return {"status": "success"}
```

#### 6.2.2 DTMF Handling
DTMF tones will be processed using LiveKit's data channel capabilities:

```python
@function_tool()
async def handle_dtmf(
    self,
    context: RunContext,
    digits: str,
) -> dict[str, Any]:
    """Handle DTMF tones from the user.
    
    Args:
        digits: The DTMF digits pressed by the user.
    """
    # Process DTMF input based on current context
    if context.get_state("awaiting_menu_selection"):
        menu_option = int(digits)
        return await self._process_menu_selection(context, menu_option)
    
    # Default handling
    return {"status": "processed", "digits": digits}
```

### 6.3 Future: Video and Avatar Integration

#### 6.3.1 Video Integration
Video capabilities will be added using LiveKit's video track support:

```typescript
// Frontend code for enabling video
async function enableAgentVideo(room: Room, avatarUrl: string) {
  // Create video element for avatar
  const videoElement = document.createElement('video');
  videoElement.autoplay = true;
  videoElement.muted = true;
  
  // Add video element to DOM
  document.getElementById('agent-container').appendChild(videoElement);
  
  // Subscribe to agent's video track
  room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
    if (participant.identity.startsWith('agent-') && track.kind === 'video') {
      track.attach(videoElement);
    }
  });
}
```

#### 6.3.2 Avatar Integration
Avatar capabilities will be implemented using LiveKit's avatar plugins:

```python
# Agent code for enabling avatar
from livekit.plugins.avatar import BeyondPresence

async def setup_avatar(session: AgentSession, avatar_config: dict):
    """Set up avatar for the agent session."""
    avatar = BeyondPresence(
        api_key=avatar_config["api_key"],
        character_id=avatar_config["character_id"],
        voice_id=avatar_config["voice_id"]
    )
    
    await session.enable_avatar(avatar)
```

## 7. Deployment Architecture

### 7.1 Kubernetes Deployment

#### 7.1.1 Cluster Configuration
- Kubernetes cluster with autoscaling node groups
- Separate namespaces for development, staging, and production
- Resource quotas and limits for each component

#### 7.1.2 Component Deployment
- Frontend: Deployed as stateless pods with horizontal scaling
- Backend Services: Deployed as stateless services with horizontal scaling
- Agent Workers: Deployed as stateful sets with horizontal scaling
- Databases: Deployed as stateful sets with persistent volumes

#### 7.1.3 Kubernetes Resources
```yaml
# Example Kubernetes deployment for agent workers
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knova-agent-worker
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: knova-agent-worker
  template:
    metadata:
      labels:
        app: knova-agent-worker
    spec:
      containers:
      - name: agent-worker
        image: knova/agent-worker:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: LIVEKIT_URL
          valueFrom:
            secretKeyRef:
              name: livekit-credentials
              key: url
        - name: LIVEKIT_API_KEY
          valueFrom:
            secretKeyRef:
              name: livekit-credentials
              key: api_key
        - name: LIVEKIT_API_SECRET
          valueFrom:
            secretKeyRef:
              name: livekit-credentials
              key: api_secret
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
```
