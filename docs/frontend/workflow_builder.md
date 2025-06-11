# Workflow Builder

## Overview

The Workflow Builder is a key component of the Knova AI frontend that allows users to create and manage complex voice AI workflows through an intuitive visual interface. It provides an infinite design pallet for drag-and-drop workflow creation with both simple and advanced interfaces.

## Architecture

The Workflow Builder is built on React Flow and integrates with the Knova AI backend through a REST API. It follows a component-based architecture with state management through React context and reducers.

### Key Components

```
┌─────────────────────────────────────────┐
│           Workflow Builder              │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐      ┌─────────────┐   │
│  │  Node       │      │  Edge       │   │
│  │  Library    │      │  Types      │   │
│  └─────────────┘      └─────────────┘   │
│         │                    │          │
│         ▼                    ▼          │
│  ┌─────────────┐      ┌─────────────┐   │
│  │  Flow       │      │ Properties  │   │
│  │  Canvas     │◄────►│  Panel      │   │
│  └─────────────┘      └─────────────┘   │
│         │                    │          │
│         └────────┬───────────┘          │
│                  │                      │
│                  ▼                      │
│  ┌─────────────────────────────────┐    │
│  │        Workflow Context          │    │
│  │  (State Management & API Calls)  │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

## Features

### Node Types

1. **Agent Nodes**
   - Voice agents with configurable LLM, STT, TTS providers
   - Text agents for chat-based interactions
   - Specialized agents (FAQ, Customer Support, etc.)

2. **Logic Nodes**
   - Conditions based on intents, keywords, or sentiment
   - Switches for branching workflows
   - Loops for repeated actions

3. **Data Nodes**
   - Knowledge Base connectors
   - Database queries
   - API integrations

4. **Utility Nodes**
   - Timers and schedulers
   - Notification senders
   - Call transfer handlers

### Edge Types

1. **Standard Edges**
   - Default flow between nodes

2. **Conditional Edges**
   - Based on specific conditions or outputs
   - With transition animations

3. **Timeout Edges**
   - Triggered after specific timeouts

## User Interface

### Simple Mode

Simple Mode provides a streamlined interface for creating basic workflows:

- Predefined templates for common scenarios
- Limited node types focused on essential functionality
- Guided creation experience with tooltips
- One-click deployment

### Advanced Mode

Advanced Mode unlocks the full potential of the Workflow Builder:

- Full node library with all available components
- Custom code nodes for advanced logic
- Direct JSON editing for workflow configuration
- Detailed property panel for fine-tuning

### Canvas Interactions

The infinite canvas supports:

- Pan and zoom navigation
- Multi-select and group operations
- Snap-to-grid for precise alignment
- Minimap for overview navigation
- Search functionality for large workflows

## Data Flow

### Saving Workflows

Workflows are saved as JSON through the backend API:

```javascript
const saveWorkflow = async () => {
  const nodes = reactFlowInstance.getNodes();
  const edges = reactFlowInstance.getEdges();
  
  await api.saveWorkflow({
    id: workflowId,
    name: workflowName,
    description: workflowDescription,
    nodes: nodes,
    edges: edges
  });
};
```

### Loading Workflows

Workflows are loaded from the backend and converted to React Flow format:

```javascript
const loadWorkflow = async (id) => {
  const workflow = await api.getWorkflow(id);
  
  setWorkflowName(workflow.name);
  setWorkflowDescription(workflow.description);
  
  reactFlowInstance.setNodes(workflow.nodes);
  reactFlowInstance.setEdges(workflow.edges);
};
```

### Testing Workflows

The Workflow Builder includes a testing panel that simulates workflow execution:

- Step-by-step execution visualization
- Test input configuration
- Execution logs and debugging information
- Performance metrics

## Mobile Support

The Workflow Builder is responsive and supports:

- Touch interactions for mobile devices
- Simplified interface for smaller screens
- Gesture-based navigation

## Integration Points

### Agent Configuration

Workflow Builder integrates with the agent configuration UI:

- Direct agent creation from workflow nodes
- Agent property editing within workflow context
- Reuse of existing agents across workflows

### Knowledge Base Integration

Workflows can leverage knowledge bases:

- Visual knowledge base selection
- Contextual search configuration
- Document relevance adjustments

### Telephony Integration

For voice workflows, SIP integration is available:

- Phone number assignment to workflow entry points
- Call transfer node configuration
- Voicemail and recording settings

## Example Workflows

### Simple IVR System

```json
{
  "nodes": [
    {
      "id": "greeting",
      "type": "agent",
      "data": {
        "name": "Greeting Agent",
        "prompt": "Welcome to our service. How can I help you today?"
      },
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "intent-router",
      "type": "condition",
      "data": {
        "name": "Intent Router",
        "conditions": [
          {"intent": "account_inquiry", "target": "account"},
          {"intent": "technical_support", "target": "support"},
          {"default": "fallback"}
        ]
      },
      "position": {"x": 300, "y": 100}
    },
    {
      "id": "account",
      "type": "agent",
      "data": {
        "name": "Account Agent",
        "prompt": "I can help with account questions."
      },
      "position": {"x": 200, "y": 300}
    },
    {
      "id": "support",
      "type": "agent",
      "data": {
        "name": "Support Agent",
        "prompt": "I can help with technical issues."
      },
      "position": {"x": 400, "y": 300}
    },
    {
      "id": "fallback",
      "type": "agent",
      "data": {
        "name": "Fallback Agent",
        "prompt": "I'm not sure how to help with that."
      },
      "position": {"x": 600, "y": 300}
    }
  ],
  "edges": [
    {"source": "greeting", "target": "intent-router"},
    {"source": "intent-router", "target": "account", "condition": "account_inquiry"},
    {"source": "intent-router", "target": "support", "condition": "technical_support"},
    {"source": "intent-router", "target": "fallback", "condition": "default"}
  ]
}
```

## Best Practices

1. **Workflow Organization**
   - Use clear naming conventions
   - Group related nodes together
   - Add comments for complex logic

2. **Error Handling**
   - Always add fallback paths
   - Use timeout edges for non-responsive paths
   - Include error handling nodes

3. **Performance**
   - Avoid deeply nested conditions
   - Reuse agents when appropriate
   - Split complex workflows into subflows

4. **Testing**
   - Test all possible paths
   - Verify error handling works as expected
   - Test with realistic input scenarios

## Keyboard Shortcuts

The Workflow Builder supports various keyboard shortcuts:

- `Ctrl+S` / `⌘+S`: Save workflow
- `Ctrl+Z` / `⌘+Z`: Undo
- `Ctrl+Shift+Z` / `⌘+Shift+Z`: Redo
- `Delete`: Remove selected elements
- `F`: Fit view to visible elements
- `C`: Toggle connection mode
