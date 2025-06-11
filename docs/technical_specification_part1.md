# Knova AI: Technical Specification

## 1. Introduction

This technical specification outlines the implementation details for Knova AI, an open source Voice AI Agent platform built on LiveKit. The document covers the system architecture, component interactions, data models, APIs, and deployment strategies.

## 2. System Components

### 2.1 Frontend Application (Next.js)

#### 2.1.1 Technology Stack
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **UI Library**: React with Tailwind CSS
- **State Management**: React Context API + SWR for data fetching
- **Authentication**: Supabase Auth
- **Real-time Communication**: LiveKit Client SDK

#### 2.1.2 Key Components
- **Authentication Module**: Handles user registration, login, and session management
- **Agent Builder**: UI for creating and configuring voice AI agents
- **Knowledge Base Manager**: Interface for uploading and managing knowledge sources
- **Function Registry**: UI for configuring and testing function calls
- **Agent Testing Interface**: Real-time testing environment for agents
- **Dashboard**: Monitoring and analytics for deployed agents

#### 2.1.3 Pages Structure
```
/app
  /auth
    /login
    /register
    /forgot-password
  /dashboard
  /agents
    /[agent_id]
      /edit
      /test
      /analytics
  /knowledge-base
  /functions
  /settings
```

### 2.2 Backend Services

#### 2.2.1 Next.js API Routes
- **Authentication API**: User management endpoints
- **Agent API**: CRUD operations for agents
- **Knowledge Base API**: Document management endpoints
- **Function Registry API**: Function configuration endpoints
- **Analytics API**: Usage and performance data endpoints

#### 2.2.2 Dedicated Services
- **Agent Deployment Service**: Manages agent container lifecycle
- **LiveKit Integration Service**: Handles room creation and token generation
- **Analytics Processing Service**: Aggregates and processes usage data

#### 2.2.3 Database Schema (Supabase)
- **Users Table**: User accounts and profiles
- **Agents Table**: Agent configurations and metadata
- **Knowledge Bases Table**: Knowledge base configurations
- **Documents Table**: Uploaded documents and their metadata
- **Functions Table**: Function definitions and configurations
- **Sessions Table**: Call/conversation session data
- **Analytics Table**: Usage and performance metrics
