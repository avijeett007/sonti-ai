# Production Deployment Guide

## Overview

This guide describes how to deploy the Knova AI platform in a production environment. The platform is designed to be deployed using Docker containers and Kubernetes for orchestration, with support for various database backends and cloud providers.

## Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-managed)
- Docker registry access
- Domain name with DNS configuration
- SSL certificates for secure communication
- Valid Knova AI license key
- Database service (PostgreSQL, Supabase, or NeonDB)
- LiveKit account or self-hosted LiveKit server

## Architecture Diagram

```
                           ┌─────────────────┐
                           │   Ingress       │
                           │  Controller     │
                           └────────┬────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
        ┌───────▼──────┐    ┌──────▼───────┐   ┌───────▼──────┐
        │   Frontend    │    │    Backend   │   │   Agent     │
        │   Service     │    │    Service   │   │   Service   │
        └───────┬───────┘    └──────┬───────┘   └───────┬──────┘
                │                   │                   │
        ┌───────▼──────┐    ┌──────▼───────┐   ┌───────▼──────┐
        │   Frontend    │    │    Backend   │   │   Agent     │
        │   Pod(s)      │    │    Pod(s)    │   │   Pod(s)    │
        └───────────────┘    └──────┬───────┘   └───────┬──────┘
                                    │                   │
                                    │                   │
                           ┌────────▼───────┐   ┌───────▼──────┐
                           │    Database    │   │   LiveKit    │
                           │    Service     │◄──┤   Server     │
                           └────────────────┘   └──────────────┘
```

## Deployment Steps

### 1. Prepare Environment Variables

Create Kubernetes secrets for sensitive information:

```bash
kubectl create namespace knova

# Create secrets
kubectl create secret generic knova-secrets \
  --namespace knova \
  --from-literal=KNOVA_LICENSE_KEY="your-license-key" \
  --from-literal=LIVEKIT_API_KEY="your-livekit-api-key" \
  --from-literal=LIVEKIT_API_SECRET="your-livekit-api-secret" \
  --from-literal=DATABASE_URL="postgresql://user:password@db-host:5432/knova" \
  --from-literal=JWT_SECRET="random-secure-jwt-secret"
```

### 2. Database Setup

If you're using a managed database service (recommended for production), ensure your database is properly set up and secured:

1. Create a database instance with your chosen provider
2. Configure network security to allow connections from your Kubernetes cluster
3. Create necessary database user with appropriate permissions
4. Run migrations:

```bash
# Apply database migrations
kubectl create job --namespace knova knova-migrations \
  --from=cronjob/knova-migrations
```

### 3. Deploy Core Components

Apply the Kubernetes manifests:

```bash
# Apply all manifests
kubectl apply -f kubernetes/production/

# Verify deployments
kubectl get pods --namespace knova
```

### 4. Configure Ingress

Set up an ingress controller to expose the services:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: knova-ingress
  namespace: knova
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - knova.yourdomain.com
    secretName: knova-tls
  rules:
  - host: knova.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: knova-backend
            port:
              number: 8000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: knova-backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: knova-frontend
            port:
              number: 3000
```

### 5. SIP Integration

For production telephony integration, configure your SIP provider (Twilio, Telnyx, or Plivo) to point to your LiveKit server:

1. Set up SIP trunk with your provider
2. Configure webhook URLs to point to your Knova API endpoint:
   ```
   https://knova.yourdomain.com/api/v1/webhooks/sip/inbound
   ```
3. Set up phone numbers and map them to your agents through the Knova UI

### 6. Scaling Configuration

Configure autoscaling for production workloads:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: knova-agent-hpa
  namespace: knova
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: knova-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 7. Monitoring Setup

Deploy monitoring tools:

```bash
# Install Prometheus and Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Apply Knova-specific monitoring configuration
kubectl apply -f kubernetes/monitoring/
```

### 8. Backup Configuration

Set up regular backups for the database:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: knova-db-backup
  namespace: knova
spec:
  schedule: "0 2 * * *"  # Every day at 2:00 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:14
            command: ["/bin/sh", "-c"]
            args:
            - |
              pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -f /backups/knova-$(date +%Y-%m-%d).dump
              aws s3 cp /backups/knova-$(date +%Y-%m-%d).dump s3://your-backup-bucket/
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: knova-secrets
                  key: DB_PASSWORD
            - name: DB_HOST
              value: "your-db-host"
            - name: DB_USER
              value: "knova"
            - name: DB_NAME
              value: "knova"
          restartPolicy: OnFailure
```

## Production Considerations

### High Availability

For production deployments, ensure high availability by:

1. Deploying multiple replicas of each component
2. Using pod anti-affinity to spread across nodes
3. Configuring proper health checks and readiness probes
4. Using a highly available database configuration

### Security

Enhance security for production:

1. Enable Network Policies to restrict pod-to-pod communication
2. Use Pod Security Policies (or their replacement) to enforce security contexts
3. Regularly update container images to patch security vulnerabilities
4. Use RBAC to restrict access to Kubernetes resources
5. Encrypt sensitive data using Kubernetes Secrets and/or external secret management solutions

### Performance Tuning

Optimize performance:

1. Adjust resource requests and limits based on observed usage
2. Configure database connection pooling
3. Set up caching for frequently accessed data
4. Use CDN for static frontend assets

### Disaster Recovery

Prepare for disaster recovery:

1. Regular database backups
2. Configuration backups
3. Documented restore procedures
4. Regular recovery testing

## Updating the Platform

To update the Knova AI platform:

1. Pull the latest Docker images
2. Update manifests if needed
3. Apply a rolling update:

```bash
# Update image tag
kubectl set image deployment/knova-frontend \
  knova-frontend=knova/frontend:new-version --namespace knova

kubectl set image deployment/knova-backend \
  knova-backend=knova/backend:new-version --namespace knova

kubectl set image deployment/knova-agent \
  knova-agent=knova/agent:new-version --namespace knova
```

## Troubleshooting

### Common Issues

1. **Database Connection Failures**
   - Check network policies
   - Verify connection string and credentials
   - Ensure database service is running

2. **License Validation Errors**
   - Verify license key in the secrets
   - Check network connectivity to license validation service
   - Check logs for specific validation errors

3. **LiveKit Connection Issues**
   - Verify API key and secret
   - Check network connectivity to LiveKit server
   - Review LiveKit server logs

### Log Collection

Centralize logs for troubleshooting:

```bash
# Install Elasticsearch, Fluentd, and Kibana (EFK stack)
helm install efk elastic/eck-operator --namespace logging --create-namespace

# Apply Knova logging configuration
kubectl apply -f kubernetes/logging/
```

### Support Access

For enterprise customers, enable secure support access:

```bash
# Install support access tool
kubectl apply -f kubernetes/support/support-access.yaml
```
