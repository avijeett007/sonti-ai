#!/bin/bash

# Knova AI Setup Script

set -e

echo "🚀 Setting up Knova AI development environment..."

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ All prerequisites met!"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your configuration"
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install Python SDK dependencies
echo "Installing Python SDK dependencies..."
cd knova-ai-sdk
pip install -e ".[dev]"
cd ..

# Install agent dependencies
echo "Installing agent dependencies..."
cd agent
pip install -r requirements.txt
cd ..

# Start infrastructure with Docker Compose
echo "Starting infrastructure services..."
cd infrastructure
docker-compose up -d postgres redis livekit qdrant

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "Running database migrations..."
docker-compose exec -T postgres psql -U knova -d knova < ../backend/schema.sql

echo "✅ Setup complete!"
echo ""
echo "To start the development environment:"
echo "  1. Start frontend: cd frontend && npm run dev"
echo "  2. Start agent worker: cd agent && python src/main.py"
echo "  3. Or use Docker Compose: cd infrastructure && docker-compose up"
echo ""
echo "Access the application at http://localhost:3000"