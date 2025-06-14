# License Management Guide

This guide covers the comprehensive license validation and management system in the Knova AI SDK.

## Overview

The Knova AI SDK implements a robust license validation system that provides:
- License key format validation with checksums
- Tier-based feature restrictions
- Usage tracking and limits
- Offline operation with grace periods
- Background validation for non-free tiers
- Comprehensive caching and retry mechanisms

## License Key Format

License keys follow a specific format:
```
KNOVA-{TIER}-{UUID}-{CHECKSUM}
```

Example:
```
KNOVA-PRO-550e8400-e29b-41d4-a716-446655440000-a1b2c3d4
```

Components:
- **TIER**: FREE, PRO, or ENTERPRISE
- **UUID**: Unique identifier for the license
- **CHECKSUM**: 8-character SHA256 checksum for validation

## License Tiers and Features

### FREE Tier
- Up to 3 agents
- 1,000 API calls per day
- 100MB storage
- 60 voice minutes per month
- 1 knowledge base with 10 documents
- Basic features only

### PRO Tier
- Up to 10 agents
- 10,000 API calls per day
- 1GB storage
- 1,000 voice minutes per month
- 5 knowledge bases with 100 documents each
- Custom functions
- Multi-agent collaboration
- Analytics access

### ENTERPRISE Tier
- Unlimited agents
- Unlimited API calls
- Unlimited storage
- Unlimited voice minutes
- Unlimited knowledge bases
- All PRO features
- Priority support
- Custom deployment options

## Using the SDK with License Validation

### Basic Usage

```python
from knova_ai import KnovaAI

# Initialize with your license key
client = KnovaAI(license_key="KNOVA-PRO-xxx-xxx")

# Initialize the client (validates license)
await client.initialize()

# Check license information
license_info = client.get_license_info()
print(f"License Tier: {license_info.tier}")
print(f"Valid Until: {license_info.expires_at}")

# Check feature availability
if client.check_feature_available(Feature.MULTI_AGENT_COLLABORATION):
    workflow = client.create_workflow("My Workflow")
else:
    print("Multi-agent workflows not available in your tier")
```

### Checking Usage Limits

```python
# Get current usage
usage = client.get_current_usage()
print(f"Agents created: {usage.get('create_agent', 0)}")
print(f"API calls today: {usage.get('api_calls', 0)}")

# Get usage limits for your tier
limits = client.get_usage_limits()
print(f"Max agents: {limits['max_agents']}")
print(f"Max API calls/day: {limits['max_api_calls_per_day']}")

# Get detailed usage summary
summary = await client.get_usage_summary(period_days=30)
print(f"Total API calls: {summary['api_calls']['total']}")
print(f"Average response time: {summary['api_calls']['avg_response_time_ms']}ms")
```

### License Validation Details

```python
# Check cache status
cache_status = client.get_cache_status()
print(f"Cache valid: {cache_status['cache_valid']}")
print(f"Days since validation: {cache_status.get('days_since_validation', 0)}")
print(f"Grace period active: {cache_status['grace_period_active']}")

# Force immediate validation
try:
    await client.force_license_validation()
    print("License validated successfully")
except ValueError as e:
    print(f"Validation failed: {e}")

# Get validation history
history = client.get_validation_history(limit=10)
for attempt in history:
    print(f"{attempt['timestamp']}: {attempt['success']} - {attempt['reason']}")
```

## Offline Operation

The SDK supports offline operation with extended grace periods:

1. **30-day cache validity**: License information is cached for up to 30 days
2. **7-day grace period**: After cache expiration, a 7-day grace period allows continued operation
3. **Automatic retry**: Failed validations are retried with exponential backoff

### Offline Behavior by Tier

- **FREE tier**: Validates every 24 hours, works offline with cached license
- **PRO tier**: Validates every 6 hours, background validation when online
- **ENTERPRISE tier**: Validates every 12 hours, background validation when online

## Background Validation

For PRO and ENTERPRISE tiers, the SDK performs background validation:

```python
# Background validation starts automatically for non-free tiers
# You can set a callback to be notified of validation results

def validation_callback(is_valid: bool, license_info: LicenseInfo):
    if not is_valid:
        print("License validation failed!")
    elif license_info.expires_at:
        days_left = (license_info.expires_at - datetime.now()).days
        if days_left < 30:
            print(f"License expires in {days_left} days")

# Set the callback (optional)
client.background_validator.set_validation_callback(validation_callback)
```

## Error Handling

The SDK provides clear error messages for license-related issues:

```python
try:
    # This might fail if you exceed your agent limit
    agent = client.create_agent("My Agent")
except ValueError as e:
    if "Usage limit exceeded" in str(e):
        print(f"Error: {e}")
        # Check current usage vs limits
        usage = client.get_current_usage()
        limits = client.get_usage_limits()
        print(f"Current agents: {usage.get('create_agent', 0)}/{limits['max_agents']}")
```

## License Expiration Warnings

The SDK automatically warns about upcoming license expiration:
- 30 days before expiration
- 7 days before expiration
- 1 day before expiration

These warnings appear in the logs and can be captured via the validation callback.

## Security

- License keys are encrypted when stored locally
- Checksums prevent tampering with license keys
- API communication uses TLS 1.3
- Local storage uses AES-256 encryption

## Troubleshooting

### Common Issues

1. **"Invalid license format"**
   - Ensure your license key follows the correct format
   - Check for extra spaces or characters

2. **"Usage limit exceeded"**
   - Check your current usage with `get_current_usage()`
   - Upgrade to a higher tier if needed

3. **"License validation failed"**
   - Check your internet connection
   - Verify the license key is correct
   - Check if you're within the grace period

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed validation attempts
client = KnovaAI(license_key="your-key")
await client.initialize()
```

## Best Practices

1. **Initialize once**: Create the client once and reuse it
2. **Handle errors gracefully**: Always catch ValueError for license issues
3. **Monitor usage**: Regularly check usage to avoid hitting limits
4. **Plan for offline**: Test your application's offline behavior
5. **Update regularly**: Keep the SDK updated for the latest features

## Migration from Older Versions

If upgrading from an older SDK version without license validation:

1. Obtain a license key from the Knova AI portal
2. Update your initialization code to include the license key
3. Test thoroughly, especially error handling for license limits
4. Review feature availability for your tier

## API Reference

### License-related Methods

- `get_license_info()`: Get current license information
- `get_license_tier()`: Get license tier (FREE, PRO, ENTERPRISE)
- `get_usage_limits()`: Get usage limits for current tier
- `get_current_usage()`: Get current usage statistics
- `get_usage_summary(period_days)`: Get detailed usage summary
- `check_feature_available(feature)`: Check if feature is available
- `get_cache_status()`: Get license cache status
- `force_license_validation()`: Force immediate validation
- `get_validation_history(limit)`: Get validation history

### Feature Enum

```python
from knova_ai import Feature

# Available features to check
Feature.CREATE_AGENT
Feature.DELETE_AGENT
Feature.UPDATE_AGENT
Feature.DEPLOY_AGENT
Feature.CREATE_KNOWLEDGE_BASE
Feature.UPLOAD_DOCUMENT
Feature.API_CALLS
Feature.WEBHOOK_CALLS
Feature.VOICE_MINUTES
Feature.TRANSCRIPTION
Feature.CUSTOM_FUNCTIONS
Feature.MULTI_AGENT_COLLABORATION
Feature.ANALYTICS_ACCESS
Feature.PRIORITY_SUPPORT
```