-- Migration: Add workflows, webhooks, and license management tables
-- Version: 003
-- Description: Support for workflow builder, webhook integrations, and license key management

-- Workflows table for storing multi-agent workflow definitions
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL, -- Stores nodes and edges configuration
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_definition CHECK (
        definition ? 'nodes' AND 
        definition ? 'edges' AND
        jsonb_typeof(definition->'nodes') = 'array' AND
        jsonb_typeof(definition->'edges') = 'array'
    )
);

-- Index for user queries
CREATE INDEX idx_workflows_user_id ON workflows(user_id);
CREATE INDEX idx_workflows_is_active ON workflows(is_active);

-- Workflow deployments tracking
CREATE TABLE IF NOT EXISTS workflow_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    deployment_id VARCHAR(255) UNIQUE NOT NULL,
    environment VARCHAR(50) NOT NULL DEFAULT 'production',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT valid_environment CHECK (environment IN ('development', 'staging', 'production')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'deploying', 'active', 'failed', 'stopped'))
);

CREATE INDEX idx_workflow_deployments_workflow_id ON workflow_deployments(workflow_id);
CREATE INDEX idx_workflow_deployments_status ON workflow_deployments(status);

-- Webhooks configuration table
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    url VARCHAR(512) NOT NULL,
    events TEXT[] NOT NULL DEFAULT '{}',
    headers JSONB DEFAULT '{}',
    retry_config JSONB DEFAULT '{"max_attempts": 3, "backoff_seconds": [1, 5, 30]}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT webhook_target CHECK (
        (agent_id IS NOT NULL AND workflow_id IS NULL) OR 
        (agent_id IS NULL AND workflow_id IS NOT NULL)
    ),
    CONSTRAINT valid_url CHECK (url ~ '^https?://')
);

CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX idx_webhooks_agent_id ON webhooks(agent_id);
CREATE INDEX idx_webhooks_workflow_id ON webhooks(workflow_id);
CREATE INDEX idx_webhooks_is_active ON webhooks(is_active);

-- Webhook delivery logs
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    attempt_count INTEGER DEFAULT 1,
    delivered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    success BOOLEAN DEFAULT false
);

CREATE INDEX idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_success ON webhook_deliveries(success);
CREATE INDEX idx_webhook_deliveries_next_retry ON webhook_deliveries(next_retry_at) WHERE next_retry_at IS NOT NULL;

-- License keys table
CREATE TABLE IF NOT EXISTS license_keys (
    key VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    quota_limits JSONB DEFAULT '{"agents": 5, "calls_per_month": 1000, "knowledge_base_size_mb": 100}',
    usage_stats JSONB DEFAULT '{"agents_created": 0, "calls_this_month": 0, "storage_used_mb": 0}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_tier CHECK (tier IN ('free', 'starter', 'professional', 'enterprise')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'suspended', 'expired', 'revoked'))
);

CREATE INDEX idx_license_keys_user_id ON license_keys(user_id);
CREATE INDEX idx_license_keys_status ON license_keys(status);
CREATE INDEX idx_license_keys_tier ON license_keys(tier);

-- License usage tracking
CREATE TABLE IF NOT EXISTS license_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key VARCHAR(255) NOT NULL REFERENCES license_keys(key) ON DELETE CASCADE,
    usage_type VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_license_usage_key ON license_usage(license_key);
CREATE INDEX idx_license_usage_type ON license_usage(usage_type);
CREATE INDEX idx_license_usage_recorded_at ON license_usage(recorded_at);

-- Telemetry data collection
CREATE TABLE IF NOT EXISTS telemetry_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key VARCHAR(255) REFERENCES license_keys(key) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    sdk_version VARCHAR(50),
    python_version VARCHAR(50),
    platform VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetry_license_key ON telemetry_events(license_key);
CREATE INDEX idx_telemetry_event_type ON telemetry_events(event_type);
CREATE INDEX idx_telemetry_created_at ON telemetry_events(created_at);

-- Update agents table to include webhook reference
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS webhook_id UUID REFERENCES webhooks(id) ON DELETE SET NULL;

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_license_keys_updated_at BEFORE UPDATE ON license_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to check license quota
CREATE OR REPLACE FUNCTION check_license_quota(p_license_key VARCHAR, p_usage_type VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_quota_limits JSONB;
    v_usage_stats JSONB;
    v_limit INTEGER;
    v_used INTEGER;
BEGIN
    SELECT quota_limits, usage_stats INTO v_quota_limits, v_usage_stats
    FROM license_keys
    WHERE key = p_license_key AND status = 'active';
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check specific quota based on usage type
    CASE p_usage_type
        WHEN 'agents' THEN
            v_limit := (v_quota_limits->>'agents')::INTEGER;
            v_used := (v_usage_stats->>'agents_created')::INTEGER;
        WHEN 'calls' THEN
            v_limit := (v_quota_limits->>'calls_per_month')::INTEGER;
            v_used := (v_usage_stats->>'calls_this_month')::INTEGER;
        WHEN 'storage' THEN
            v_limit := (v_quota_limits->>'knowledge_base_size_mb')::INTEGER;
            v_used := (v_usage_stats->>'storage_used_mb')::INTEGER;
        ELSE
            RETURN TRUE; -- Unknown usage type, allow by default
    END CASE;
    
    RETURN v_used < v_limit;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security policies
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE license_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE license_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry_events ENABLE ROW LEVEL SECURITY;

-- Workflows policies
CREATE POLICY "Users can view own workflows" ON workflows
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own workflows" ON workflows
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workflows" ON workflows
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workflows" ON workflows
    FOR DELETE USING (auth.uid() = user_id);

-- Webhooks policies
CREATE POLICY "Users can view own webhooks" ON webhooks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own webhooks" ON webhooks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own webhooks" ON webhooks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own webhooks" ON webhooks
    FOR DELETE USING (auth.uid() = user_id);

-- License keys policies
CREATE POLICY "Users can view own license keys" ON license_keys
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage license keys" ON license_keys
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Comments for documentation
COMMENT ON TABLE workflows IS 'Stores multi-agent workflow definitions created in the workflow builder';
COMMENT ON TABLE webhooks IS 'Webhook configurations for agent and workflow events';
COMMENT ON TABLE license_keys IS 'License key management for SDK usage and quotas';
COMMENT ON TABLE telemetry_events IS 'Anonymous telemetry data from SDK usage';