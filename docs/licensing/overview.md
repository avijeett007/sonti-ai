# Licensing System Overview

## License Model

Knova AI uses a freemium licensing model:

- **Free Tier**: Available for individual developers and small organizations
- **Pro Tier**: (Future) Enhanced features for enterprise customers

All users require a license key to activate the platform, even for the free tier. This ensures proper tracking, support, and enables a smooth upgrade path.

## License Key Flow

1. **User Registration**
   - Users sign up on the Knova AI website
   - Email verification is completed
   - License key is automatically generated for the free tier

2. **Key Installation**
   - User installs Knova AI platform
   - During setup, the license key is added to configuration files
   - Both frontend/backend and agent layers require the same key

3. **Validation Process**
   - Upon startup, the license key is validated with the Knova AI API service
   - Validation results are cached for offline operation
   - Periodic revalidation occurs in the background

4. **License Enforcement**
   - Free tier has generous usage limits
   - License validation failures result in graceful degradation
   - Users are notified when approaching limits

## License Key Format

Knova AI license keys follow this format:

```
KNOVA-{tier}-{uuid}-{checksum}
```

For example:
```
KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-A7F4E
```

## SDK License Integration

The Knova AI SDK manages license validation:

```python
from knova_ai import KnovaAI

# Initialize with license key
knova = KnovaAI(license_key="KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-A7F4E")

# Check license status
license_info = await knova.get_license_info()
print(f"License tier: {license_info.tier}")
print(f"License valid: {license_info.valid}")
print(f"Expires on: {license_info.expires_at}")
```

## License Validation API

The license validation API is accessible at:
```
https://api.knova.ai/v1/license/validate
```

This endpoint accepts a POST request with the license key and returns validation information.

## License Storage

The license key is stored in:

1. **Frontend/Backend**: `.env` file or environment variable
   ```
   KNOVA_LICENSE_KEY=KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-A7F4E
   ```

2. **Agent Layer**: `.env` file or environment variable
   ```
   KNOVA_LICENSE_KEY=KNOVA-FREE-550e8400-e29b-41d4-a716-446655440000-A7F4E
   ```

3. **Database**: A reference to the active license is stored for tracking

## Offline Operation

For environments with limited internet access:

1. **Initial Validation**: Required at setup time
2. **Cached Validation**: Results are cached for 30 days
3. **Grace Period**: 7 additional days after cache expiration

## License Management UI

The platform includes a license management interface:

1. **Key Display**: View current license details
2. **Usage Metrics**: Track usage against license limits
3. **Upgrade Options**: Paths to upgrade to Pro tier (future)

## Troubleshooting

Common license issues:

1. **Invalid License**: Key format is incorrect or key has been tampered with
2. **Expired License**: The time-limited license has expired
3. **Connection Issues**: Unable to validate due to network/firewall issues

## Security Considerations

License keys are secured through:

1. **Encryption**: Keys are encrypted at rest in the database
2. **Checksum Validation**: Protects against tampering
3. **Time-Limited Tokens**: For validation operations

## License Usage Metrics

The following metrics are tracked for license validation:

1. **API Calls**: Number of calls to provider APIs
2. **Active Agents**: Count of concurrently running agents
3. **Call Minutes**: For voice telephony usage
4. **Storage Usage**: For knowledge bases and document storage

## Future License Tiers

The licensing system is designed to support future tiers:

1. **Free Tier**: Current offering
2. **Pro Tier**: Enhanced features, higher limits (future)
3. **Enterprise Tier**: Custom limits, SLAs, support (future)

## Developer Notes

For contributors and developers:

1. The license validation system is intentionally simple to avoid barriers to adoption
2. License validation is designed to be unobtrusive for legitimate users
3. The focus is on providing value rather than restrictive enforcement
