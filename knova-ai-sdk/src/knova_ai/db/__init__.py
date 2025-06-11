"""Database module for Knova AI SDK.

This module provides database integration for the Knova AI platform,
supporting multiple database backends including SQLite, PostgreSQL,
Supabase, and NeonDB.
"""

from .base import BaseEntity, BaseConnector
from .connectors import (
    SQLiteConnector,
    PostgreSQLConnector,
    SupabaseConnector,
    NeonDBConnector,
    get_connector
)
from .entities import (
    User,
    ApiKey,
    Agent,
    Workflow,
    KnowledgeBase,
    Document,
    SipTrunk,
    PhoneNumber,
    Webhook,
    CallLog,
    UsageLog
)

__all__ = [
    # Base classes
    'BaseEntity',
    'BaseConnector',
    
    # Connectors
    'SQLiteConnector',
    'PostgreSQLConnector',
    'SupabaseConnector',
    'NeonDBConnector',
    'get_connector',
    
    # Entities
    'User',
    'ApiKey',
    'Agent',
    'Workflow',
    'KnowledgeBase',
    'Document',
    'SipTrunk',
    'PhoneNumber',
    'Webhook',
    'CallLog',
    'UsageLog'
]