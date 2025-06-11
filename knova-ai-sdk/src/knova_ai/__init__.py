"""Knova AI SDK - Open-source Voice AI Agent platform"""

from .client import KnovaAI
from .agents.base import Agent as BaseAgent
from .agents.voice import VoiceAgent
from .agents.workflow import WorkflowAgent
from .db import (
    BaseEntity, BaseConnector,
    SQLiteConnector, PostgreSQLConnector, SupabaseConnector, NeonDBConnector,
    get_connector,
    User, ApiKey, Agent, Workflow, KnowledgeBase, Document,
    SipTrunk, PhoneNumber, Webhook, CallLog, UsageLog
)
from .db.migrations import MigrationManager

__version__ = "0.1.0"
__all__ = [
    # Client
    "KnovaAI", 
    
    # Agents
    "BaseAgent",
    "VoiceAgent", 
    "WorkflowAgent",
    
    # Database
    "BaseEntity",
    "BaseConnector",
    "SQLiteConnector",
    "PostgreSQLConnector", 
    "SupabaseConnector",
    "NeonDBConnector",
    "get_connector",
    
    # Entities
    "User",
    "ApiKey",
    "Agent",
    "Workflow",
    "KnowledgeBase",
    "Document",
    "SipTrunk",
    "PhoneNumber",
    "Webhook",
    "CallLog",
    "UsageLog",
    
    # Migrations
    "MigrationManager"
]