#!/bin/bash

# Knova AI Test Script

set -e

echo "🧪 Running Knova AI tests..."

# Run Python SDK tests
echo "Running Python SDK tests..."
cd knova-ai-sdk
pytest tests/ -v --cov=src/knova_ai
cd ..

# Run frontend tests
echo "Running frontend tests..."
cd frontend
npm run lint
npm run type-check
npm test
cd ..

# Run agent tests
echo "Running agent tests..."
cd agent
pytest tests/ -v
cd ..

echo "✅ All tests passed!"