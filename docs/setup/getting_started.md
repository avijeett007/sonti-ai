# Getting Started with Knova AI

This guide will walk you through setting up the Knova AI platform for local development and production use.

## Prerequisites

- Node.js 18+
- Python 3.10+
- Docker and Docker Compose
- Git
- (Optional) Kubernetes for production deployment

## Step 1: Get Your License Key

Before installing Knova AI, you need to obtain a free license key:

1. Go to [Knova AI website](https://www.knova.ai/register)
2. Create an account or log in
3. Navigate to the "License Keys" section
4. Generate a new license key for your project
5. Keep this key safe as you'll need it during setup

## Step 2: Clone the Repository

```bash
git clone https://github.com/yourusername/knova-ai.git
cd knova-ai
```

## Step 3: Install Dependencies

### Install the Knova AI SDK

The Knova AI SDK is available as a separate PyPI package:

```bash
pip install knova-ai-sdk
```

### Set Up the Project

Run the setup script which will install all required dependencies:

```bash
./scripts/setup.sh
```

## Step 4: Configure Environment Variables

1. Copy the example environment files:

```bash
cp .env.example .env
cp agent/.env.example agent/.env
```

2. Edit the `.env` and `agent/.env` files to add your license key and other configuration options

### Required Configuration Variables

| Variable | Description |
|----------|-------------|
| `KNOVA_LICENSE_KEY` | Your Knova AI license key |
| `DATABASE_URL` | Database connection URL |
| `LIVEKIT_API_KEY` | Your LiveKit API key |
| `LIVEKIT_API_SECRET` | Your LiveKit API secret |
| `LIVEKIT_URL` | URL of your LiveKit server |

## Step 5: Set Up the Database

Choose one of the supported database options:

### SQLite (Simplest for Development)

```bash
# SQLite is configured by default
# Just run the migration script
./scripts/db-migrate.sh
```

### PostgreSQL / NeonDB / Supabase

1. Create a PostgreSQL database
2. Update `DATABASE_URL` in your `.env` files
3. Run migrations:

```bash
./scripts/db-migrate.sh
```

## Step 6: Start the Application

### Development Mode

```bash
# Run all components with Docker Compose
docker-compose up

# Or run components separately

# Backend API
cd backend
npm run dev

# Frontend
cd frontend
npm run dev

# Agent Layer
cd agent
python src/main.py
```

### Production Mode

```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or using Kubernetes
kubectl apply -f kubernetes/
```

## Step 7: Access the Application

Once everything is running:

1. Open your browser and go to `http://localhost:3000`
2. Log in with your credentials
3. Enter your license key in the settings page if not already configured
4. Start creating your first agent!

## Next Steps

- [Configure your first agent](../examples/first_agent.md)
- [Set up a knowledge base](../examples/knowledge_base.md)
- [Create your first workflow](../examples/workflow.md)
- [Set up telephony integration](../examples/sip_integration.md)

## Troubleshooting

If you encounter any issues during setup:

1. Check that your license key is valid and properly configured
2. Ensure all services are running (check Docker or process status)
3. Verify database connection and migrations
4. Check the logs for each component for specific errors
5. See our [troubleshooting guide](troubleshooting.md) for common issues
