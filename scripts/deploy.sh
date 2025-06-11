#!/bin/bash

# Knova AI Deployment Script

set -e

echo "🚀 Deploying Knova AI..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Build Docker images
echo "Building Docker images..."
docker build -t knova-ai/frontend:latest ./frontend
docker build -t knova-ai/agent:latest ./agent

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f infrastructure/k8s/namespace.yaml
kubectl apply -f infrastructure/k8s/postgres.yaml
kubectl apply -f infrastructure/k8s/redis.yaml
kubectl apply -f infrastructure/k8s/livekit.yaml
kubectl apply -f infrastructure/k8s/qdrant.yaml
kubectl apply -f infrastructure/k8s/agent-deployment.yaml
kubectl apply -f infrastructure/k8s/frontend-deployment.yaml

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n knova-ai

# Get frontend URL
FRONTEND_URL=$(kubectl get service frontend -n knova-ai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "✅ Deployment complete!"
echo "Access the application at http://${FRONTEND_URL}:3000"