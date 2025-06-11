"""Tests for agent implementations"""

import pytest
from unittest.mock import MagicMock

from knova_ai.agents.voice import VoiceAgent
from knova_ai.agents.workflow import WorkflowAgent


def test_voice_agent_creation():
    """Test voice agent creation"""
    mock_client = MagicMock()
    
    config = {
        "name": "Test Voice Agent",
        "llm_provider": "openai",
        "llm_model": "gpt-4",
        "stt_provider": "deepgram",
        "tts_provider": "elevenlabs"
    }
    
    agent = VoiceAgent(mock_client, config)
    
    assert agent.name == "Test Voice Agent"
    assert agent.llm_provider == "openai"
    assert agent.llm_model == "gpt-4"
    assert agent.stt_provider == "deepgram"
    assert agent.tts_provider == "elevenlabs"
    

def test_voice_agent_deployment_config():
    """Test voice agent deployment configuration"""
    mock_client = MagicMock()
    
    config = {
        "name": "Test Agent",
        "llm_provider": "openai",
        "llm_model": "gpt-4"
    }
    
    agent = VoiceAgent(mock_client, config)
    deployment_config = agent.to_deployment_config()
    
    assert deployment_config["name"] == "Test Agent"
    assert deployment_config["type"] == "voice"
    assert deployment_config["llm"]["provider"] == "openai"
    assert deployment_config["llm"]["model"] == "gpt-4"
    

def test_workflow_agent_creation():
    """Test workflow agent creation"""
    mock_client = MagicMock()
    
    config = {
        "name": "Test Workflow",
        "description": "A test workflow"
    }
    
    workflow = WorkflowAgent(mock_client, config)
    
    assert workflow.name == "Test Workflow"
    assert workflow.description == "A test workflow"
    assert len(workflow.nodes) == 0
    assert len(workflow.edges) == 0
    

def test_workflow_add_nodes():
    """Test adding nodes to workflow"""
    mock_client = MagicMock()
    
    workflow = WorkflowAgent(mock_client, {"name": "Test"})
    
    # Create a voice agent
    agent = VoiceAgent(mock_client, {"name": "Agent1"})
    
    # Add agent node
    node_id = workflow.add_agent_node(agent)
    assert len(workflow.nodes) == 1
    assert workflow.nodes[0].type == "agent"
    
    # Add condition node
    cond_id = workflow.add_condition_node("Check Intent", "keyword", "support")
    assert len(workflow.nodes) == 2
    assert workflow.nodes[1].type == "condition"
    
    # Connect nodes
    workflow.connect_nodes(node_id, cond_id)
    assert len(workflow.edges) == 1
    

def test_workflow_validation():
    """Test workflow validation"""
    mock_client = MagicMock()
    
    workflow = WorkflowAgent(mock_client, {"name": "Test"})
    
    # Empty workflow should fail
    valid, error = workflow.validate()
    assert valid is False
    assert "No start node" in error
    
    # Add nodes
    agent = VoiceAgent(mock_client, {"name": "Agent1"})
    node1 = workflow.add_agent_node(agent)
    node2 = workflow.add_condition_node("Check", "keyword", "test")
    
    # Connect nodes
    workflow.connect_nodes(node1, node2)
    
    # Should be valid now
    valid, error = workflow.validate()
    assert valid is True
    assert error is None