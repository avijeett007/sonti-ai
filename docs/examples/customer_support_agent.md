# Building a Customer Support Voice Agent

This example demonstrates how to build a complete customer support voice agent with Knova AI. The agent will be able to handle customer inquiries, provide product information, and escalate to human agents when needed.

## Prerequisites

- Knova AI platform set up and running
- Valid license key configured
- API keys for OpenAI (or other LLM provider)
- API keys for ElevenLabs (or other TTS provider)
- API keys for Deepgram (or other STT provider)
- (Optional) Twilio account for telephony integration

## Step 1: Create the Knowledge Base

First, let's create a knowledge base with product information:

1. Log in to the Knova AI dashboard
2. Navigate to **Knowledge Bases** > **Create New**
3. Fill in the details:
   - Name: `Product Documentation`
   - Description: `Contains information about our products and services`
   - Vector Store: `Supabase` (or your preferred option)
   - Embedding Model: `text-embedding-ada-002`
4. Click **Create**
5. Upload your documentation files:
   - Product manuals (PDF)
   - FAQs (Markdown or Text)
   - Technical specifications (PDF or Text)

## Step 2: Create the Voice Agent

Now, let's create our customer support agent:

1. Navigate to **Agents** > **Create New**
2. Select **Voice Agent**
3. Configure basic details:
   - Name: `Customer Support`
   - Description: `Handles customer inquiries and product support`
4. Configure providers:
   - LLM Provider: `OpenAI`
   - LLM Model: `gpt-4`
   - STT Provider: `Deepgram`
   - STT Model: `nova-2`
   - TTS Provider: `ElevenLabs`
   - Voice: Choose your preferred voice
5. Link to the knowledge base:
   - Select `Product Documentation` from the dropdown
6. Configure the agent prompt:

```
You are a helpful customer support agent for our company. Your name is Support Assistant.

Your goal is to assist customers with their inquiries about our products and services.

When speaking with customers:
1. Be polite, professional, and concise
2. Use the knowledge base to provide accurate information about our products
3. If you don't know an answer, admit it and offer to connect the customer with a human agent
4. Ask clarifying questions if the customer's request is ambiguous
5. Summarize the conversation at the end and ask if there's anything else you can help with

Products we offer:
- Smart Home Hub ($199): Central control system for home automation
- Security Sensors ($49 each): Motion and entry detection
- Smart Thermostats ($129): Energy-efficient temperature control
- Video Doorbells ($159): HD video and two-way audio
```

7. Click **Create Agent**

## Step 3: Test the Agent in the Browser

Before deploying to production, let's test the agent:

1. Navigate to **Agents** > **Customer Support**
2. Click **Test Agent**
3. In the testing interface, try various customer inquiries:
   - "Tell me about your Smart Home Hub"
   - "How much does the Video Doorbell cost?"
   - "Can I integrate third-party devices with your system?"
4. Evaluate the agent's responses and adjust the prompt or knowledge base as needed

## Step 4: Create a Simple Workflow

Now, let's create a workflow for handling different customer intents:

1. Navigate to **Workflows** > **Create New**
2. Name: `Customer Support Flow`
3. Description: `Handles customer support calls with routing`
4. Add a greeting agent node:
   - Node type: `Agent`
   - Select your `Customer Support` agent
   - Position at the start of the workflow
   - Prompt override: "Welcome to our customer support. How can I help you today?"
5. Add an intent router node:
   - Node type: `Condition`
   - Name: `Intent Router`
   - Add conditions:
     - Intent "product_inquiry" → route to Product Info Agent
     - Intent "technical_support" → route to Technical Support Agent
     - Intent "billing" → route to Billing Agent
     - Default → route to General Support Agent
6. Add the specialized agent nodes:
   - Create separate agent nodes for each intent
   - Configure each with specialized prompts
7. Save the workflow

## Step 5: Set Up Telephony Integration

To make your agent accessible via phone:

1. Navigate to **Telephony** > **SIP Trunks** > **Add New**
2. Select **Twilio** as the provider
3. Enter your Twilio credentials:
   - Account SID
   - Auth Token
   - SIP Domain
4. Save the SIP trunk configuration
5. Navigate to **Phone Numbers** > **Add New**
6. Enter the phone number from Twilio
7. Link it to your `Customer Support Flow` workflow
8. Save the phone number mapping

## Step 6: Configure Webhooks

To receive notifications about agent activities:

1. Navigate to **Settings** > **Webhooks** > **Add New**
2. Configure webhook:
   - Name: `Call Events`
   - URL: `https://your-server.com/webhook`
   - Events: Select call.started, call.ended, transcription
   - Secret: Generate a secure secret
3. Save webhook configuration
4. Implement a webhook receiver at your URL that processes these events

## Step 7: Monitor Performance

Once your agent is live:

1. Navigate to **Dashboard** > **Analytics**
2. Monitor key metrics:
   - Call volume and duration
   - Customer satisfaction (if enabled)
   - Common inquiries and issues
   - Escalation rate to human agents
3. Review call transcripts to identify areas for improvement

## Step 8: Iterate and Improve

Based on performance data:

1. Refine your agent's prompt
2. Add more content to your knowledge base
3. Adjust the workflow for better caller experience
4. Update your product information as needed

## Implementing with the Knova AI SDK

You can also implement this example programmatically using the SDK:

```python
from knova_ai import KnovaAI

# Initialize client
client = KnovaAI(
    license_key="your-license-key",
    database_config={"type": "sqlite", "path": "local.db"}
)

# Create knowledge base
kb = await client.create_knowledge_base(
    name="Product Documentation",
    vector_store="supabase"
)

# Upload documents
await kb.add_document("path/to/product_manual.pdf")
await kb.add_document("path/to/faqs.md")

# Create agent
agent = client.create_agent(
    name="Customer Support",
    llm_provider="openai",
    llm_model="gpt-4",
    stt_provider="deepgram",
    tts_provider="elevenlabs",
    prompt="You are a helpful customer support agent...",
    knowledge_base_id=kb.id
)

# Create workflow
workflow = client.create_workflow(
    name="Customer Support Flow",
    description="Handles customer support calls with routing"
)

# Add nodes
greeting_node = workflow.add_node(
    type="agent",
    data={"agent_id": agent.id, "prompt_override": "Welcome to..."}
)

router_node = workflow.add_node(
    type="condition",
    data={"condition_type": "intent", "conditions": [...]}
)

# Add edges
workflow.add_edge(source=greeting_node.id, target=router_node.id)

# Deploy
await client.deploy_agent(agent)
await client.deploy_workflow(workflow)

# Set up phone number
await client.map_phone_number(
    phone_number="+15551234567",
    workflow_id=workflow.id,
    trunk_id="twilio-trunk-id"
)
```

## Conclusion

This example demonstrates how to build a complete customer support voice agent using Knova AI. The platform's flexibility allows you to create sophisticated agents that can handle real customer interactions while leveraging your knowledge base for accurate information.

By following these steps, you can create similar agents for other use cases such as sales, appointment scheduling, or technical support.
