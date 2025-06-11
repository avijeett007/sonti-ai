"""Tests for Knova AI client"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from knova_ai import KnovaAI


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization"""
    with patch('knova_ai.client.LicenseValidator') as mock_validator:
        mock_validator.return_value.validate = AsyncMock(return_value=True)
        
        async with KnovaAI(license_key="test-key") as client:
            assert client.license_key == "test-key"
            assert client._license_valid is True
            

@pytest.mark.asyncio
async def test_create_agent():
    """Test agent creation"""
    with patch('knova_ai.client.LicenseValidator') as mock_validator:
        mock_validator.return_value.validate = AsyncMock(return_value=True)
        
        async with KnovaAI(license_key="test-key") as client:
            agent = client.create_agent(
                name="Test Agent",
                llm_provider="openai",
                llm_model="gpt-4"
            )
            
            assert agent.name == "Test Agent"
            assert agent.llm_provider == "openai"
            assert agent.llm_model == "gpt-4"
            

@pytest.mark.asyncio
async def test_create_workflow():
    """Test workflow creation"""
    with patch('knova_ai.client.LicenseValidator') as mock_validator:
        mock_validator.return_value.validate = AsyncMock(return_value=True)
        
        async with KnovaAI(license_key="test-key") as client:
            workflow = client.create_workflow(
                name="Test Workflow",
                description="A test workflow"
            )
            
            assert workflow.name == "Test Workflow"
            assert workflow.description == "A test workflow"