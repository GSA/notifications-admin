# Feature Flagging

## Using Environment Variables

This guide explains how to update cloud foundry envirionment variables to enable or disable feature flagging.

### Prerequisites

- Cloud Foundry CLI (`cf`) must be installed.
- Access to Cloud Foundry with the necessary credentials.

## Steps to Update

### 1. Log in to Cloud Foundry

```bash
cf login -a api.fr.cloud.gov --sso
```

### 2. Target Correct Space

This should be handled after authenticating but if not, you can target the spaces specifically

```
cf target -o gsa-tts-benefits-studio -s notify-sandbox
```

### 3. Set Environment Variable

```
cf set-env <APP_NAME> <ENV_VAR_NAME> <VALUE>
```

#### Example:

```
cf set-env notify-admin-sandbox FEATURE_BEST_PRACTICES_ENABLED true
```

### 4. Restage the Application

```
cf restage <APP_NAME>
```

#### Example:

```
cf restage notify-admin-sandbox
```

### 5. Update environment specific manifest file(s) and merge into source code

#### Example:

If demo environment had a feature flag flipped, then navigate to the demo.yml file and add appropriate value.
